"""
Created by Epic at 7/27/20
"""

import logging
import config
import discord
from discord.ext import commands, tasks
from models import Commit
import random


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("hub_bot.cogs.leaderboard")
        self.message = None

    async def create_leaderboard(self):
        if self.message is None:
            loading_embed = discord.Embed(title="Loading...", description="Please wait")
            self.message = await (await self.bot.fetch_channel(config.LEADERBOARD_CHANNEL)).send(embed=loading_embed)

    async def post_leaderboard(self):
        await self.create_leaderboard()
        commits = self.bot.db_session.query(Commit).all()
        num_commits = {}

        embed = discord.Embed(title="Commit leaderboard", color=random.randint(0x0, 0xFFFFFF))
        description = ""
        description += f"**Server total:** {len(commits)} commits\n"

        for commit in commits:
            num_commits[commit.user_id] = num_commits.get(commit.user_id, 0) + 1

        sorted_rankings = reversed(sorted(num_commits.items(), key=lambda items: items[1]))

        ranking = 0
        for userid, users_total_commits in sorted_rankings:
            ranking += 1
            description += f"**{ranking})** <@{userid}> - {users_total_commits}\n"

        embed.description = description
        await self.message.edit(embed=embed)


def setup(bot):
    bot.add_cog(Leaderboard(bot))
