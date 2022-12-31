import re
import time
from datetime import datetime, timedelta
from enum import Enum

from dateutil import tz
from discord import Forbidden, Guild, ButtonStyle, User, ForumChannel, TextChannel, CategoryChannel, Thread, DMChannel
from discord.ext import tasks
from discord.ext.commands.context import Context
from discord.ui import Button
from parsedatetime import Calendar
from termcolor import cprint

import config
from helpers import db
from helpers.component_globals import ComponentBase
from main import MadiBot


class SubError(Exception):
    def __init__(self, message: str = "Oops, something went wrong, try again!"):
        self.message = message


# Used for reminders, schedule announcements, poll DMs
class SingleLinkButtonView(ComponentBase):
    def __init__(self, label, url):
        super().__init__()
        self.add_link_button(label=label, url=url)


# Used for repeating reminders
class CancelRepeatingReminderView(ComponentBase):
    def __init__(self, reminder_id: str = "", label: str = "Cancel Repeating Reminder", disabled: bool = False):
        super().__init__()
        self.add_item(Button(label=label, style=ButtonStyle.red, custom_id=f"CRR {reminder_id}", disabled=disabled))


class ScheduledEventType(Enum):
    REMINDER = 0
    SUB = 1
    UNSUB = 2
    REPEATING_REMINDER = 3


# Put event types that require a valid target ID here.
NEEDS_TARGET = [ScheduledEventType.REMINDER, ScheduledEventType.SUB, ScheduledEventType.UNSUB, ScheduledEventType.REPEATING_REMINDER]


