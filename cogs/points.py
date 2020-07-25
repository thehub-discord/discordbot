"""
Created by Epic at 7/2/20
"""
import logging
from discord.ext import commands, tasks
import config
import discord
from models import User


class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("hub_bot.cogs.points")
        self.queue = []
        self.auth_headers = {"Authorization": f"Token {config.GITHUB_TOKEN}"}
        self.github_baseuri = "https://api.github.com"

    @commands.command()
    async def start(self, ctx: commands.Context, github: str):
        if len(github) > 100:
            return await ctx.send("Invalid github username")
        if ctx.author.id in self.queue:
            return await ctx.send("You are already in the queue!")
        if self.bot.db_session.query(User).get(ctx.author.id) is not None:
            return await ctx.send("You already have a github connected!")
        self.queue.append(ctx.author.id)
        embed = discord.Embed(title="Verify GitHub account",
                              description=f"User: {ctx.author.mention}\nGitHub username: {github}", color=0x00FFFF
                              )
        message: discord.Message = await self.bot.get_channel(config.VERIFICATION_CHANNEL).send(embed=embed)
        await message.add_reaction(config.ACCEPT_EMOJI)
        await message.add_reaction(config.DENY_EMOJI)

        def check(reaction: discord.Reaction, _):
            return reaction.message.id == message.id

        await ctx.send(f"You have been put in queue for verification! Your posision in queue: {len(self.queue)}")
        r, _ = await self.bot.wait_for("reaction_add", check=check)
        self.queue.remove(ctx.message.author.id)
        if str(r) == config.ACCEPT_EMOJI:
            try:
                await ctx.author.send("Your github has been connected!")
            except discord.Forbidden:
                pass
            user = User(id=ctx.author.id, github_username=github)
            self.bot.db_session.add(user)
            self.bot.db_session.commit()
        else:
            try:
                await ctx.author.send(
                    "Your github connection has been denied! Remember to have the github integration on your account public & make sure it doesnt contain any typos!")
            except discord.Forbidden:
                pass
        await message.delete()

    async def fetch_notifications(self):
        headers = self.auth_headers.copy()
        body = {
            "all": True
        }
        request = await self.bot.http_session.get(f"{self.github_baseuri}/notifications", headers=headers, json=body)
        return await request.json()

    async def follow_repository(self, owner, repo):
        request = await self.bot.http_session.put(f"{self.github_baseuri}/repos/{owner}/{repo}/subscription",
                                                  headers=self.auth_headers, json={"subscribed": True})
        return await request.json()


def setup(bot):
    bot.add_cog(Points(bot))
