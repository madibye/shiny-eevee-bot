from discord import Interaction, app_commands, TextChannel, Thread, Object
from discord.ext import commands

import config
from handlers import scheduler
from main import ShinyEevee


class Notifications(commands.Cog, name="notifications"):
    def __init__(self, bot):
        self.bot: ShinyEevee = bot
        self.ccgse_channel: TextChannel | None = None
        self.club_channel: Thread | None = None
        self.minecraft_channel: TextChannel | None = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.ccgse_channel: TextChannel | None = self.bot.get_channel(config.ccgse_channel)
        self.club_channel: Thread | None = self.bot.get_channel(config.club_channel)
        self.minecraft_channel: TextChannel | None = self.bot.get_channel(config.minecraft_channel)
        [self.bot.tree.add_command(command, guild=Object(config.koala_city_id)) for command in self.get_app_commands()]

    # yes he is naked. please don't make fun of him :(
    sub_command_group = app_commands.Group(name="sub", description="Receive notifications for various things in the server!")

    @sub_command_group.command(name="ccgse", description="Receive notifications about the up-and-coming card game!")
    async def ccgse_sub(self, interaction: Interaction):
        try:
            sub_msg = await scheduler.sub(self.ccgse_channel, self.bot, interaction.user.id, ping=False)
        except scheduler.SubError as e:
            return await interaction.response.send_message(e.message, ephemeral=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @sub_command_group.command(name="minecraft", description="Receive notifications about our Minecraft server!")
    async def minecraft_sub(self, interaction: Interaction):
        try:
            sub_msg = await scheduler.sub(self.minecraft_channel, self.bot, interaction.user.id, ping=False)
        except scheduler.SubError as e:
            return await interaction.response.send_message(e.message, ephemeral=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @sub_command_group.command(name="club", description="Receive notifications about our upcoming Corporate Clash club!")
    async def club_sub(self, interaction: Interaction):
        try:
            sub_msg = await scheduler.sub(self.club_channel, self.bot, interaction.user.id, ping=False)
        except scheduler.SubError as e:
            return await interaction.response.send_message(e.message, ephemeral=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    unsub_command_group = app_commands.Group(name="unsub", description="Stop receiving notifications for various things in the server!")

    @unsub_command_group.command(name="ccgse", description="Stop receiving notifications about the up-and-coming card game!")
    async def ccgse_unsub(self, interaction: Interaction):
        try:
            sub_msg = await scheduler.sub(self.ccgse_channel, self.bot, interaction.user.id, unsub=True, ping=False)
        except scheduler.SubError as e:
            return await interaction.response.send_message(e.message, ephemeral=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @unsub_command_group.command(name="minecraft", description="Stop receiving notifications about our Minecraft server!")
    async def minecraft_unsub(self, interaction: Interaction):
        try:
            sub_msg = await scheduler.sub(self.minecraft_channel, self.bot, interaction.user.id, unsub=True, ping=False)
        except scheduler.SubError as e:
            return await interaction.response.send_message(e.message, ephemeral=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @unsub_command_group.command(name="club", description="Stop receiving notifications about our upcoming Corporate Clash club!")
    async def club_unsub(self, interaction: Interaction):
        try:
            sub_msg = await scheduler.sub(self.club_channel, self.bot, interaction.user.id, unsub=True, ping=False)
        except scheduler.SubError as e:
            return await interaction.response.send_message(e.message, ephemeral=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)


async def setup(client):
    await client.add_cog(Notifications(client), guilds=client.guilds)