class ScheduledEvent:
    def __init__(
            self, bot: MadiBot, event_type: ScheduledEventType, timestamp: int, channel_id: int,
            target_id: int = 0, url: str = "", raw_data: dict | None = None, extra_args=None
    ):
        """
        This class handles everything related to scheduled events.

        :param bot: We need to take in our bot object here. Usually, this will be self.bot if you're acting within a cog.
        :param event_type: The type of event this is. A callback method will be determined depending on this value.
                           If implementing a new event type, be sure to add its enum in the get_callback method.
        :param timestamp: When our reminder will go off.
        :param channel_id: The channel ID, usually that in which our event will occur.
        :param target_id: (Optional) The user that's setting our event. Not necessary to set in all cases.
        :param url: (Optional) A message URL for our event to take from.
        :param raw_data: (Optional) The dict this event was loaded from if it's being loaded from the db.
                         Don't worry about setting this 99% of the time.
        :param extra_args: (Optional) Any extra information we need to pass our event.
        """
        self.bot: MadiBot = bot
        self.event_type: ScheduledEventType = event_type
        self.timestamp: int = timestamp
        self.guild: Guild = self.bot.get_guild(config.guild_id)
        self.target: User | None = self.bot.get_user(target_id) if target_id else None
        self.channel: ForumChannel | TextChannel | CategoryChannel | Thread | DMChannel = self.bot.get_channel(
            channel_id)
        self.url: str = url
        self.extra_args = extra_args
        self.raw_data: dict = raw_data if raw_data else self.__dict__()
        if "_id" in self.raw_data:
            self.raw_data.pop("_id")  # Just in case, we don't need the object ID
        self.callback = self.get_callback()

    def get_callback(self):
        return {
            ScheduledEventType.REMINDER: self.send_reminder,
            ScheduledEventType.SUB: self.handle_sub,
            ScheduledEventType.UNSUB: self.handle_sub,
            ScheduledEventType.REPEATING_REMINDER: self.send_repeating_reminder,
        }.get(self.event_type)

    def __dict__(self):
        return {"event_type": self.event_type.value, "timestamp": self.timestamp,
                "target_id": getattr(self.target, "id", 0),
                "channel_id": self.channel.id, "url": self.url, "extra_args": self.extra_args}

    def add_to_db(self):
        return db.add_reminder(self.raw_data)

    def remove_from_db(self):
        return db.delete_reminder(self.raw_data)

    async def send_reminder(self):
        if self.extra_args:
            note = f"I'm reminding you {(self.extra_args + '!') if (self.extra_args.split(' ')[0] in ['to', 'about']) else ('about this message: ' + self.extra_args)}"[
                   0:1970]
        else:
            msg = await self.channel.fetch_message(int(self.url.split("/")[6]))
            split_msg_content = msg.content.split(" ")
            if len(split_msg_content) > 3:
                note = f"I'm reminding you about this message: {' '.join(split_msg_content[3:])}"[0:1970]
            else:
                note = "I'm reminding you about this message!"
        # if the URL is empty, this means it's a slash command; therefore, we should DM the user
        if self.url == "":
            try:
                await self.target.send(f"Hey there, {note}")
            except Forbidden:
                pass  # i.e. if the user's DM channel can't be opened due to having server DMs off or having the bot blocked
        else:
            await self.channel.send(content=f"Hey <@{self.target.id}>! {note}",
                                    view=SingleLinkButtonView("Message", self.url))

    async def send_repeating_reminder(self):
        self.extra_args: dict[str, str | int]
        note = self.extra_args.get("note")
        repeat_delta = self.extra_args.get("repeat")
        prev_id = self.extra_args.get("prev_id")
        if prev_id:
            prev_msg = await self.target.dm_channel.fetch_message(prev_id)
            if prev_msg:
                await prev_msg.edit(view=None)
        edited_note = f"I'm reminding you {(note + '!') if (note.split(' ')[0] in ['to', 'about']) else ('about this message: ' + note)}"[
                      0:1970]
        try:
            msg = await self.target.send(f"Hey there, {edited_note}", view=CancelRepeatingReminderView(disabled=True))
            reminder = ScheduledEvent(bot=self.bot, event_type=ScheduledEventType.REPEATING_REMINDER,
                                      target_id=self.target.id,
                                      timestamp=round((datetime.now(tz=tz.gettz("America/New_York")) + timedelta(
                                          seconds=repeat_delta)).timestamp()),
                                      channel_id=self.channel.id,
                                      extra_args={'note': note, 'repeat': repeat_delta, 'prev_id': msg.id})
            reminder_id = reminder.add_to_db()
            await msg.edit(view=CancelRepeatingReminderView(reminder_id))
        except Forbidden:
            pass  # i.e. if the user's DM channel can't be opened due to having server DMs off or having the bot blocked

    async def handle_sub(self):
        try:
            sub_msg = await sub(self.channel, self.bot, self.target.id, self.event_type == ScheduledEventType.UNSUB)
            if "silent" not in str(self.extra_args):
                await self.channel.send(sub_msg)
        except SubError:
            pass


@tasks.loop(seconds=15)
async def schedule_loop(bot: MadiBot):
    current_ts = time.time()
    for reminder in [reminder_from_dict(bot, r) for r in db.get_all_reminders() if r.get("timestamp", 0) <= current_ts]:
        if not reminder.channel or not reminder.callback or not reminder.timestamp or (
                reminder.event_type in NEEDS_TARGET and not reminder.target):
            cprint(f"Oopsie, something went wrong with a reminder, here's the reminder dict:\n{reminder.raw_data}",
                   "red")
            reminder.remove_from_db()
            continue
        await reminder.callback()
        reminder.remove_from_db()


def reminder_from_dict(bot: MadiBot, data: dict) -> ScheduledEvent:
    try:
        event_type = ScheduledEventType(data.get("event_type", data.get("type")))
    except ValueError:
        event_type = {None: ScheduledEventType.REMINDER, "reminder": ScheduledEventType.REMINDER,
                      "sub": ScheduledEventType.SUB, "unsub": ScheduledEventType.UNSUB}.get(data.get("event_type", data.get("type")))
    return ScheduledEvent(bot=bot, event_type=event_type, timestamp=data.get("timestamp", 0),
                          target_id=data.get("target_id", data.get("target", 0)),
                          channel_id=data.get("channel_id", data.get("channel", 0)),
                          url=data.get("url", ""), raw_data=data, extra_args=data.get("extra_args", data.get("note")))


