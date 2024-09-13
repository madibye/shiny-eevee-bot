import traceback

from discord import Game, Intents, Object
from discord.ext.commands import Bot
from termcolor import cprint

import config

intents = Intents.all()


class ShinyEevee(Bot):
    def __init__(self):
        super().__init__(command_prefix=["!"], help_command=None, application_id=config.bot_application_id, intents=intents)

    async def setup_hook(self):
        from config.live_config import lc  # Please don't worry about why this is here
        lc.load()  # Anyways, let's also wait for the live config to load up before starting
        for command in await self.tree.fetch_commands():
            self.tree.remove_command(command.name)
        for extension in config.discord_cogs:
            try:
                await self.load_extension(extension)
                cprint(f"Loaded extension {extension}", "green")
            except Exception as error:
                traceback.print_exc()
                cprint(f"Cog {extension} could not be loaded for reason: {error}", "red")
        for guild in self.guilds:
            await self.tree.sync(guild=Object(guild.id))  # Sync slash commands for each server
            if guild.id in [guild.id for guild in (await self.fetch_user(188875600373481472)).mutual_guilds]:
                continue
            cprint(f"Leaving guild {guild.name} {guild.id}", "red")
            await guild.leave()
        await self.tree.sync()  # Sync our global slash commands

    @staticmethod
    async def on_ready():
        cprint(f"I've logged in as {bot.user.name}. I'm ready to go!", "green")
        await bot.change_presence(activity=Game(name=config.activity_text))


if __name__ == "__main__":
    bot = ShinyEevee()
    bot.run(config.discord_token, log_level=40)
