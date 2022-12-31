from datetime import datetime, timedelta

from dateutil import tz
from discord import Guild, DMChannel, Interaction, Object, app_commands
from discord.ext import commands

import config
from helpers import db, scheduler, embedding
from helpers.scheduler import ScheduledEvent, ScheduledEventType as SET
from main import MadiBot


class Reminders(commands.Cog, name="Reminders"):
    def __init__(self, bot):
        self.bot: MadiBot = bot
        self.guild: Guild | None = None

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
                reminder = ScheduledEvent(bot=self.bot, event_type=SET.REMINDER, timestamp=int(new_time.timestamp()),
                                          target_id=ctx.author.id, channel_id=ctx.channel.id, url=ctx.message.jump_url, extra_args=note)
                reminder.add_to_db()
            elif current_time > new_time:
                await ctx.send("I can't remind you about something that already happened!")
            elif current_time == new_time:
                await ctx.send("Sorry, I couldn't find when you wanted me to set this reminder for!")
        else:
            await ctx.send("Sorry, I couldn't find when you wanted me to set this reminder for!")

    @commands.command(name="remindmecancel", aliases=["remindercancel", "rmc"])
    async def remindme_cancel(self, ctx):
        if ctx.message.reference:
            reminder = scheduler.reminder_from_dict(self.bot, db.get_reminder_from_url(ctx.message.reference.jump_url))
            if reminder is not None:
                if reminder.target.id == ctx.author.id:
                    reminder.remove_from_db()
                    await ctx.message.reference.resolved.add_reaction("❌")
                    await ctx.send("Okie, I won't remind you about that, then!")
                else:
                    await ctx.send("Hey, don't delete other people's reminders! That's mean!")
            else:
                await ctx.send("I couldn't find any reminders here! Either you didn't reply to a message containing a "
                               "reminder, or the reminder already went off!")
        else:
            await ctx.send("To cancel a reminder, you need to reply to a message containing a reminder!")

    @app_commands.command(name="remindme", description="Need a reminder set? I'll be happy to help!")
    @app_commands.describe(time="The time for your reminder", note="The note for your reminder",
                           repeat="If you want to schedule a repeating reminder, set how often you want it to repeat")
    async def remindme_slash(self, interaction: Interaction, time: str, note: str, repeat: str | None = None):
        current_time = datetime.now(tz=tz.gettz("America/New_York"))
        total_delta = scheduler.process_time_strings(current_time, time.split(" "), False)
        new_time = current_time + total_delta
        repeat_delta: timedelta = timedelta()
        if repeat:
            repeat_delta = scheduler.process_time_strings(current_time, repeat.split(" "), False)
        if current_time < new_time:
            await interaction.response.send_message(
                f"Okie, I'll remind you at {new_time.strftime('%l:%M %p on %b %d, %Y')}! "
                f"{f'Afterward, you will be reminded every {embedding.get_time_remaining_str(repeat_delta)}.' if repeat else ''}"
                .replace('  ', ' '), ephemeral=True)
            reminder = ScheduledEvent(bot=self.bot, event_type=SET.REPEATING_REMINDER if repeat else SET.REMINDER,
                                      timestamp=int(new_time.timestamp()), target_id=interaction.user.id, channel_id=interaction.channel.id,
                                      extra_args={'note': note, 'repeat': round(repeat_delta.total_seconds())} if repeat else note)
            return reminder.add_to_db()
        await interaction.response.send_message(
            "Sorry, I couldn't find when you wanted me to set this reminder for!" if current_time == new_time else
            "I can't remind you about something that already happened!", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        # Handles cancel repeating reminder buttons
        if "custom_id" not in interaction.data:
            return
        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith("CRR"):
            return
        reminder_id = interaction.data["custom_id"].split()[1]
        reminder = db.get_reminder(reminder_id)
        if not reminder:
            return await interaction.response.send_message(
                "I couldn't find any reminders here! Either this is an old reminder that already got cancelled, "
                "or something else went wrong!", ephemeral=True)
        db.delete_reminder(reminder)
        await interaction.message.edit(view=scheduler.CancelRepeatingReminderView(label="Cancelled", disabled=True))
        return await interaction.response.send_message("Okie, I won't remind you about that, then!", ephemeral=True)


async def setup(client):
    await client.add_cog(Reminders(client), guild=Object(id=config.guild_id))