async def scheduler_add(bot: MadiBot, ctx: Context, args, unsub=False) -> str:
    schedule_str = ""
    current_time = datetime.now(tz=tz.gettz("America/New_York"))
    total_delta = process_time_strings(current_time, list(args), False)
    new_time = current_time + total_delta
    if new_time != current_time:
        schedule_str = f" You will be {'un' if unsub else 're-'}subscribed at {new_time.strftime('%l:%M %p on %b %d, %Y')}.".replace(
            '  ', ' ')
        reminder = ScheduledEvent(bot=bot, event_type=ScheduledEventType.UNSUB if unsub else ScheduledEventType.SUB,
                                  timestamp=int(new_time.timestamp()),
                                  target_id=ctx.author.id, channel_id=ctx.channel.id, url=ctx.message.jump_url)
        reminder.add_to_db()
    return schedule_str


def info_from_channel(channel):
    return {
        config.ccgse_channel: (channel.guild.get_role(config.ccgse_notif_role), "the Crazy Card Game Showdown Experience"),
        config.minecraft_channel: (channel.guild.get_role(config.minecraft_notif_role), "Minecraft"),
        config.club_channel: (channel.guild.get_role(config.club_notif_role), "the Koala City club"),
    }.get(channel.id, (None, None))


async def sub(channel: TextChannel | Thread, bot: MadiBot, target_id: int, unsub: bool = False, ping: bool = True) -> str:
    guild = bot.get_guild(config.guild_id)
    target = await guild.fetch_member(target_id)
    notif_role, msg_end = info_from_channel(channel)
    if not notif_role:
        raise SubError(
            message=f"Oh no, looks like something went wrong... Please contact Madi, I'm sure she'll fix it.")
    if unsub and notif_role in target.roles:
        clean_sub_tasks(ScheduledEventType.UNSUB, target_id, channel.id)
        await target.remove_roles(notif_role)
        return f"{f'<@{target.id}> ' if ping else ''}You have been unsubscribed from notifications for {msg_end}."
    elif not unsub and notif_role not in target.roles:
        clean_sub_tasks(ScheduledEventType.SUB, target_id, channel.id)
        await target.add_roles(notif_role)
        return f"{f'<@{target.id}> ' if ping else ''}You have been subscribed to notifications for {msg_end}."
    else:
        raise SubError(
            message=f"{f'<@{target.id}> ' if ping else ''}You {'are not currently' if unsub else 'are already'} "
                    f"subscribed to notifications for {msg_end}!")


def clean_sub_tasks(event_type: ScheduledEventType, target_id: int, channel_id: int):
    def check_reminder_dict(data: dict):
        # This is probably way less scary than it looks.
        return (data.get("target_id", data.get("target", 0)) == target_id
                and data.get("channel_id", data.get("channel", 0)) == channel_id
                and data.get("timestamp") > time.time() and (
                    data.get("event_type", data.get("type")) in [ScheduledEventType.SUB, "sub"]
                    if event_type == ScheduledEventType.SUB else [ScheduledEventType.UNSUB, "unsub"]))

    for raw_reminder in [r for r in db.get_all_reminders() if check_reminder_dict(r)]:
        db.delete_reminder(raw_reminder)


def remove_empty_items(items: list):
    for _ in range(items.count("")):
        items.remove("")
    return items


async def replace_tags_with_mentions(note: str, guild: Guild) -> str:
    for role in guild.roles:
        note = note.replace(f"@{role.name}", role.mention)
    async for member in guild.fetch_members(limit=100):
        note = note.replace(
            f"@{member.name}#{member.discriminator}", member.mention
        ).replace(
            f"@{member.name}", member.mention
        ).replace(
            f"@{member.nick}", member.mention
        )
    return note


def make_time_delta(dt: datetime, now: datetime) -> timedelta:
    """takes a datetime object and represents it in a time delta"""
    return dt - now


