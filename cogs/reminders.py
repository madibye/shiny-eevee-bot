from discord.ext import commands
from helpers import db, scheduler, command_helpers
from dateutil import tz
from datetime import datetime
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option
import config

class Reminders(commands.Cog, name="Reminders"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            scheduler.schedule_loop.start(self.bot)
        except RuntimeError:
            print("Failed to start suggestion loop as it is already running.")

    @commands.command(name="remindme", aliases=["remind", "rm"])
    async def remindme(self, ctx: commands.Context):
        args_list = command_helpers.parse_args(ctx)
        if args_list:
            current_time = datetime.now(tz=tz.gettz("America/New_York"))
            total_delta, note = scheduler.process_time_strings(current_time, args_list)
            new_time = current_time + total_delta
            if current_time < new_time:
                await ctx.send(f"awa, i'll try to remember... {new_time.strftime('%l:%M %p on %b %d, %Y').lower()}, right?".replace('  ', ' '))
                # Now time to make the DB entry
                await scheduler.add_to_schedule(
                    "reminder",
                    int(new_time.timestamp()),
                    ctx.author.id,
                    ctx.channel.id,
                    ctx.message.jump_url,
                    note
                )
            elif current_time > new_time:
                await ctx.send("awa, that already happened, silly goose :)")
            elif current_time == new_time:
                await ctx.send("awa...? i can't find a time here :(")
        else:
            await ctx.send("awa...? i can't find a time here :(")

    @commands.command(name="remindmecancel", aliases=["remindercancel", "rmc"])
    async def remindme_cancel(self, ctx: commands.Context):
        if ctx.message.reference:
            reminder = await db.get_reminder_from_url(ctx.message.reference.jump_url)
            if reminder is not None:
                if reminder['target'] == ctx.author.id:
                    await ctx.message.reference.resolved.add_reaction("❌")
                    await db.delete_reminder(reminder)
                    await ctx.send("hehe, okie dokie, guess you changed your mind, awa")
                else:
                    await ctx.send("hey... you're not supposed to delete other people's reminders, that's not nice...")
            else:
                await ctx.send("you have to reply to a message containing a reminder, awa :)")
        else:
            await ctx.send("you have to reply to a message containing a reminder, awa :)")

    @cog_ext.cog_slash(name="remindme",
                       description="awa, i can help you set reminders if you want :)",
                       options=[create_option(name="content", description="the time and note for your reminder, awa", option_type=3, required=True)]
                       )
    async def remindme_slash(self, ctx: SlashContext, content: str):
        args_list = command_helpers.remove_empty_items(
            content.replace("\n", " \n").split(" ")
        )
        if args_list:
            current_time = datetime.now(tz=tz.gettz("America/New_York"))
            total_delta, note = scheduler.process_time_strings(current_time, args_list)
            new_time = current_time + total_delta
            if current_time < new_time:
                await ctx.send(f"awa, i'll try to remember... {new_time.strftime('%l:%M %p on %b %d, %Y').lower()}, right?".replace('  ', ' '), hidden=True)
                await scheduler.add_to_schedule(
                    "reminder",
                    int(new_time.timestamp()),
                    ctx.author.id,
                    ctx.channel.id,
                    "",
                    note
                )
            elif current_time > new_time:
                await ctx.send("awa, that already happened, silly goose :)", hidden=True)
            elif current_time == new_time:
                await ctx.send("awa...? i can't find a time here :(", hidden=True)
        else:
            await ctx.send("awa...? i can't find a time here :(", hidden=True)


def setup(client):
    client.add_cog(Reminders(client))
