from datetime import datetime, timedelta

from dateutil import tz
from discord import Guild, DMChannel, Interaction, Object, app_commands
from discord.errors import Forbidden, HTTPException, NotFound
from discord.ext import commands

import config
from handlers import database, scheduler, embedding
from handlers.scheduler import ScheduledEvent, ScheduledEventType as SET
from main import Amelia


class Reminders(commands.Cog, name="Reminders"):
    def __init__(self, bot):
        self.bot: Amelia = bot
        self.guild: Guild | None = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(config.guild_id)
        try:
            scheduler.schedule_loop.start(self.bot)
        except RuntimeError:
            print("Failed to start schedule loop as it is already running.")

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
                msg = await ctx.send(f"Okie, I'll remind you on <t:{new_time.timestamp()}:f>! "
                                     f"Feel free to press the button below if you'd like to cancel your reminder!".replace('  ', ' '),
                                     view=scheduler.CancelReminderView(label="Don't Remind", disabled=True))
                # Now time to make the DB entry
                reminder_id = ScheduledEvent(
                    bot=self.bot, event_type=SET.REMINDER, timestamp=int(new_time.timestamp()), target_id=ctx.author.id,
                    channel_id=ctx.channel.id, url=ctx.message.jump_url, extra_args={"note": note, "prev_id": msg.id}).add_to_db()
                await msg.edit(view=scheduler.CancelReminderView(label=f"Don't Remind", reminder_id=reminder_id))
            elif current_time > new_time:
                await ctx.send("I can't remind you about something that already happened!")
            elif current_time == new_time:
                await ctx.send("Sorry, I couldn't find when you wanted me to set this reminder for!")
        else:
            await ctx.send("Sorry, I couldn't find when you wanted me to set this reminder for!")

    @commands.command(name="remindmecancel", aliases=["remindercancel", "rmc"])
    async def remindme_cancel(self, ctx):
        if ctx.message.reference:
            reminder = scheduler.reminder_from_dict(self.bot, database.get_reminder_from_url(ctx.message.reference.jump_url))
            if reminder is not None:
                if reminder.target.id == ctx.author.id:
                    if isinstance(reminder.extra_args, dict):
                        try:
                            prev_msg = await reminder.channel.fetch_message(reminder.extra_args.get("prev_id"))
                            await prev_msg.edit(view=scheduler.CancelReminderView(label="Cancelled", disabled=True))
                            await prev_msg.delete(delay=10)
                        except (Forbidden, HTTPException, NotFound):
                            pass
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
    @app_commands.describe(time=f"The time you'd like me to remind you (e.g. \"2h\", \"10pm\", \"5/24 6:30pm\")",
                           note="A note for your reminder (e.g. \"Brush Teeth\", \"Do Homework\", etc.)",
                           repeat="If you want to schedule a repeating reminder, set how often you want it to repeat")
    async def remindme_slash(self, interaction: Interaction, time: str, note: str, repeat: str | None = None):
        current_time = datetime.now(tz=tz.gettz("America/New_York"))
        total_delta = scheduler.process_time_strings(current_time, time.split(" "), False)
        new_time = current_time + total_delta
        repeat_delta: timedelta = timedelta()
        if repeat:
            repeat_delta = scheduler.process_time_strings(current_time, repeat.split(" "), False)
            if repeat_delta.total_seconds() < 59:
                return await interaction.response.send_message(
                    "Sorry, I can't set a reminder with a repeat duration of under 60 seconds!" if repeat_delta.total_seconds() else
                    "Sorry, it looks like your repeat duration is invalid!", ephemeral=True)
        if current_time < new_time:
            try:
                msg = await interaction.user.send(
                    content=f"Hi there! At {new_time.strftime('%l:%M %p on %b %d, %Y')}, you'll be reminded about: `{note}`! "
                    f"{f'Afterward, you will be reminded every {embedding.get_time_remaining_str(repeat_delta)}. ' if repeat else ''}"
                    f"Feel free to press the button below if you'd like to cancel your reminder!".replace('  ', ' '),
                    view=scheduler.CancelReminderView(label="Stop Reminding" if repeat else "Don't Remind", disabled=True))
            except Forbidden:  # i.e. if the user's DM channel can't be opened due to having server DMs off or having the bot blocked
                return await interaction.response.send_message(
                    "Looks like I couldn't DM you. Make sure you don't have me blocked, "
                    "and you have DMs enabled from users in this server!", ephemeral=True)
            await interaction.response.send_message("Okie, I'll remind you then! Check your DMs for more info!", ephemeral=True)
            reminder_id = ScheduledEvent(
                bot=self.bot, event_type=SET.REPEATING_REMINDER if repeat else SET.REMINDER, timestamp=int(new_time.timestamp()),
                target_id=interaction.user.id, channel_id=msg.channel.id, extra_args={
                    'note': note, 'repeat': round(repeat_delta.total_seconds()), 'prev_id': msg.id
                } if repeat else {'note': note, 'prev_id': msg.id}
            ).add_to_db()
            return await msg.edit(view=scheduler.CancelReminderView(
                label="Stop Reminding" if repeat else "Don't Remind", reminder_id=reminder_id))
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
        reminder = database.get_reminder(reminder_id)
        if not reminder:
            return await interaction.response.send_message(
                "I couldn't find any reminders here! Either this is an old reminder that already got cancelled, "
                "or something else went wrong!", ephemeral=True)
        if interaction.user.id != reminder.get("target_id"):
            return await interaction.response.send_message("Hey, don't delete other people's reminders! That's mean!", ephemeral=True)
        database.delete_reminder(reminder)
        await interaction.message.edit(view=scheduler.CancelReminderView(label="Cancelled", disabled=True))
        await interaction.response.send_message("Okie, I won't remind you about that, then!", ephemeral=True)
        await interaction.message.delete(delay=10)


async def setup(client):
    await client.add_cog(Reminders(client), guild=Object(id=config.guild_id))
