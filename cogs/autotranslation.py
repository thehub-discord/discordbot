"""
Created by Epic at 7/2/20
"""
import logging

import discord
import googletrans
from discord.ext import commands


class AutoTranslation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("hub_bot.cogs.autotranslation")
        self.translator = googletrans.Translator()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        detected = self.translator.detect(message.content)
        if detected.confidence < .85:
            return

        translated = self.translator.translate(message.content)
        if translated.src == "en" or translated.text == message.content:
            return
        await message.channel.send(translated.text)


def setup(bot):
    bot.add_cog(AutoTranslation(bot))

