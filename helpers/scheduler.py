from discord.ext import tasks
from helpers import db, command_helpers
import time
import re
from typing import Tuple, List
from parsedatetime import Calendar
from dateutil import tz
from datetime import datetime, timedelta
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle

'''a lot of this is copied directly from the mod server's scheduler, it may not make a ton of sense to have all these
functions be factored out in this way just for one command, but it will make our lives a whole lot easier if we ever
decide to add more commands that require scheduling functionality to the staff discord'''

async def add_to_schedule(schedule_type: str, timestamp: int, target: int, channel: int, url: str, args):
    """
    :param schedule_type: String denoting what we're scheduling for ("reminder", "sub", "unsub", or "poll")
    :param timestamp: Timestamp for when the reminder should go off
               (use the get_timestamp function to help determine that, if you like!!!)
    :param target: User id
    :param channel: Channel id
    :param url: URL to link to the original message that is associated with the scheduled
    :param args: additional arguments that need to be stored in the reminder object can be stored here
    """
    await db.add_reminder(
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
    r_list = await db.get_all_reminders()
    for reminder in r_list:
        channel = bot.get_channel(reminder["channel"])
        if reminder["timestamp"] <= current_ts:
            if "type" in reminder:
                if reminder["type"] == "reminder":
                    await send_reminder(reminder, bot, channel)
                    await db.delete_reminder(reminder)
            else:
                await send_reminder(reminder, bot, channel)
                await db.delete_reminder(reminder)


async def send_reminder(rem, bot, channel):
    if "note" in rem:
        if rem["note"]:
            note = f"i managed to remember {(rem['note'] + '!') if (rem['note'].split(' ')[0] in ['to', 'about']) else ('about this message: ' + rem['note'])}"
        else:
            note = "i managed to remember!!"
    else:
        msg = await channel.fetch_message(rem["url"].split("/")[6])
        note_array = msg.content.split(" ")[3:]
        note = f"i managed to remember about this message{(': ' + ' '.join(note_array)) if note_array else '!'}"
    if len(note) >= 1970:
        note = note[0:1970]
    # if the URL is empty, this means it's a slash command; therefore, we should DM the user
    if rem["url"] == "":
        user = bot.get_user(rem['target'])
        await user.send(f"hi hi, {note}")
    else:
        await channel.send(
            content=f"hi hi <@{rem['target']}>, {note}",
            components=[create_actionrow(create_button(style=ButtonStyle.URL, label="Message", url=rem["url"]))]
        )


def make_time_delta(dt: datetime, now: datetime) -> timedelta:
    """takes a datetime object and represents it in a time delta"""
    return dt - now


def process_time_strings(now: datetime, nstrings: List[str]) -> Tuple[timedelta, str]:
    """processes a list of strings/arguments, adds up all recognizable times in them"""
    a = Calendar()
    words_to_remove = ["in", "and", "on", "at", "@"]

    # Regex stuff to make it so the parser does not read anything between block quotes or `` markers
    tstrings = command_helpers.remove_empty_items(re.sub(r"`((?:\S+\s*)*)`", "", re.sub(r"```((?:\S+\s*)*)```", "", " ".join(nstrings))).split(" "))

    # And we also wanna remove quote markdown from the note itself
    nstrings = " ".join(nstrings).replace("```", " \n").replace("`", "").split(" ")

    # first, create an expansion of tstrings
    # converts ['1', '2', '3'] -> ['1', '1 2', '1 2 3']
    exp_tstrs = tstrings[:]
    for i in range(len(exp_tstrs))[:0:-1]:
        exp_tstrs[i] = ' '.join(exp_tstrs[:i]) + f' {exp_tstrs[i]}'

    # run over all of the potential strings to calculate a total delta
    best_delta = timedelta()
    for i in range(len(exp_tstrs)):
        # build our string we're attempting to parse
        time_string = exp_tstrs[i]
        dt, parse_status = a.parseDT(datetimeString=time_string, sourceTime=now, tzinfo=tz.gettz("America/New_York"))

        # if what we have is parsable..
        if parse_status:
            # create a time delta based on our parse.
            new_delta = make_time_delta(dt, now)

            # if it is different than what we originally parsed,
            if new_delta != best_delta and now < now + new_delta:
                # we'll use that one instead.
                best_delta = new_delta
                # and we can start removing now-irrelevant parts of the original string itself
                # if we find that the previous index slot is a number, and the one before that is a keyword like "in",
                if i > 1 and (nstrings[i - 1].isnumeric() and nstrings[i - 2].lower() in words_to_remove):
                    # we'll remove the last three words from the note
                    tstrings[i - 2:i + 1] = '', '', ''
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

    # return the best parse we could find,
    # along with a string of everything other than that parse.
    return best_delta, ' '.join(command_helpers.remove_empty_items(nstrings))
