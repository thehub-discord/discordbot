"""
Created by vcokltfre - 2020-07-23
"""

import discord
from discord.ext import commands


class MyCog(commands.Cog):
    """A description of what this cog does"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(MyCog(bot))