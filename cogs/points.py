"""
Created by Epic at 7/2/20
"""
import logging
from discord.ext import commands, tasks
import config
import discord
from models import User, Repository, Commit
import re


class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("hub_bot.cogs.points")
        self.github_account_verification_queue = []
        self.github_repository_verification_queue = []
        self.github_regex = re.compile("(https://github.com/)(.*/.*)")
        self.utils = self.bot.get_cog("Utils")

        self.summary_header = [
            "Hello {user}! Our sauce scanning bots found {total_commits} commits from you and added them to the queue",
            "Commits that was found:"
        ]

        self.summary_format = "{commit_id}: `{commit_message}` ({commit_hash})"

        # Loops
        self.commit_scan_loop.start()

    @commands.command()
    async def start(self, ctx: commands.Context, github: str):
        if len(github) > 100:
            return await ctx.send("Invalid github username")
        if ctx.author.id in self.github_account_verification_queue:
            return await ctx.send("You are already in the queue!")
        if self.bot.db_session.query(User).get(ctx.author.id) is not None:
            return await ctx.send("You already have a github connected!")
        self.github_account_verification_queue.append(ctx.author.id)
        await ctx.send(
            f"You have been put in queue for verification! I will dm you the result, make sure you have your DMs open!")
        embed = discord.Embed(title="Verify GitHub account",
                              description=f"User: {ctx.author.mention}\nGitHub username: {github}", color=0x00FFFF
                              )
        github = github.lower()
        mod_result = await self.utils.mod_poll(embed)
        self.github_account_verification_queue.remove(ctx.message.author.id)
        if mod_result:
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

    @commands.command(name="addrepo")
    async def add_repository(self, ctx, github_link: str):
        github_link = github_link.replace(".git", "").lower()
        github_search = self.github_regex.search(github_link)
        if github_search is None or len(github_link) > 50:
            return await ctx.send("This is not a valid github repository url!")
        github_parsed = github_search.group(2)
        if github_parsed in self.github_repository_verification_queue:
            return await ctx.send("This repository is already in the queue!")
        if self.bot.db_session.query(Repository).get(github_parsed) is not None:
            return await ctx.send("This repository has already been added!")
        if self.bot.db_session.query(User).get(ctx.author.id) is None:
            return await ctx.send("You need to start first! Use `!start <github username>` to start!")

        response = await self.bot.http_session.get(github_link)
        if response.status != 200:
            return await ctx.send("This repository does not exist!")

        embed = discord.Embed(title="New repository",
                              description=f"**Url**: {github_link}\n**Extracted**: {github_parsed}", color=0x55CC33)
        await ctx.send("Your repository has been put in queue for verification!")
        self.github_repository_verification_queue.append(github_link)
        mod_result = await self.utils.mod_poll(embed)
        self.github_repository_verification_queue.remove(github_link)
        if mod_result:
            self.bot.db_session.add(Repository(repository=github_parsed, submitter_id=ctx.author.id))
            self.bot.db_session.commit()

            try:
                await ctx.author.send(f"The repository you submitted (`{github_parsed}`) got accepted!")
            except discord.Forbidden:
                pass
        else:
            try:
                await ctx.author.send(f"The repository you submitted (`{github_parsed}`) got denied!")
            except discord.Forbidden:
                pass

    @commands.command()
    async def points(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        points = self.bot.db_session.query(Commit).filter(Commit.user_id == user.id).count()
        await ctx.send(f"You have {points} points!")

    @tasks.loop(minutes=10)
    async def commit_scan_loop(self):
        leaderboard_cog = self.bot.get_cog("Leaderboard")
        await leaderboard_cog.create_leaderboard()
        repositories = self.bot.db_session.query(Repository).all()
        user_cache = {}
        summaries = {}

        for repository in repositories:
            repository_user, repository_repo = repository.repository.split("/")
            raw_commits = await self.utils.get_commits(repository_user, repository_repo)
            commits = self.utils.parse_commits(raw_commits)

            for commit in commits:
                commit["author"] = commit["author"].lower()
                if commit["author"] not in user_cache.keys():
                    user = self.bot.db_session.query(User).filter(
                        User.github_username == commit["author"]).first()
                    if user is None:
                        continue
                    user_cache[commit["author"]] = user
                user = user_cache[commit["author"]]
                old_commit = self.bot.db_session.query(Commit).filter(Commit.commit_hash == commit["hash"]).first()
                if old_commit is not None:
                    continue
                database_commit = Commit(commit_hash=commit["hash"], user_id=user.id)
                self.bot.db_session.add(database_commit)

                old_summary = summaries.get(user.id, [])
                old_summary.append(commit)
                summaries[user.id] = old_summary
        self.bot.db_session.commit()

        for user_id, commits in summaries.items():
            user = await self.bot.fetch_user(user_id)
            if user is None:
                continue
            summary_pages = self.create_summary(user, commits)
            self.logger.debug(f"Sending a dm to {user}!")
            for page in summary_pages:
                await user.send(page)
        await leaderboard_cog.post_leaderboard()

    def create_summary(self, user: discord.User, commits):
        paginator = commands.Paginator(prefix="", suffix="")

        for line in self.summary_header:
            paginator.add_line(line.format(user=user.name, total_commits=len(commits)))

        for commit_id, commit in enumerate(commits):
            paginator.add_line(
                self.summary_format.format(commit_id=commit_id + 1, commit_message=commit["message"].split("\n")[0],
                                           commit_hash=commit["hash"]))

        return paginator.pages


def setup(bot):
    bot.add_cog(Points(bot))
