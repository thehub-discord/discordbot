"""
Created by vcokltfre - 2020-07-23
"""

import discord
from discord.ext import commands
from discord.ext.commands import has_any_role

import logging
import config

logger = logging.getLogger("hub_bot")


class Bot(commands.Bot):
    """A subclassed version of commands.Bot"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_cog(self, cog: commands.Cog) -> None:
        """Adds a cog to the bot and logs it."""
        super().add_cog(cog)
        logger.info(f"Cog loaded: {cog.qualified_name}")

    def load_extensions(self, cogs: list):
        """Loads a list of cogs"""
        for cog in cogs:
            try:
                super().load_extension(cog)
                logger.info(f"Loaded cog {cog} successfully.")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}.")
                print(e)

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Log errors raised in event listeners rather than printing them to stderr."""

        logger.exception(f"Unhandled exception in {event}.", exc_info=True)


if __name__ == "__main__":
    bot = Bot(
        command_prefix=commands.when_mentioned_or("!"),
        max_messages=10000,
        allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False),
        help_command=commands.MinimalHelpCommand()
        )

    @bot.command(name="restart")
    @has_any_role(*config.MOD_ROLES)
    async def restart(ctx: commands.Context):
        await ctx.channel.send("Restarting hub bot...")
        logger.info("Shutting down hub bot")
        await bot.logout()

    cogs = []

    bot.load_extensions(cogs)
    bot.run(config.TOKEN)
