import math

from discord import Embed, Interaction, ButtonStyle
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ui import Button

from config import *
from handlers import database, paginator
from handlers.component_globals import ComponentBase
from main import ShinyEevee


class RoleButtonCreator(Button):
    def __init__(self, role_button, row):
        super().__init__(label=role_button[0], custom_id=f"rolebutton {str(role_button[1])}", style=ButtonStyle.primary, row=row)


class RoleButtons(ComponentBase):
    """
    Dynamically creates our role buttons with RoleButtonCreator
    """
    def __init__(self, buttons, max_row_length):
        super().__init__(timeout=None)
        self.buttons = buttons

        for i, role_button in enumerate(buttons):
            row = math.floor(i/max_row_length)
            self.add_item(RoleButtonCreator(role_button, row))


class RolePicker(commands.Cog, name="role_picker"):
    def __init__(self, bot):
        self.bot: ShinyEevee = bot

    @commands.has_any_role(config.admin_roles)
    @commands.command(name="refresh", aliases=["rpr"])
    async def refresh(self, ctx: Context, *args):
        refreshed = await self.role_picker_refresh(*args)
        await ctx.send("i refreshed the role pickers for you! :)" if refreshed else
                       "couldn't find any role pickers with that name :(", reference=ctx.message)

    @commands.has_any_role(config.admin_roles)
    @commands.command(name="viewrolepickers", aliases=["viewrolepickerinfo", "vrpi", "vrp"])
    async def view_role_picker_info(self, ctx: Context):
        info_embeds = []
        role_picker_list = database.get_role_picker_db()
        for key, role_picker_info in role_picker_list.items():
            embed = Embed(title=role_picker_info.embed_name, description=role_picker_info.embed_desc)
            embed.add_field(name="ID:", value=key)
            embed.add_field(name="Channel:", value=f"<#{role_picker_info.channel_id}>")
            embed.add_field(name="Max Row Length:", value=role_picker_info.max_row_length)
            roles_str = "No roles yet!"
            if role_picker_info.role_ids:
                roles_str = "<@&"
                for role_id in role_picker_info.role_ids:
                    roles_str += f"{str(role_id)}> <@&"
                roles_str = roles_str[:-4]
            embed.add_field(name="Roles:", value=roles_str)
            info_embeds.append(embed)
        p = paginator.Paginator(ctx, info_embeds, self.bot)
        await p.paginate()

    @commands.has_any_role(config.admin_roles)
    @commands.command(name="addrolepicker", aliases=["arp"])
    async def add_role_picker(self, ctx: Context, key: str):
        role_picker_list = database.get_role_picker_db()
        if key in role_picker_list:
            return await ctx.send(
                f"a role picker with the ID of {key} already exists, i can't replace it :(", reference=ctx.message)
        role_picker_list[key] = RolePickerInfo(channel_id=ctx.channel.id)
        database.set_role_picker_db(role_picker_list)
        return await ctx.send(
            f"okay, i made a new role picker with the ID of {key} in this channel. "
            f"use `!editrolepicker` to set its properties before `!refresh`ing it into existence, pleeeease :)",
            reference=ctx.message)

    @commands.has_any_role(config.admin_roles)
    @commands.command(name="removerolepicker", aliases=["killrolepicker", "krp", "rrp"])
    async def remove_role_picker(self, ctx: Context, key: str):
        role_picker_list = database.get_role_picker_db()
        if key not in role_picker_list:
            return await ctx.send(f"i can't find a role picker with the ID of {key} :(", reference=ctx.message)
        await self.delete_role_picker(role_picker_list[key])  # Delete the current message for this role picker to avoid confusion later
        role_picker_list.pop(key)  # And kill the role picker from the DB
        database.set_role_picker_db(role_picker_list)
        return await ctx.send(f"okay, i deleted the role picker with the ID of {key}... sad to see it go :(", reference=ctx.message)

    @commands.has_any_role(config.admin_roles)
    @commands.command(name="editrolepicker", aliases=["editrp", "erp"])
    async def edit_role_picker(self, ctx: Context, key: str, value: str, *, args: str):
        role_picker_list = database.get_role_picker_db()
        if key not in role_picker_list:
            return await ctx.send(f"i can't find a role picker with the ID of {key} :(", reference=ctx.message)

        # Channel ID
        if value in ['channel_id', 'channel', 'ch', 'c']:
            if not args.isnumeric():
                return await ctx.send(f"Couldn't change to channel {args}: In order to change the channel of a role picker, you need to input a valid channel ID!", reference=ctx.message)
            if int(args) not in [channel.id for channel in ctx.guild.channels]:
                return await ctx.send(f"Couldn't change to channel {args}: This channel ID isn't a channel in this server!", reference=ctx.message)
            role_picker_list[key].channel_id = int(args)
            database.set_role_picker_db(role_picker_list)
            return await ctx.send(f"I've set the channel for role picker **{key}** to <#{args}>!", reference=ctx.message)

        # Role IDs
        if value in ['role_ids', 'roles', 'role', 'r']:
            if not args.startswith('add ') and not args.startswith('remove ') and not args.startswith('a ') and not args.startswith('r '):
                return await ctx.send(f"You need to use `add` or `remove` (aliases `a` or `r`, respectively) if you want to edit this role picker's roles!", reference=ctx.message)
            args_list = args.split(' ')
            if len(args_list) < 2:
                return await ctx.send(f"Please specify the ID(s) of the role(s) you want to edit.", reference=ctx.message)
            role_ids = args_list[1:]
            updated = False
            for role in role_ids:
                if not role.isnumeric():
                    await ctx.send(f"Couldn't {'add' if args.startswith('a') else 'remove'} role {role}: In order to edit the roles of a role picker, you need to input a valid role ID!")
                    continue
                if int(role) not in [r.id for r in ctx.guild.roles]:
                    await ctx.send(f"Couldn't {'add' if args.startswith('a') else 'remove'} role {role}: This role ID isn't a role in this server!")
                    continue
                if args.startswith('a'):
                    if int(role) in role_picker_list[key].role_ids:
                        await ctx.send(f"Couldn't add role {role}: This role is already apart of this role picker!")
                        continue
                    if len(role_picker_list[key].role_ids) + 1 > (5 * role_picker_list[key].max_row_length):
                        await ctx.send(f"Couldn't add role {role}: You have too many roles, the role picker would be unable to send with the current max row length.")
                        continue
                    role_picker_list[key].role_ids.append(int(role))
                    updated = True
                elif args.startswith('r'):
                    if int(role) not in role_picker_list[key].role_ids:
                        await ctx.send(f"Couldn't remove role {role}: This role isn't part of this role picker!")
                        continue
                    role_picker_list[key].role_ids.remove(int(role))
                    updated = True
            if not updated:
                return
            database.set_role_picker_db(role_picker_list)
            return await ctx.send(f"I've finished updating the role IDs! Use `!viewrolepickers` to check and make sure "
                                  f"everything looks right before refreshing!", reference=ctx.message)

        # Embed name
        if value in ['embed_name', 'name', 'title', 'n', 't']:
            if len(args) > 250:
                return await ctx.send(f"Couldn't edit embed title: This embed title is too long! Please keep it below 250 characters.")
            role_picker_list[key].embed_name = args
            database.set_role_picker_db(role_picker_list)
            return await ctx.send(f"I've set the embed title for role picker **{key}** to:\n\n**{args}**", reference=ctx.message)

        # Embed description
        if value in ['embed_desc', 'description', 'desc', 'd']:
            if len(args) > 2000:
                return await ctx.send(f"Couldn't edit embed title: This embed title is too long! Please keep it below 2000 characters.", reference=ctx.message)
            role_picker_list[key].embed_desc = args
            database.set_role_picker_db(role_picker_list)
            return await ctx.send(f"I've set the embed description for role picker **{key}** to:\n\n{args}", reference=ctx.message)

        # Max row length
        if value in ['max_row_length', 'row_length', 'length', 'mrl', 'rl', 'l']:
            if not args.isnumeric():
                return await ctx.send(f"Couldn't edit max row length: Please input an integer value!")
            if not (1 <= int(args) <= 5):
                return await ctx.send(f"Couldn't edit max row length: Please input an integer value between 1 and 5.")
            if len(role_picker_list[key].role_ids) > (5 * int(args)):
                return await ctx.send(f"Couldn't edit max row length: You have too many roles, the role picker would be unable to send with this max row length.")
            role_picker_list[key].max_row_length = int(args)
            database.set_role_picker_db(role_picker_list)
            return await ctx.send(f"I've set the max row length for role picker **{key}** to **{args}**!", reference=ctx.message)

        else:
            return await ctx.send(f"You're trying to edit a property that is invalid! Please select one of the following properties:\n"
                                  f"`channel_id` (aliases: `channel`, `ch`, `c`)\n`role_id` (aliases: `roles`, `role`, `r`)\n"
                                  f"`embed_name` (aliases: `name`, `title`, `n`, `t`)\n`embed_desc` (aliases: `description`, `desc`, `d`)\n"
                                  f"`max_row_length` (aliases: `row_length`, `length`, `mrl`, `rl`, `l`)", reference=ctx.message)

    async def role_picker_refresh(self, *args):
        """
        :param args: List all IDs of role pickers you want to refresh
        :return: Whether or not any role pickers were refreshed via this method
        """
        role_picker_list = database.get_role_picker_db()
        refreshed = False  # How we'll keep track of whether or not we've done anything here

        # Now let's repost new ones for the session
        for key, role_picker in role_picker_list.items():
            if (args and key not in args) or (not role_picker.channel_id):
                continue
            # First we delete the old message
            await self.delete_role_picker(role_picker)
            database.remove_role_picker_msg(key)
            # Now we can repost!!!
            msg = await self.post_role_picker(role_picker)
            database.add_role_picker_msg(key, msg.channel.id, msg.id)
            refreshed = True

        return refreshed

    async def post_role_picker(self, role_picker_info: RolePickerInfo):
        """
        :param role_picker_info: The RolePickerInfo object you want to send
        :return: The Message object that gets sent by this bot
        """
        channel = self.bot.get_channel(role_picker_info.channel_id)
        embed = Embed(title=role_picker_info.embed_name, description=role_picker_info.embed_desc)
        if not role_picker_info.role_ids or role_picker_info.max_row_length > 5:
            return await channel.send(embed=embed)  # In these cases, we'll send a role picker without any buttons.

        buttons = []
        for role_id in role_picker_info.role_ids:
            role = channel.guild.get_role(role_id)
            buttons.append((role.name, role.id))

        return await channel.send(embed=embed, view=RoleButtons(buttons, role_picker_info.max_row_length))

    async def delete_role_picker(self, role_picker_info: RolePickerInfo):
        try:
            if role_picker_info.message_data['channel_id'] and role_picker_info.message_data['message_id']:
                channel = await self.bot.fetch_channel(role_picker_info.message_data['channel_id'])
                message = await channel.fetch_message(role_picker_info.message_data['message_id'])
                await message.delete()
        except NotFound:  # The message got deleted beforehand :(
            pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if "custom_id" not in interaction.data:
            return
        if not interaction.data["custom_id"].startswith("rolebutton "):
            return
        role_id = interaction.data["custom_id"].replace("rolebutton ", "")
        role = interaction.guild.get_role(int(role_id))

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                content=f"I've removed the **{role.name}** role from you. Feel free to press the button again if you'd like me to give you the role back!",
                ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                content=f"I've given the **{role.name}** role to you. Feel free to press the button again if you'd like me to remove it!",
                ephemeral=True
            )

async def setup(client):
    await client.add_cog(RolePicker(client), guilds=client.guilds)
