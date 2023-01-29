import io

import aiohttp
from discord import Guild, app_commands, Object, File
from discord.ext import commands
from discord.utils import MISSING
from discord.errors import Forbidden, HTTPException

import config
from helpers import db
from helpers.component_globals import *
from main import Madi


class Roles(commands.Cog, name="roles"):
    def __init__(self, bot):
        self.bot: Madi = bot
        self.guild: Guild | None = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(config.guild_id)

    @app_commands.command(name="customrole", description="set your own custom role color with this nice little slash command :)")
    @app_commands.describe(color="the hex color for your role. you can leave out the # if you like. set to 0 to clear color!",
                           name="the name for your role. leave it blank if you don't wanna change it!")
    async def custom_role(self, interaction: Interaction, color: str | None = None, name: str | None = None, icon: str | None = None):
        if not name and not color and not icon:
            return await interaction.response.send_message(f"oh okay... but nothing changed :(", ephemeral=True)
        custom_roles_db = db.get_custom_roles()
        icon_file: File | None = None
        if icon:
            async with aiohttp.ClientSession() as session:
                async with session.get(icon) as resp:
                    if resp.status != 200:
                        return await interaction.response.send_message('Could not download file...', ephemeral=True)
                    icon_file = File(io.BytesIO(await resp.read()))
        if not custom_roles_db.get(str(interaction.user.id)):
            if not name:
                name = interaction.user.display_name
            role = await self.guild.create_role(name=name)
            await role.edit(position=20)
            await interaction.user.add_roles(role)
            db.edit_custom_role(str(interaction.user.id), role.id)
        else:
            role = self.guild.get_role(custom_roles_db[str(interaction.user.id)])
            await interaction.user.add_roles(role)  # Make sure they have the role of course
        try:
            await role.edit(
                name=name if name else MISSING,
                colour=int(color.replace('#', ''), base=16) if color else MISSING,
                display_icon=icon_file if icon_file else MISSING)
        except (Forbidden, HTTPException, ValueError):
            return await interaction.response.send_message(f"Sorry, something went wrong while updating your role.")
        return await interaction.response.send_message(f"Your custom role has been set to <@&{role.id}>!", ephemeral=True)

    @commands.command(name="setcustomrole", aliases=["scr"])
    @commands.has_role("alpha koala")
    async def set_custom_role(self, ctx: Context, user_id: int, role_id: int):
        if ctx.channel.id != 997571188727492749:
            return
        db.edit_custom_role(str(user_id), role_id)
        return await ctx.send(f"Set <@{user_id}>'s custom role to <@&{role_id}>!")


async def setup(client):
    await client.add_cog(Roles(client), guild=Object(id=config.guild_id))
