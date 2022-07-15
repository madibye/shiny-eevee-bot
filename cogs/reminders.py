from datetime import datetime

import config
from dateutil import tz
from discord import Guild, DMChannel, Interaction, Object, app_commands
from discord.ext import commands
from helpers import db, scheduler


class Reminders(commands.Cog, name="Reminders"):
    def __init__(self, bot):
        self.bot = bot
        self.guild: Guild = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(config.guild_id)
        try:
            scheduler.schedule_loop.start(self.bot)
        except RuntimeError:
            print("Failed to start suggestion loop as it is already running.")

    @commands.command(name="remindme", aliases=["remind", "rm"])
    async def remindme(self, ctx, *, time_and_note):
        if isinstance(ctx.channel, DMChannel):
            return await ctx.send("sorry, the reminder command won't work in DMs :( "
                                  "you can use the slash command `/remindme` instead if you want your reminder to be private!")
        if time_and_note:
            time_and_note_list = scheduler.remove_empty_items(time_and_note.replace("\n", " \n").split(" "))
            current_time = datetime.now(tz=tz.gettz("America/New_York"))
            total_delta, note = scheduler.process_time_strings(current_time, time_and_note_list, True)
            new_time = current_time + total_delta
            if current_time < new_time:
                await ctx.send(f"okay, i'll remind you at {new_time.strftime('%l:%M %p on %b %d, %Y')}!".replace('  ', ' '))
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
                await ctx.send("that already happened, silly goose!")
            elif current_time == new_time:
                await ctx.send("sorry, i can't find a time here :(")
        else:
            await ctx.send("sorry, i can't find a time here :(")

    @commands.command(name="remindmecancel", aliases=["remindercancel", "rmc"])
    async def remindme_cancel(self, ctx):
        if ctx.message.reference:
            reminder = db.get_reminder_from_url(ctx.message.reference.jump_url)
            if reminder is not None:
                if reminder['target'] == ctx.author.id:
                    await ctx.message.reference.resolved.add_reaction("❌")
                    db.delete_reminder(reminder)
                    await ctx.send("that's okay, i won't remind you about that then!")
                else:
                    await ctx.send("hey, don't delete other people's reminders! that's mean :(")
            else:
                await ctx.send("you have to reply to a message containing a reminder, silly goose")
        else:
            await ctx.send("you have to reply to a message containing a reminder, silly goose")

    @app_commands.command(name="remindme", description="happy to help with all your reminder needs :)")
    @app_commands.describe(time="the time for your reminder", note="the note for your reminder")
    async def remindme_slash(self, interaction: Interaction, time: str, note: str):
        current_time = datetime.now(tz=tz.gettz("America/New_York"))
        total_delta = scheduler.process_time_strings(current_time, time.split(" "), False)
        new_time = current_time + total_delta
        if current_time < new_time:
            await interaction.response.send_message(f"okay, i'll remind you at {new_time.strftime('%l:%M %p on %b %d, %Y')}!".replace('  ', ' '), ephemeral=True)
            await scheduler.add_to_schedule(
                "reminder",
                int(new_time.timestamp()),
                interaction.user.id,
                interaction.channel.id,
                "",
                note
            )
        elif current_time > new_time:
            await interaction.response.send_message("that already happened, silly goose!", ephemeral=True)
        elif current_time == new_time:
            await interaction.response.send_message("sorry, i can't find a time here :(", ephemeral=True)


async def setup(client):
    await client.add_cog(Reminders(client), guild=Object(id=config.guild_id))
