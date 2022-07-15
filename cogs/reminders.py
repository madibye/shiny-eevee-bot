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
            return await ctx.send("Sorry, you can't use my DMs to set reminders! "
                                  "Feel free to use the slash command `/remindme` instead if you'd like your reminder to be private!")
        if time_and_note:
            time_and_note_list = scheduler.remove_empty_items(time_and_note.replace("\n", " \n").split(" "))
            current_time = datetime.now(tz=tz.gettz("America/New_York"))
            total_delta, note = scheduler.process_time_strings(current_time, time_and_note_list, True)
            new_time = current_time + total_delta
            if current_time < new_time:
                await ctx.send(f"Okie, I'll remind you at {new_time.strftime('%l:%M %p on %b %d, %Y')}!".replace('  ', ' '))
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
                await ctx.send("I can't remind you about something that already happened!")
            elif current_time == new_time:
                await ctx.send("Sorry, I couldn't find when you wanted me to set this reminder for!")
        else:
            await ctx.send("Sorry, I couldn't find when you wanted me to set this reminder for!")

    @commands.command(name="remindmecancel", aliases=["remindercancel", "rmc"])
    async def remindme_cancel(self, ctx):
        if ctx.message.reference:
            reminder = db.get_reminder_from_url(ctx.message.reference.jump_url)
            if reminder is not None:
                if reminder['target'] == ctx.author.id:
                    await ctx.message.reference.resolved.add_reaction("❌")
                    db.delete_reminder(reminder)
                    await ctx.send("Okie, I won't remind you about that, then!")
                else:
                    await ctx.send("Hey, don't delete other people's reminders! That's mean!")
            else:
                await ctx.send("I couldn't find any reminders here! Either you didn't reply to a message containing a "
                               "reminder, or the reminder already went off!")
        else:
            await ctx.send("To cancel a reminder, you need to reply to a message containing a reminder!")

    @app_commands.command(name="remindme", description="Need a reminder set? I'll be happy to help!")
    @app_commands.describe(time="The time for your reminder", note="The note for your reminder")
    async def remindme_slash(self, interaction: Interaction, time: str, note: str):
        current_time = datetime.now(tz=tz.gettz("America/New_York"))
        total_delta = scheduler.process_time_strings(current_time, time.split(" "), False)
        new_time = current_time + total_delta
        if current_time < new_time:
            await interaction.response.send_message(f"Okie, I'll remind you at {new_time.strftime('%l:%M %p on %b %d, %Y')}!".replace('  ', ' '), ephemeral=True)
            await scheduler.add_to_schedule(
                "reminder",
                int(new_time.timestamp()),
                interaction.user.id,
                interaction.channel.id,
                "",
                note
            )
        elif current_time > new_time:
            await interaction.response.send_message("I can't remind you about something that already happened!", ephemeral=True)
        elif current_time == new_time:
            await interaction.response.send_message("Sorry, I couldn't find when you wanted me to set this reminder for!", ephemeral=True)


async def setup(client):
    await client.add_cog(Reminders(client), guild=Object(id=config.guild_id))
