import config
from helpers.component_globals import *
from helpers import db

from discord import Guild, app_commands, Object
from discord.ext import commands

class Roles(commands.Cog, name="roles"):
    def __init__(self, bot):
        self.bot = bot
        self.guild: Guild = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(config.guild_id)

    @app_commands.command(name="customrole", description="Set your own custom role color with this nice little slash command!")
    async def custom_role(self, interaction: Interaction):
        role_modal = ModularModal(
            timeout=1200,
            title="Custom Role",
            inputs=[TextInputInfo(
                label='Color',
                style=TextStyle.short,
                placeholder='Type out a color code here...',
                max_length=7,
                required=True,
                custom_id="color"
            ), TextInputInfo(
                label='Role Name',
                style=TextStyle.short,
                placeholder='Leave this blank if you don\'t want to change the name..',
                max_length=100,
                required=False,
                custom_id="name"
            )]
        )
        await interaction.response.send_modal(role_modal)

        timed_out = await role_modal.wait()  # Wait for stop() or timeout
        if timed_out:
            return
        color, name = ModalComponentData(role_modal.interaction).value
        custom_roles_db = db.get_custom_roles()
        if str(interaction.user.id) not in custom_roles_db or not custom_roles_db.get(str(interaction.user.id)):
            if not name:
                name = interaction.user.display_name
            try:
                role = await self.guild.create_role(name=name)
                await role.edit(position=20)
            except Exception as e:
                print(e)
                return await role_modal.interaction.response.send_message("sorry, it looks like the name was invalid :(", ephemeral=True)
            await interaction.user.add_roles(role)
            db.edit_custom_role(str(interaction.user.id), role.id)
        else:
            print(custom_roles_db[str(interaction.user.id)])
            role = self.guild.get_role(custom_roles_db[str(interaction.user.id)])
        try:
            await role.edit(colour=int(color.replace('#', ''), base=16))
        except Exception as e:
            print(e)
            return await role_modal.interaction.response.send_message("sorry, it looks like the color was invalid :(", ephemeral=True)
        return await role_modal.interaction.response.send_message(f"your custom role has been set to <@&{role.id}>", ephemeral=True)

    @commands.command(name="setcustomrole", aliases=["scr"])
    @commands.has_role("alpha koala")
    async def set_custom_role(self, ctx: Context, user_id: int, role_id: int):
        if ctx.channel.id != 997571188727492749:
            return
        db.edit_custom_role(str(user_id), role_id)
        return await ctx.send(f"Set <@{user_id}>'s custom role to <@&{role_id}>!")


async def setup(client):
    await client.add_cog(Roles(client), guild=Object(id=config.guild_id))
