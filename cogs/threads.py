from discord import Thread
from discord.ext import commands
from discord.ext.commands import Context

from handlers import database


class Threads(commands.Cog, name="Threads"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name="threadkeepalive", aliases=["tka"])
    async def thread_keep_alive(self, ctx: Context):
        if not isinstance(ctx.channel, Thread):
            return await ctx.send("to keep a thread alive, use this in a thread!")
        keep_alive_threads = database.get_keep_alive_threads()
        if ctx.channel.id not in keep_alive_threads:
            database.add_keep_alive_thread(ctx.channel.id)
            return await ctx.send("okay, i'll keep this thread alive for you :)! use this again in this "
                                  "channel if you want me to stop reviving this thread!")
        database.remove_keep_alive_thread(ctx.channel.id)
        return await ctx.send("okay, i won't keep this thread alive anymore... hope it's okay on its own :(")

    @commands.Cog.listener()
    async def on_thread_update(self, before: Thread, after: Thread):
        if not before.archived and after.archived:  # when a thread archival happens
            keep_alive_threads = database.get_keep_alive_threads()
            if after.id in keep_alive_threads:
                return await after.edit(archived=False)


async def setup(client):
    await client.add_cog(Threads(client), guilds=client.guilds)
