import random

from discord import Object, Embed
from discord.ext.commands import Context, Cog, command

import config
from handlers import command_helpers
from handlers.type_matchups import PokeType, generate_type_loops


class Fun(Cog, name="Fun"):
    def __init__(self, bot):
        self.bot = bot

    @command(name="magicball", aliases=["8", "8ball"])
    async def magicball(self, ctx):
        answer = random.choice(config.magicball_answers)
        await ctx.send(answer)

    @command(name="pick", aliases=["p"])
    async def pick(self, ctx, *, options: str):
        options_list: list[str] = options.split(',')
        if len(options_list) == 0:
            return  # Died
        pick_total = 1
        if options.startswith(("pick:", "choose:", "total:", "p:")):
            if (
                stripped_first_option := options_list[0].removeprefix("pick:").removeprefix("choose:")
                    .removeprefix("total:").removeprefix("p:")
            ).split(" ")[0].isnumeric():
                options_list[0] = stripped_first_option
                if len(split_first_option := stripped_first_option.split(" ")) > 1:
                    options_list[0] = split_first_option[0]
                    options_list.insert(1, " ".join(split_first_option[1:]))
                pick_total = int(options_list.pop(0))
        answers = []
        while len(answers) < pick_total and len(options_list):
            if not (choice := random.choice(options_list)).isspace():
                answers.append(choice.strip())
            options_list.remove(choice)
        if len(answers) == 2:
            answers_str = ' and '.join(answers)
        elif len(answers) == 1:
            answers_str = answers[0]
        else:
            answers[-1] = f'and {answers[-1]}'
            answers_str = ', '.join(answers)
        await ctx.send(f"I've decided, you should pick **{answers_str}**!")

    @command(name="biglist")
    async def big_list(self, ctx: Context):
        if ctx.author.id != 188875600373481472:
            return
        await ctx.send("Okie, I'll go ahead and start working on that!! I'll letcha know when I'm all finished up :)")
        generate_type_loops(3, 2)
        await ctx.send("I'm done!!")

    @command(name="weakness", aliases=["weak", "w"])
    async def weakness(self, ctx: Context):
        type_input: list[PokeType] = [PokeType[t.capitalize()] for t in command_helpers.remove_empty_items(
            " ".join(command_helpers.parse_args(ctx)).replace("/", " ").lower().split(" "))]
        types = [t for i, t in enumerate(type_input) if (t not in type_input[:i]) and (t in PokeType)]
        if not types:
            return await ctx.send("looks like there's something wrong with the list of types you gave me...")
        matchups: dict[PokeType, int] = {_type: 1 for _type in PokeType}
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
