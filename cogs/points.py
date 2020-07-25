"""
Created by Epic at 7/2/20
"""
import logging
from discord.ext import commands, tasks
import config
import discord
from models import User
from datetime import datetime
import dateutil.parser
import asyncio
import math
from copy import deepcopy


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

    async def get_commits(self, github_user, github_repo):
        r = await self.request("GET", f"{self.github_baseuri}/repos/{github_user}/{github_repo}/commits", headers=self.auth_headers)
        return await r.json()

    def parse_commits(self, commits_json: list):
        parsed_commits = []
        for commit in commits_json:
            parsed_commits.append({
                "hash": commit["sha"],
                "author": commit["author"]["login"] if commit["author"] is not None else commit["commit"]["author"],
                "message": commit["commit"]["message"]
            })
        return parsed_commits

    async def request(self, *args, **kwargs):
        r = await self.bot.http_session.request(*args, **kwargs)

        headers = r.headers
        if headers.get("X-RateLimit-Remaining", None) == "0":
            reset_time = int(headers["X-RateLimit-Reset"])
            current_time = datetime.utcnow().timestamp()
            sleep_time = reset_time - current_time
            self.logger.info(f"Ratelimited! Sleeping for {sleep_time}s")
            await asyncio.sleep(sleep_time)
            r = await self.request(*args, **kwargs)
        return r



def setup(bot):
    bot.add_cog(Points(bot))
