from discord import Guild, Role, Embed, Colour, Interaction, Object, app_commands
from discord.ext import commands
from discord.app_commands import Choice
from helpers import scheduler, db
from typing import Optional
import config


class Notifications(commands.Cog, name="notifications"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.guild: Guild = None
        self.ccgse_notif_role = None
        self.club_notif_role = None
        self.minecraft_notif_role = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild: Guild = self.bot.get_guild(config.guild_id)
        self.ccgse_notif_role: Role = self.guild.get_role(config.ccgse_notif_role)
        self.club_notif_role: Role = self.guild.get_role(config.club_notif_role)
        self.minecraft_notif_role: Role = self.guild.get_role(config.minecraft_notif_role)

    # yes he is naked. please don't make fun of him :(
    sub_command_group = app_commands.Group(name="sub", description="Receive notifications for various things in the server!")

    @sub_command_group.command(name="ccgse", description="Receive notifications about the up-and-coming card game!")
    async def ccgse_sub(self, interaction: Interaction):
        member = await self.guild.fetch_member(interaction.user.id)
        sub_msg = await scheduler.sub(member, self.ccgse_notif_role, "Crazy Card Game Showdown Experience")
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @sub_command_group.command(name="minecraft", description="Receive notifications about our Minecraft server!")
    async def minecraft_sub(self, interaction: Interaction):
        member = await self.guild.fetch_member(interaction.user.id)
        sub_msg = await scheduler.sub(member, self.minecraft_notif_role, "the Minecraft server")
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @sub_command_group.command(name="club", description="Receive notifications about our upcoming Corporate Clash club!")
    async def club_sub(self, interaction: Interaction):
        member = await self.guild.fetch_member(interaction.user.id)
        sub_msg = await scheduler.sub(member, self.club_notif_role, "the upcoming Corporate Clash club")
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    unsub_command_group = app_commands.Group(name="unsub", description="Stop receiving notifications for various things in the server!")

    @unsub_command_group.command(name="ccgse", description="Stop receiving notifications about the up-and-coming card game!")
    async def ccgse_unsub(self, interaction: Interaction):
        member = await self.guild.fetch_member(interaction.user.id)
        sub_msg = await scheduler.sub(member, self.ccgse_notif_role, "Crazy Card Game Showdown Experience", unsub=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @unsub_command_group.command(name="minecraft", description="Stop receiving notifications about our Minecraft server!")
    async def minecraft_unsub(self, interaction: Interaction):
        member = await self.guild.fetch_member(interaction.user.id)
        sub_msg = await scheduler.sub(member, self.minecraft_notif_role, "the Minecraft server", unsub=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)

    @unsub_command_group.command(name="club", description="Stop receiving notifications about our upcoming Corporate Clash club!")
    async def club_unsub(self, interaction: Interaction):
        member = await self.guild.fetch_member(interaction.user.id)
        sub_msg = await scheduler.sub(member, self.club_notif_role, "the upcoming Corporate Clash club", unsub=True)
        return await interaction.response.send_message(sub_msg, ephemeral=True)


async def setup(client):
    await client.add_cog(Notifications(client), guild=Object(id=config.guild_id))
