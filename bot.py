import json
import logging
import os
import platform
import sys

import asyncpg
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from dotenv import load_dotenv

from database import DatabaseManager
from utils import roblox

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True # Allow prefix commands
intents.members = True 

# Setup both of the loggers
class LoggingFormatter(logging.Formatter):
    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
# File handler
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

# Add the handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(config["prefix"]),
            intents=intents,
            help_command=None,
            
        )
        """
        This creates custom bot variables so that we can access these variables in cogs more easily.

        For example, The config is available using the following code:
        - self.config # In this class
        - bot.config # In this file
        - self.bot.config # In cogs
        """
        self.logger = logger
        self.config = config
        self.database = None
        self.db_pool = None

    async def init_db(self) -> None:
        self.db_pool = await asyncpg.create_pool(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT')
        )

        # Read the SQL file
        with open('./database/schema.sql', 'r') as f:
            sql = f.read()

        # Execute the SQL commands
        async with self.db_pool.acquire() as conn:
            await conn.execute(sql)

        self.database = DatabaseManager(connection=self.db_pool)

    async def close(self):
        await self.db_pool.close()
        await super().close()


    async def load_cogs(self) -> None:
        """
        The code in this function is executed whenever the bot will start.
        """
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load extension {extension}\n{exception}"
                    )

    @tasks.loop(minutes=1.0)
    async def status_task(self) -> None:
        """
        Setup the game status task of the bot.
        """
        
        activity = discord.CustomActivity(
            name = "Ultio nostra erit!",
        )

        await self.change_presence(activity=activity)

    @tasks.loop(minutes=1440.0)
    async def call_ceo_a_dirty_jew_task(self) -> None:
        """
        Call ceo a dirty jew once a day.
        """

        channel = await bot.fetch_channel(self.config['channels']['general'])
        await channel.send("<@1134427767283396639> You are dirty jew.")

    @tasks.loop(minutes=1.0)
    async def check_tracker(self) -> None:
        """
        Check if any tracked users are online/offline and post it.
        """

        tracked_users = await bot.database.get_tracked_users()

        if len(tracked_users) == 0:
            return

        user_ids = []

        for x in tracked_users:
            user_ids.append(int(x['roblox_id']))

        user_presences = await roblox.get_user_presences_by_ids(user_ids)
        user_names = await roblox.get_users_by_ids(user_ids)

        try:
            user_names = user_names['data']
        except:
            logger.error("Unknown error occured when fetching users by ids.")
            return # Probably a 429 error
        
        try:
            user_presences = user_presences['userPresences']
        except:
            logger.info("Check tracker hit a 429 error.")
            return 
        
        tracker_post_channel = await bot.fetch_channel(self.config['channels']['tracker_post'])

        if not tracker_post_channel:
            logger.critical("Cannot find tracker post channel.")
            return


        for i, presence in enumerate(user_presences):
            embed = None

            game_id = presence['gameId']
            place_id = presence['placeId']
            last_location = presence['lastLocation']
            
            roblox_id = user_names[i]['id']
            user_name = user_names[i]['name']
            is_posted = tracked_users[i]['posted']

            if presence['userPresenceType'] == 2: # user is playing a game
                if not place_id and not is_posted: # user has joins off and wasn't posted
                    embed = discord.Embed(
                        description=f"[{user_name}]({await roblox.profile(roblox_id)}) is playing a game. Their joins are off.",
                        color=discord.Color.green(),
                    )

                    await bot.database.modify_tracked_user(str(roblox_id), True)
                elif place_id and not is_posted: # user has joins on and wasn't posted
                    if place_id == 4238077359:
                        embed = discord.Embed(
                            description=f"[{user_name}]({await roblox.profile(roblox_id)}) is playing Coruscant.",
                            color=discord.Color.green()
                        )

                        await bot.database.modify_tracked_user(str(roblox_id), True)
                elif place_id and is_posted:
                    if place_id != 4238077359:
                        embed = discord.Embed(
                            description=f"[{user_name}]({await roblox.profile(roblox_id)}) has left Coruscant.",
                            color=discord.Color.red()
                        )

                    await bot.database.modify_tracked_user(str(roblox_id), False)
            else:
                if is_posted:
                    embed = discord.Embed(
                        description=f"[{user_name}]({await roblox.profile(roblox_id)}) has left {'Coruscant' if place_id else 'their game'}.",
                        color=discord.Color.red()
                    )

                    await bot.database.modify_tracked_user(str(roblox_id), False)

            if embed:
                embed.set_thumbnail(url=(await roblox.get_user_avatar(roblox_id)))
                await tracker_post_channel.send(embed=embed)
                
    @status_task.before_loop
    async def before_status_task(self) -> None:
        """
        Before starting the status changing task, we make sure the bot is ready
        """
        await self.wait_until_ready()

    @call_ceo_a_dirty_jew_task.after_loop
    async def after_call_ceo_a_dirty_jew_task(self) -> None:
        await self.wait_until_ready()

    @check_tracker.after_loop
    async def after_check_tracker(self) -> None:
        await self.wait_until_ready()


    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {discord.__version__}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})"
        )
        self.logger.info("-------------------")
        await self.init_db()
        await self.load_cogs()
        self.status_task.start()
        self.check_tracker.start()
        self.call_ceo_a_dirty_jew_task.start()

    async def on_message(self, message: discord.Message) -> None:
        """
        The code in this event is executed every time someone sends a message, with or without the prefix

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_completion(self, context: Context) -> None:
        """
        The code in this event is executed every time a normal command has been *successfully* executed.

        :param context: The context of the command that has been executed.
        """
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if context.guild is not None:
            self.logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def on_command_error(self, context: Context, error) -> None:
        """
        The code in this event is executed every time a normal valid command catches an error.

        :param context: The context of the normal command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=discord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=discord.Color.red()
            )
            await context.send(embed=embed)
            if context.guild:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="You are missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to execute this command!",
                color=discord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                description="I am missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to fully perform this command!",
                color=discord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=str(error).capitalize(),
                color=discord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.UserNotFound):
            embed = discord.Embed(
                description=str(error).capitalize(), 
                color=discord.Color.red()
            )
            await context.send(embed=embed)
        else:
            raise error
        
bot = DiscordBot()
bot.run(os.getenv("BOT_TOKEN"))