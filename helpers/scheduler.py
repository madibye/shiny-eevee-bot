import re
import time
from datetime import datetime, timedelta
from typing import Tuple, List, Union
import json

import config
from dateutil import tz
from discord import Forbidden, Guild, ButtonStyle
from discord.ext import tasks
from discord.ext.commands.context import Context
from discord.ui import Button
from helpers import db
from helpers.component_globals import ComponentBase
from parsedatetime import Calendar
from termcolor import cprint


# Reminders
class ReminderButtons(ComponentBase):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_link_button("Message", url)


class SubError(Exception):
    def __init__(self, message: str = "Oops, something went wrong, try again!"):
        self.message = message


# Polls
class ArchiveButton(Button):
    def __init__(self, thread_id):
        super().__init__(label="Archive", style=ButtonStyle.success, custom_id=f"archive {thread_id}")


class ArchiveButtonView(ComponentBase):
    def __init__(self, thread_id):
        super().__init__(timeout=None)
        self.add_item(ArchiveButton(thread_id))


async def add_to_schedule(schedule_type: str, timestamp: int, target: int, channel: int, url: str = "", args=""):
    """
    :param schedule_type: String denoting what we're scheduling for ("reminder", "sub", "unsub", or "poll")
    :param timestamp: Timestamp for when the reminder should go off
               (use the get_timestamp function to help determine that, if you like!!!)
    :param target: User id
    :param channel: Channel id
    :param url: URL to link to the original message that is associated with the scheduled
    :param args: additional arguments that need to be stored in the reminder object can be stored here
    """
    db.add_reminder(
        {
            "type": schedule_type,
            "timestamp": timestamp,
            "target": target,
            "channel": channel,
            "url": url,
            "note": args,
        }
    )

@tasks.loop(seconds=15)
async def schedule_loop(bot):
    current_ts = time.time()
    r_list = db.get_all_reminders()
    for reminder in r_list:
        if reminder["timestamp"] <= current_ts:
            try:
                channel = bot.get_channel(reminder["channel"])
            except AttributeError:
                cprint(f"Tried to send a reminder in a non-existent channel, here's the reminder dict:\n{reminder}", "red")
                return db.delete_reminder(reminder)
            r_type = reminder.get("type")
            if r_type == "reminder" or not r_type:
                await send_reminder(reminder, bot, channel)
            db.delete_reminder(reminder)

async def scheduler_add(ctx: Context, args, unsub=False) -> str:
    schedule_str = ""
    current_time = datetime.now(tz=tz.gettz("America/New_York"))
    total_delta = process_time_strings(current_time, list(args), False)
    new_time = current_time + total_delta
    if new_time != current_time:
        schedule_str = f" You will be {'un' if unsub else 're-'}subscribed at {new_time.strftime('%l:%M %p on %b %d, %Y')}.".replace('  ', ' ')
        await add_to_schedule(
            "unsub" if unsub else "sub",
            int(new_time.timestamp()),
            ctx.author.id,
            ctx.channel.id,
            ctx.message.jump_url,
            ""
        )
    return schedule_str

async def send_reminder(rem, bot, channel):
    if "note" in rem:
        if rem["note"]:
            note = f"I'm reminding you {(rem['note'] + '!') if (rem['note'].split(' ')[0] in ['to', 'about']) else ('about this message: ' + rem['note'])}"
        else:
            note = "I'm reminding you about this message!"
    else:
        msg = await channel.fetch_message(rem["url"].split("/")[6])
        note_array = msg.content.split(" ")[3:]
        note = f"I'm reminding you about this message{(': ' + ' '.join(note_array)) if note_array else '!'}"
    if len(note) >= 1970:
        note = note[0:1970]
    # if the URL is empty, this means it's a slash command; therefore, we should DM the user
    if rem["url"] == "":
        try:
            user = bot.get_user(rem['target'])
            await user.send(f"Hey there, {note}")
        except Forbidden:
            pass  # i.e. if the user's DM channel can't be opened due to having server DMs off or having the bot blocked
    else:
        await channel.send(
            content=f"Hey <@{rem['target']}>! {note}",
            view=ReminderButtons(rem["url"])
        )

async def send_shift_announcement(note, channel, url, redis):
    announcement_msg = await channel.send(note)
    await redis.lpush("posted-sa", json.dumps({
        "msg_id": int(url.split('/')[-1]),
        "url": announcement_msg.jump_url,
    }))

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


def process_note(nstrings: List[str], i: int) -> List[str]:
    # if we find that the previous index slot is a number, and the one before that is a keyword like "in",
    if i > 1 and (nstrings[i - 1].isnumeric() and nstrings[i - 2].lower() in config.remindme_remove_words):
        # we'll remove the last three words from the note
        nstrings[i - 2:i + 1] = '', '', ''
    # if the previous index slot is one or the other between a number or one of our keywords,
    elif i > 0 and (nstrings[i - 1].isnumeric() or nstrings[i - 1].lower() in config.remindme_remove_words):
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


def process_time_strings(now: datetime, tstrings: List[str], return_note: bool = False) -> Union[Tuple[timedelta, str], timedelta]:
    """
    processes a list of strings/arguments, adds up all recognizable times in them, and returns a timedelta object.
    if return_note is true, we'll also return a string with the times parsed out.
    """
    a = Calendar()

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
        dt, parse_status = a.parseDT(datetimeString=time_string, sourceTime=now, tzinfo=tz.gettz("America/New_York"))

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
            elif return_note:
                update_time = False

    # return the best parse we could find,
    # along with a string of everything other than that parse.
    return (best_delta, ' '.join(remove_empty_items(nstrings))) if return_note else best_delta

async def get_timestamp(ctx, args):
    current_time = datetime.now()
    try:
        if int(args[0]) < 1:
            await ctx.send("Please specify a time greater than 0")
            return 0
        else:
            amount = args[0]
            unit = args[1]
    except (ValueError or KeyError):
        await ctx.send("Please specify time as a number.")
        return 0

    # Calculate the time
    if unit in ["second", "sec", "seconds", "s"]:
        current_time += timedelta(seconds=int(amount))
    elif unit in ["min", "mins", "minutes", "minute", "m"]:
        current_time += timedelta(minutes=int(amount))
    elif unit in ["hr", "hrs", "hours", "hour", "h"]:
        current_time += timedelta(hours=int(amount))
    elif unit in ["day", "days", "d"]:
        current_time += timedelta(days=int(amount))
    elif unit in ["week", "weeks", "w"]:
        current_time += timedelta(weeks=int(amount))
    elif unit in ["month", "months", "mo"]:
        current_time += timedelta(days=int(amount) * 30)
    elif unit in ["year", "years", "y"]:
        current_time += timedelta(days=int(amount) * 365)
    else:
        await ctx.send(
            "Please specify a time unit: second/minute/hour/day/week/month/year"
        )
        return 0
    return current_time