def process_note(nstrings: list[str], i: int) -> list[str]:
    words_to_remove = ["in", "and", "on", "at", "@"]
    # if we find that the previous index slot is a number, and the one before that is a keyword like "in",
    if i > 1 and (nstrings[i - 1].isnumeric() and nstrings[i - 2].lower() in words_to_remove):
        # we'll remove the last three words from the note
        nstrings[i - 2:i + 1] = '', '', ''
    # if the previous index slot is one or the other between a number or one of our keywords,
    elif i > 0 and (nstrings[i - 1].isnumeric() or nstrings[i - 1].lower() in words_to_remove):
        # we'll just remove the last two words
        nstrings[i - 1:i + 1] = '', ''
    # otherwise, we already know the current index slot we're on needs to be removed
    else:
        # so we can just remove that one
        nstrings[i] = ''
    # this is here in case the word after our current slot is something that won't change the time delta, like AM, PM, or a year
    if i < len(nstrings) - 2 and (nstrings[i + 1].lower() in ["am", "pm"] or nstrings[i + 1].isnumeric()):
        nstrings[i + 1] = ''
    return nstrings


def process_time_strings(now: datetime, tstrings: list[str], return_note: bool = False) -> tuple[
                                                                                               timedelta, str] | timedelta:
    """
    processes a list of strings/arguments, adds up all recognizable times in them, and returns a timedelta object.
    if return_note is true, we'll also return a string with the times parsed out.
    """
    a = Calendar()
    nstrings = ""

    # words_to_remove and nstrings are only referenced behind if return_note statements, so we don't need to worry about referencing them before assignment
    if return_note:
        # We wanna remove quote markdown from what will become the note itself
        nstrings = " ".join(tstrings).replace("```", " \n").replace("`", "").split(" ")
        # Regex stuff to make it so the time parsing does not read anything between block quotes or `` markers
        tstrings = re.sub(r"`((?:\S+\s*)*)`", "", re.sub(r"```((?:\S+\s*)*)```", "", " ".join(tstrings))).split(" ")
        for i, ts in enumerate(tstrings):
            # We want to remove certain words we ignore for time parsing
            if ts in config.remindme_ignore_words:
                tstrings[i] = ""
            # Here we're inserting blank words we removed via regex back into the list.
            # This is to make sure we're later removing the correct objects from nstrings, it relies on iterating through tstrings, so we want both lists to be the same length
            if tstrings[i] != nstrings[i] and tstrings[i] in nstrings:
                tstrings.insert(i, "")

    # first, create an expansion of tstrings
    # converts ['1', '2', '3'] -> ['1', '1 2', '1 2 3']
    exp_tstrs = tstrings[:]
    for i in range(len(exp_tstrs))[:0:-1]:
        exp_tstrs[i] = ' '.join(exp_tstrs[:i]) + f' {exp_tstrs[i]}'

    # run over all of the potential strings to calculate a total delta
    best_delta = timedelta()
    update_time = True
    for i in range(len(exp_tstrs)):
        # build our string we're attempting to parse
        time_string = exp_tstrs[i]
        dt, parse_status = a.parseDT(datetimeString=time_string, sourceTime=now,
                                     tzinfo=tz.gettz("America/New_York"))

        # if what we have is parsable..
        if parse_status:
            # create a time delta based on our parse.
            new_delta = make_time_delta(dt, now)

            # if it is different than what we originally parsed,
            if new_delta != best_delta:
                if update_time:
                    if now < now + new_delta:
                        # we'll use that one instead.
                        best_delta = new_delta
                    # this ensures that if we say something like "remindme at 12am",
                    elif now < now + new_delta + timedelta(days=1):
                        # it will set the reminder for tomorrow morning at 12am rather than error because 12am already happened today
                        best_delta = new_delta + timedelta(days=1)
                if return_note:
                    # and we can start removing now-irrelevant parts of the original string itself
                    nstrings = process_note(nstrings, i)
            else:
                update_time = False

    # return the best parse we could find,
    # along with a string of everything other than that parse.
    return (best_delta, ' '.join(remove_empty_items(nstrings))) if return_note else best_delta
