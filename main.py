import traceback
import discord
from discord.ext.commands import Bot
from discord import Game
from termcolor import cprint
from discord_slash import SlashCommand

import config

intents = discord.Intents.default()
intents.members = True

bot = Bot(command_prefix=config.command_prefixes, help_command=None, intents=intents)
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)

@bot.event
async def on_ready():
    cprint(f"I've logged in as {bot.user.name}. I'm ready to go!", "green")
    for guild in bot.guilds:
        print(f"{guild.name} ({guild.id}): {[member.name for member in guild.members]}")
    await bot.change_presence(activity=Game(name=config.activity_text))

if __name__ == "__main__":
    for extension in config.discord_cogs:
        try:
            bot.load_extension(extension)
            cprint(f"Loaded extension {extension}", "green")
        except Exception as error:
            traceback.print_exc()
            cprint(f"Cog {extension} could not be loaded for reason: {error}", "green")
    bot.run(config.discord_token)
