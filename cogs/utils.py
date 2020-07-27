"""
Created by Epic at 7/26/20
"""
import logging

import discord
from discord.ext import commands
import config
from datetime import datetime
import asyncio


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("hub_bot.cogs.utils")

    async def mod_poll(self, embed: discord.Embed):
        message: discord.Message = await self.bot.get_channel(config.VERIFICATION_CHANNEL).send(embed=embed)
        await message.add_reaction(config.ACCEPT_EMOJI)
        await message.add_reaction(config.DENY_EMOJI)

        def check(reaction: discord.Reaction, _):
            return reaction.message.id == message.id
        await asyncio.sleep(1)
        r, _ = await self.bot.wait_for("reaction_add", check=check)
        await message.delete()
        if str(r) == config.ACCEPT_EMOJI:
            return True
        return False

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


    async def get_commits(self, github_user, github_repo):
        r = await self.utils.request("GET", f"{self.github_baseuri}/repos/{github_user}/{github_repo}/commits",
                                     headers=self.auth_headers)
        return await r.json()

    def parse_commits(self, commits_json: list):
        parsed_commits = []
        for commit in commits_json:
            parsed_commits.append({
                "hash": commit["sha"],
                "author": commit["author"]["login"] if commit["author"] is not None else commit["commit"]["author"][
                    "name"],
                "message": commit["commit"]["message"]
            })
        return parsed_commits



def setup(bot):
    bot.add_cog(Utils(bot))

