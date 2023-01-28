import random
from typing import List, Dict

from discord import Object, Embed
from discord.ext.commands import Context, Cog, command

import config
from helpers import command_helpers
from helpers.type_matchups import type_list, PTN


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
        types: List[PTN] = [*set(PTN[t.capitalize()] for t in command_helpers.remove_empty_items(
            " ".join(command_helpers.parse_args(ctx)).replace("/", " ").lower().split(" ")
        ))]
        type_matchups: Dict[PTN, int] = {_type: 1 for _type in type_list}
        for t in types:
            if t not in type_matchups.keys():
                return await ctx.send("looks like there's something wrong with the list of types you gave me...")
            for w in type_list[t].weak:
                type_matchups[w] *= 2
            for r in type_list[t].resist:
                type_matchups[r] *= 0.5
            for i in type_list[t].immune:
                type_matchups[i] = 0
        matchup_lists: Dict[str, str] = {"Weaknesses": "", "Resistances": "", "Immunities": ""}
        for key in type_matchups:
            mult = type_matchups[key]
            if mult == 0:
                matchup_lists["Immunities"] += f"{key.name}, "
            elif mult > 1:
                matchup_lists["Weaknesses"] += f"{key.name}{f' ({mult}x)' if mult != 2 else ''}, "
            elif mult < 1:
                matchup_lists["Resistances"] += f"{key.name}{f' ({mult}x)' if mult != 0.5 else ''}, "
        embed = Embed(title="**Type Matchups**", description=f"{'/'.join([_type.name.capitalize() for _type in types])}-type")
        [embed.add_field(name=key, value=matchup_lists[key][0:-2], inline=False) for key in matchup_lists if len(matchup_lists[key]) > 0]
        return await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(Fun(client), guild=Object(id=config.guild_id))
