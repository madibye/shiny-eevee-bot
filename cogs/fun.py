import random
from typing import List, Dict

from discord import Object, Embed
from discord.ext.commands import Context, Cog, command

import config
from helpers import command_helpers
from helpers.type_matchups import PTN


class Fun(Cog, name="Fun"):
    def __init__(self, bot):
        self.bot = bot

    @command(name="magicball", aliases=["8", "8ball"])
    async def magicball(self, ctx):
        answer = random.choice(config.magicball_answers)
        await ctx.send(answer)

    @command(name="pick", aliases=["p"])
    async def pick(self, ctx, *, options: str):
        options_list = options.split(',')
        answer = random.choice(options_list).strip()
        await ctx.send(f"I've decided, you should pick **{answer}**!")

    @command(name="weakness", aliases=["weak", "w"])
    async def weakness(self, ctx: Context):
        type_input: List[PTN] = [PTN[t.capitalize()] for t in command_helpers.remove_empty_items(
            " ".join(command_helpers.parse_args(ctx)).replace("/", " ").lower().split(" "))]
        types = [t for i, t in enumerate(type_input) if (t not in type_input[:i]) and (t in PTN)]
        if not types:
            return await ctx.send("looks like there's something wrong with the list of types you gave me...")
        matchups: Dict[PTN, int] = {_type: 1 for _type in PTN}
        for t in types:
            for mult, mult_types in t.get_type_matchups().items():
                for mult_type in mult_types:
                    matchups[mult_type] *= mult
        embed = Embed(title="**Type Matchups**", description=f"{'/'.join([t.name.capitalize() for t in types])}-type")
        embed.add_field(name="Weaknesses", inline=False, value=", ".join(
            [f"{key.name}{f' ({matchups[key]}x)' if matchups[key] != 2 else ''}" for key in matchups if matchups[key] > 1]))
        embed.add_field(name="Resistances", inline=False, value=", ".join(
            [f"{key.name}{f' ({matchups[key]}x)' if matchups[key] != 0.5 else ''}"
             for key in matchups if matchups[key] < 1 and matchups[key] != 0]))
        embed.add_field(name="Immunities", inline=False, value=", ".join([key.name for key in matchups if matchups[key] == 0]))
        return await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(Fun(client), guild=Object(id=config.guild_id))
