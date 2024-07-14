import discord
import math
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils import roblox

class Tracker(commands.Cog, name="tracker"):
    def __init__(self, bot) -> None:
        self.bot = bot

    tracker = app_commands.Group(
        name="tracker",
        description="Manage the tracker."
    )

    @tracker.command(
        name="add",
        description="Add a user to the tracker"
    )
    @app_commands.describe(user="The user to add", reason="The reason for tracking the user")
    @commands.has_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, user: str, reason: str) -> None:
        """
        Add a user to the tracker.

        :param interaction: The app command context.
        :param user: The user to add.
        :param reason: The reason for tracking the user.
        """
        
        moderator_id = str(interaction.user.id)

        roblox_user = await roblox.get_user(user)

        if roblox_user is None:
            embed = discord.Embed(
                description=f"User \"{user}\" not found.",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)      
            return
        
        user_id = str(roblox_user["id"])
        user_name = roblox_user["username"]
        
        success = await self.bot.database.get_tracked_user(user_id)

        if success:
            embed = discord.Embed(
                description=f"User \"{user}\" is already being tracked.",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)      
            return


        success = await self.bot.database.track_user(user_id, moderator_id, reason if reason else "No reason stated.")

        if success:
            embed = discord.Embed(
                description=f"Now tracking [{user_name}]({await roblox.profile(user_id)}).",
                color=discord.Color.green(),
            )      
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description=f"An error occurned when trying to add [{user_name}({await roblox.profile(user_id)}).",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)

    @tracker.command(
        name="remove",
        description="Remove a user from the tracker"
    )
    @app_commands.describe(user="The user to remove")
    @commands.has_permissions(administrator=True)
    async def remove(self, interaction: discord.Interaction, user: str) -> None:
        """
        Remove a user from the tracker.

        :param interaction: The app command context.
        :param user: The user to remove.
        """
        
        roblox_user = await roblox.get_user(user)

        if roblox_user is None:
            embed = discord.Embed(
                description=f"User \"{user}\" not found.",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)      
            return
        
        user_id = str(roblox_user["id"])
        user_name = roblox_user["username"]
        
        success = await self.bot.database.get_tracked_user(user_id)

        if not success:
            embed = discord.Embed(
                description=f"User \"{user}\" isn't being tracked.",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)      
            return


        success = await self.bot.database.untrack_user(user_id)

        if success:
            embed = discord.Embed(
                description=f"Stopped tracking [{user_name}]({await roblox.profile(user_id)}).",
                color=discord.Color.green(),
            )      
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description=f"An error occurned when trying to remove [{user_name}({await roblox.profile(user_id)}).",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)

    @tracker.command(
        name="list",
        description="List all the users in the tracker"
    )
    @commands.has_permissions(administrator=True)
    async def list(self, interaction: discord.Interaction) -> None:
        """
        List all users in the tracker.

        :param interaction: The app command context.
        """

        tracked_users = await self.bot.database.get_tracked_users()

        if len(tracked_users) == 0:
            embed = discord.Embed(
                description="None",
                color=discord.Color.blue()
            )

            await interaction.response.send_message(embed=embed)
            return

        user_ids = []

        for x in tracked_users:
            user_ids.append(int(x['roblox_id']))

        users = await roblox.get_users_by_ids(user_ids) # Only can request 50 at one time
        users = users['data']
        description_string = ""

        for user in users:
            user_obj = list(filter(lambda u: str(user['id']) == u['roblox_id'], tracked_users))
            user_obj = user_obj[0]

            unix_timestamp = math.floor(user_obj['created_at'].timestamp())
            description_string += f"\n- [{user['name']}]({await roblox.profile(user['id'])}) | `{user_obj['reason']}` (<t:{unix_timestamp}:d>)"

        embed = discord.Embed(
            description=description_string,
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed)



async def setup(bot) -> None:
    await bot.add_cog(Tracker(bot))