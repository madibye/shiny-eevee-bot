import traceback

from discord import Game, Intents, Object
from discord.ext.commands import Bot
from termcolor import cprint

import config

intents = Intents.all()


class Amelia(Bot):
    def __init__(self):
        super().__init__(command_prefix=["!"], help_command=None, application_id=config.bot_application_id, intents=intents)

    async def setup_hook(self):
        from config.live_config import lc  # Please don't worry about why this is here
        lc.load()  # Anyways, let's also wait for the live config to load up before starting
        for extension in config.discord_cogs:
            try:
                await bot.load_extension(extension)
                cprint(f"Loaded extension {extension}", "green")
            except Exception as error:
                traceback.print_exc()
                cprint(f"Cog {extension} could not be loaded for reason: {error}", "red")
        await bot.tree.sync(guild=Object(id=config.guild_id))  # Sync our slash commands

    @staticmethod
    async def on_ready():
        cprint(f"I've logged in as {bot.user.name}. I'm ready to go!", "green")
        await bot.change_presence(activity=Game(name="hiiiiiii :)"))
        for guild in bot.guilds:
            if guild.id != config.guild_id:
                await guild.leave()


if __name__ == "__main__":
    bot = Amelia()
    bot.run(config.discord_token, log_level=40)
