from discord import Thread
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db

class Threads(commands.Cog, name="Threads"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name="threadkeepalive", aliases=["tka"])
    async def thread_keep_alive(self, ctx: Context):
        if not isinstance(ctx.channel, Thread):
            return await ctx.send("To keep a thread alive, use this command in a thread!")
        keep_alive_threads = db.get_keep_alive_threads()
        if ctx.channel.id not in keep_alive_threads:
            db.add_keep_alive_thread(ctx.channel.id)
            return await ctx.send("Okie, I'll keep this thread alive for you! Use `!threadkeepalive` again in this "
                                  "channel if you want me to stop reviving this thread!")
        db.remove_keep_alive_thread(ctx.channel.id)
        return await ctx.send("Alright, I won't keep this thread alive anymore!")

    @commands.Cog.listener()
    async def on_thread_update(self, before: Thread, after: Thread):
        if not before.archived and after.archived:  # when a thread archival happens
            keep_alive_threads = db.get_keep_alive_threads()
            if after.id in keep_alive_threads:
                return await after.edit(archived=False)


async def setup(client):
    await client.add_cog(Threads(client))
