import sys

import aiohttp
from discord import app_commands, TextChannel, Embed, ButtonStyle
from discord.errors import Forbidden, HTTPException
from discord.ext import commands
from discord.utils import MISSING
from termcolor import cprint

import config
from handlers import database
from handlers.component_globals import *
from main import ShinyEevee


class CustomRoleView(ComponentBase):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Custom Role", custom_id="custom_role_button", style=ButtonStyle.blurple))

class Roles(commands.Cog, name="roles"):
    def __init__(self, bot):
        self.bot: ShinyEevee = bot
        self.roles_channel: TextChannel | None = None

    @commands.Cog.listener()
    async def on_ready(self):
        [self.bot.tree.add_command(command, guilds=self.bot.guilds) for command in self.get_app_commands()]

    @app_commands.command(name="customrole", description="set your own custom role color with this nice little slash command :)")
    @app_commands.describe(color="the hex color for your role. you can leave out the # if you like. set to 0 to clear color!",
                           name="the name for your role. leave it blank if you don't wanna change it!",
                           icon="the URL of a role icon you want. must be under 256kb!!")
    async def custom_role(self, interaction: Interaction, color: str | None = None, name: str | None = None, icon: str | None = None):
        await self.configure_custom_role(interaction, color, name, icon)

    @commands.command(name="setcustomrole", aliases=["scr"])
    async def set_custom_role(self, ctx: Context, user_id: int, role_id: int):
        if ctx.author.id != config.madi_id:
            return
        database.edit_custom_role(str(ctx.guild.id), str(user_id), role_id)
        return await ctx.send(f"Set <@{user_id}>'s custom role to <@&{role_id}>!")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if "custom_id" not in interaction.data:
            return
        if not interaction.data["custom_id"] == "custom_role_button":
            return
        custom_roles_db = database.get_custom_roles()
        color_placeholder = "Awaiting your input...!"
        name_placeholder = interaction.user.display_name
        icon_placeholder = "The URL of a role icon you want. Must be under 256kb!!"
        if role_id := custom_roles_db.get(interaction.guild.id, {}).get(str(interaction.user.id)):
            role = interaction.guild.get_role(role_id)
            color_placeholder = hex(int(role.colour)).replace('0x', '#')
            name_placeholder = role.name
            icon_placeholder = role.icon.url
        custom_role_modal = ModularModal(
            timeout=1200,
            title="Configure Your Custom Role",
            inputs=[TextInputInfo(
                label='Role Color', style=TextStyle.short, placeholder=color_placeholder,
                max_length=7, required=False, custom_id="color",
            ), TextInputInfo(
                label='Role Name', style=TextStyle.short, placeholder=name_placeholder,
                max_length=32, required=False, custom_id="name",
            ), TextInputInfo(
                label='Role Icon', style=TextStyle.short, placeholder=icon_placeholder[:99],
                max_length=1000, required=False, custom_id="icon",
            ),]
        )
        await interaction.response.send_modal(custom_role_modal)
        timed_out = await custom_role_modal.wait()  # Wait for stop() or timeout
        if timed_out:
            return

        component_data = ModalComponentData(custom_role_modal.interaction)
        await self.configure_custom_role(custom_role_modal.interaction, *component_data.value)

    @commands.command(name="refreshcustomroleembed", aliases=["rcre"])
    async def refresh_custom_role_embed(self, ctx: Context):
        if ctx.channel.id != 997571188727492749:
            return
        if old_msg := await self.get_custom_role_embed():
            await old_msg.delete()
        await self.send_custom_role_embed()

    async def get_custom_role_embed(self):
        async for msg in self.roles_channel.history(limit=5):
            if msg.components and msg.author == self.bot.user:
                if getattr(msg.components[0], "custom_id", None) == "custom_role_button":
                    return msg

    async def send_custom_role_embed(self):
        await self.roles_channel.send(embed=Embed(
            title="💭 Custom Role",
            type="rich",
            description="Want to have a custom name color, or an icon next to your name? Use the button below to open up a UI to easily set that up!",
        ), view=CustomRoleView())

    async def configure_custom_role(self, interaction: Interaction, color: str | None = None,
                                    name: str | None = None, icon: str | None = None):
        if interaction.guild_id not in config.custom_role_allowed_servers:
            return await interaction.response.send_message(f"Sorry, seems custom roles haven't been enabled in this server. Ask Madi about it!!", ephemeral=True)
        if not name and not color and not icon:
            return await interaction.response.send_message(f"Oh, okay... but nothing changed.", ephemeral=True)
        custom_roles_db = database.get_custom_roles()
        icon_file: bytes | None = None
        if icon:
            if interaction.guild.premium_tier < 2:
                return await interaction.response.send_message("Sorry, seems there's not enough server boosters in here for you to set an icon.", ephemeral=True)
            async with aiohttp.ClientSession() as session:
                async with session.get(icon) as resp:
                    if resp.status != 200:
                        return await interaction.response.send_message("Sorry, I couldn\'t download the file for some reason.", ephemeral=True)
                    icon_file = await resp.read()
                    if sys.getsizeof(icon_file) >= 256000:
                        return await interaction.response.send_message("Sorry, this file is too big, they have to be under 256kb!!", ephemeral=True)
        if not custom_roles_db.get(str(interaction.guild.id), {}).get(str(interaction.user.id)):
            if not name:
                name = interaction.user.display_name
            role = await interaction.guild.create_role(name=name)
            cprint(f"Created role {name} ({role.id})", "yellow")
            await interaction.user.add_roles(role)
            cprint(f"Added role {name} ({role.id}) to user {interaction.user.name} {interaction.user.id}", "yellow")
            database.edit_custom_role(str(interaction.guild.id), str(interaction.user.id), role.id)
        else:
            role = interaction.guild.get_role(custom_roles_db.get(str(interaction.guild.id), {}).get(str(interaction.user.id)))
            if role:
                await interaction.user.add_roles(role)  # Make sure they have the role of course
                cprint(f"Added role {role.name} ({role.id}) to user {interaction.user.name} {interaction.user.id}", "yellow")
        try:
            await role.edit(
                name=name if name else MISSING,
                colour=int(color.replace('#', ''), base=16) if color else MISSING,
                display_icon=icon_file if icon_file else MISSING)
            cprint(f"Edited role {name} ({role.id})", "yellow")
        except (Forbidden, HTTPException, ValueError):
            return await interaction.response.send_message(f"Sorry, something went wrong while updating your role.", ephemeral=True)
        return await interaction.response.send_message(f"Okay, your custom role has been set to <@&{role.id}>!!", ephemeral=True)


async def setup(client):
    await client.add_cog(Roles(client), guilds=client.guilds)
