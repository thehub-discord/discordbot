"""
Created by vcokltfre - 2020-07-23
"""

import discord
from discord.ext import commands
from discord.ext.commands import has_any_role
from pathlib import Path
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from aiohttp import ClientSession
import warnings

import logging
import config
import models

logger = logging.getLogger("hub_bot")


class Bot(commands.Bot):
    """A subclassed version of commands.Bot"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.filterwarnings("ignore")
        self.db_engine = sqlalchemy.create_engine(config.DATABASE_URI, echo=False)
        self.db_session: Session = sessionmaker()(bind=self.db_engine)
        self.http_session = ClientSession()
        models.Base.metadata.create_all(self.db_engine)

    def add_cog(self, cog: commands.Cog) -> None:
        """Adds a cog to the bot and logs it."""
        super().add_cog(cog)
        logger.info(f"Cog loaded: {cog.qualified_name}")

    def load_extensions(self, cogs: list):
        """Loads a list of cogs"""
        self.load_extension("jishaku")
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
        allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False),
        help_command=commands.MinimalHelpCommand()
        )

    @bot.command(name="restart")
    @has_any_role(*config.MOD_ROLES)
    async def restart(ctx: commands.Context):
        await ctx.channel.send("Restarting hub bot...")
        logger.info("Shutting down hub bot")
        await bot.logout()

    cogs = ["cogs." + i.name[:-3] for i in Path("cogs/").glob("*.py")]

    bot.load_extensions(cogs)
    bot.run(config.TOKEN)
