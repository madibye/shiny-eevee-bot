from typing import List, Dict
import random

from discord import Object, Embed
from discord.ext.commands import Context, Cog, command

import config
from helpers import command_helpers
from helpers.type_matchups import type_list, PokemonType, PTN


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
        types: List[PTN] = [PTN[t.capitalize()] for t in command_helpers.remove_empty_items(
            " ".join(command_helpers.parse_args(ctx)).replace("/", " ").lower().split(" ")
        )]
        if len(types) > 2:
            types = types[0:1]
        if len(types) == 2:
            if types[0] == types[1]:
                types = [types[0]]
        current_type_matchup: Dict[PTN, int] = {}
        for type_name in type_list:
            current_type_matchup[type_name] = 1
        for t in types:
            if t not in current_type_matchup.keys():
                return await ctx.send("looks like there's something wrong with the list of types you gave me...")
            ptype: PokemonType = type_list[t]
            for w in ptype.weak:
                current_type_matchup[w] *= 2
            for r in ptype.resist:
                current_type_matchup[r] *= 0.5
            for i in ptype.immune:
                current_type_matchup[i] = 0
        matchup_lists: Dict[str, str] = {"Weaknesses": "", "Resistances": "", "Immunities": ""}
        for key in current_type_matchup:
            if current_type_matchup[key] == 1:
                continue
            elif current_type_matchup[key] == 4:
                matchup_lists["Weaknesses"] += f"**{key.name}**, "
            elif current_type_matchup[key] == 2:
                matchup_lists["Weaknesses"] += f"{key.name}, "
            elif current_type_matchup[key] == 0.5:
                matchup_lists["Resistances"] += f"{key.name}, "
            elif current_type_matchup[key] == 0.25:
                matchup_lists["Resistances"] += f"**{key.name}**, "
            elif current_type_matchup[key] == 0:
                matchup_lists["Immunities"] += f"{key.name}, "
        clean_typing = f"{types[0].capitalize()}/{types[1].capitalize()}" if len(types) == 2 else types[0].capitalize()
        embed = Embed(title="**Type Matchups**", description=f"{clean_typing}-type")
        for key in matchup_lists:
            if len(matchup_lists[key]) > 0:
                embed.add_field(name=key, value=matchup_lists[key][0:-2], inline=False)
        return await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(Fun(client), guild=Object(id=config.guild_id))
