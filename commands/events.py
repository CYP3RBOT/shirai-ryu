import discord

from discord import app_commands, Interaction
from discord.ext import commands

class Events(commands.Cog, name="events"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="log",
        description="Log an event"
    )
    @app_commands.guild_only()
    @app_commands.describe(message_link="The event to log")
    async def log(self, interaction: Interaction, message_link: str):
        await interaction.response.defer()

        permission_role = self.bot.config['roles']['officer_perms']

        if permission_role not in [str(role.id) for role in interaction.user.roles]:
            embed = discord.Embed(
                description="You do not have permission to use this command",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            # Extracting channel_id and message_id from the message_link
            split_link = message_link.split("/")
            channel_id = int(split_link[5])
            message_id = int(split_link[-1])

            # Fetching the channel and message
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                raise ValueError("Channel not found")

            message = await channel.fetch_message(message_id)

            members = message.mentions

            if len(members) == 0:
                embed = discord.Embed(
                    description="No members mentioned in the message",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            success = await self.bot.database.batch_log_event([str(member.id) for member in members])
            
            if success:
                embed = discord.Embed(
                    description="Logged the event for these members:\n\n" + ", ".join([f"<@{member.id}>" for member in members]),
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    description="Could not log the event",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                description=f"Invalid message link or could not fetch the message",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="events",
        description="Get the number of events logged for a user"
    )
    @app_commands.describe(user="The user to get the events for")
    async def events(self, interaction: Interaction, user: discord.User):
        await interaction.response.defer()

        events = await self.bot.database.get_events(str(user.id))

        embed = discord.Embed(
            description=f"<@{user.id}> has attended `0` events",
            color=discord.Color.blue()
        )

        if events:
            embed.description=str(f"<@{user.id}> has attended `{str(events['events'])}` events")

        await interaction.followup.send(embed=embed)
 
    @app_commands.command(
        name="leaderboard",
        description="Get the leaderboard of events logged"
    )
    async def leaderboard(self, interaction: Interaction):
        await interaction.response.defer()

        leaderboard = await self.bot.database.get_leaderboard()

        if leaderboard:
            leaderboard = leaderboard[:10]  # Select only the top ten players
            description = "\n".join([f"{index+1}. <@{user['discord_id']}> - {user['events']} events" for index, user in enumerate(leaderboard)])
        else:
            description = "No events logged yet"

        embed = discord.Embed(
            title="Leaderboard",
            description=description,
            color=discord.Color.blue()
        )

        await interaction.followup.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Events(bot))