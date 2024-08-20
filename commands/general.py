import platform
import discord
import pytube
import math

from discord import app_commands, Interaction
from discord.ext import commands

from utils import roblox

class RankRequest(discord.ui.View):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        embed = interaction.message.embeds[0]
        user_field = embed.fields[1].value
        rank_field = embed.fields[3].value

        user_id = user_field.split(" | <@")[1].split("> | `")[0]
        rank_id = rank_field.split(" |")[0][3:][:-1]
                
        member = interaction.guild.get_member(int(user_id))
        rank = interaction.guild.get_role(int(rank_id))

        if not member or not rank:
            await interaction.message.delete()
            self.bot.logger.info(user_field)
            self.bot.logger.info(rank_field)
            self.bot.logger.info(user_id)
            self.bot.logger.info(rank_id)
            self.bot.logger.info(member)
            self.bot.logger.info(rank)
            self.bot.logger.error("Member or rank not found.")
            return
        
        ranks = self.bot.config['ranks']

        roles_to_add = [] # Roles to add to the user
        roles_to_remove = [] # Roles to remove from the user

        previous_rank = None

        for member_role in member.roles:
            for rank_obj in ranks:
                if str(member_role.id) == rank_obj['discord_role']: # If the member has a rank that is in the ranks list
                    roles_to_remove.append(member_role)    
                if str(member_role.id) == self.bot.config["roles"]["verification"]["outsider"]: # If the member is an outsider
                    roles_to_remove.append(member_role)

        if len(roles_to_remove) > 0:
            previous_rank = roles_to_remove[-1]

        roles_to_add.append(rank)
        roles_to_add.append(interaction.guild.get_role(int(self.bot.config["roles"]["verification"]["member"])))
        
        rank_obj = list(filter(lambda role: str(rank.id) == role['discord_role'], ranks))[0]
        
        if rank_obj['type'] == "lr":
            roles_to_add.append(interaction.guild.get_role(int(self.bot.config["roles"]["verification"]["lr_category"])))
            roles_to_remove.append(interaction.guild.get_role(int(self.bot.config["roles"]["verification"]["mr_category"])))
        else:
            roles_to_remove.append(interaction.guild.get_role(int(self.bot.config["roles"]["verification"]["lr_category"])))
            roles_to_add.append(interaction.guild.get_role(int(self.bot.config["roles"]["verification"]["mr_category"])))


        await member.remove_roles(*roles_to_remove)
        await member.add_roles(*roles_to_add)

        embed.title = "Rank Request - Accepted"
        if previous_rank:
            embed.add_field(name="Previous Rank", value=f"<@&{previous_rank.id}>")
        embed.add_field(name="Status", value=f"Accepted by: {interaction.user} | <@{interaction.user.id}> | `{interaction.user.id}`", inline=False)
        embed.color = discord.Color.green()

        await interaction.message.edit(embed=embed, view=None)
        
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        embed = interaction.message.embeds[0]

        embed.title = "Rank Request - Denied"
        embed.add_field(name="Status", value=f"Denied by: {interaction.user} | <@{interaction.user.id}> | `{interaction.user.id}`", inline=False)
        embed.color = discord.Color.red()

        await interaction.message.edit(embed=embed, view=None)

class General(commands.Cog, name="general"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="say",
        description="The bot will say anything you want",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    async def say(self, interaction: Interaction, *, message: str) -> None:
        await interaction.response.send_message("Saying...", ephemeral=True)
        await interaction.channel.send(message)

    @app_commands.command(
        name="help", description="List all commands the bot has loaded"
    )
    async def help(self, interaction: Interaction) -> None:
        prefix = self.bot.config["prefix"]

        embed = discord.Embed(
            title="Help", description="List of available commands:", color=discord.Color.blue()
        )

        for i in self.bot.cogs:
            if i == "owner" and not (await self.bot.is_owner(interaction.user)):
                continue
            
            cog = self.bot.get_cog(i.lower())

            app_commands = cog.get_app_commands()
            commands = cog.get_commands()

            data = []
            
            for command in commands:
                description = command.description.partition("\n")[0]
                data.append(f"{prefix}{command.name} - {description}")

            for app_command in app_commands:
                description = app_command.description.partition("\n")[0]
                data.append(f"/{app_command.name} - {description}")

            help_text = "\n".join(data)
            
            embed.add_field(
                name=i.capitalize(), value=f"```{help_text}```", inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="botinfo",
        description="Get some useful (or not) information about the bot.",
    )
    async def botinfo(self, interaction: Interaction) -> None:
        owner = await self.bot.fetch_user(759552371285426176)

        embed = discord.Embed(
            description="Made for the server of [Shirari Ryu](https://discord.gg/Cccsj2BXcn)",
            color=discord.Color.blue(),
        )
        embed.set_author(name="Bot Information")
        embed.add_field(name="Owner:", value=f"{owner.name} (<@{owner.id}>)", inline=True)
        embed.add_field(
            name="Python Version:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Prefix:",
            value=f"/ (Slash Commands) or {self.bot.config['prefix']} for normal commands",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="serverinfo",
        description="Get some useful (or not) information about the server.",
    )
    async def serverinfo(self, interaction: Interaction) -> None:
        roles = [role.name for role in interaction.guild.roles]
        num_roles = len(roles)
        if num_roles > 50:
            roles = roles[:50]
            roles.append(f">>>> Displaying [50/{num_roles}] Roles")
        roles = ", ".join(roles)

        embed = discord.Embed(
            title="**Server Name:**", description=f"{interaction.guild}", color=discord.Color.blue()
        )
        if interaction.guild.icon is not None:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.add_field(name="Server ID", value=interaction.guild.id)
        embed.add_field(name="Member Count", value=interaction.guild.member_count)
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(interaction.guild.channels)}"
        )
        embed.add_field(name=f"Roles ({len(interaction.guild.roles)})", value=roles)
        embed.set_footer(text=f"Created at: {interaction.guild.created_at}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="ping",
        description="Check if the bot is alive.",
    )
    async def ping(self, interaction: Interaction) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="download",
        description="Download a youtube video"
    )
    @app_commands.describe(
        link="The youtube video link to download"
    )
    async def download(self, interaction: Interaction, link: str) -> None:
        await interaction.response.defer(thinking=True)

        try:
            yt = pytube.YouTube(link)
        except:
            embed = discord.Embed(
                description="Invalid Youtube link."
            )
            await interaction.followup.send(embed=embed)
            return
        
        video = yt.streams.get_highest_resolution()

        try:
            video.download("/temp", filename="video.mp4")
        except:
            embed = discord.Embed(
                description="Could not download the file.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            description=f"[{yt.title}]({link})"
        )
        await interaction.followup.send(embed=embed, file=discord.File(f"/temp/video.mp4"))

    @app_commands.command(
        name="rank-request",
        description="Request a new rank"
    )
    @app_commands.describe(rank="The rank to request", proof="The proof of points required for requested rank")
    @app_commands.guild_only()
    async def rank_request(self, interaction: Interaction, rank: discord.Role, proof: discord.Attachment) -> None:
        """
        Request a new rank.

        :param rank: The rank to request.
        :param proof: The proof of points required for requested rank.
        """
        await interaction.response.defer()

        verification = await self.bot.database.get_verification_by_discord_id(str(interaction.user.id))

        if not verification:
            embed = discord.Embed(
                description="You must be verified to use this command.",
                color=discord.Color.red()
            )

            await interaction.followup.send(embed=embed)
            return
        
        roblox_id = verification[0]['roblox_id']
        
        ranks = self.bot.config['ranks']

        is_rank_role = list(filter(lambda role: str(rank.id) == role['discord_role'], ranks))

        if len(is_rank_role) == 0:
            embed = discord.Embed(
                description=f"{rank} is not a requestable role.",
                color=discord.Color.red()
            )

            await interaction.followup.send(embed=embed)
            return
        
        member = await interaction.guild.fetch_member(interaction.user.id)

        roles_to_remove = []

        for member_role in member.roles:
            for rank_obj in ranks:
                if str(member_role.id) == rank_obj['discord_role']:
                    roles_to_remove.append(member_role)
        
        if len(roles_to_remove) > 0:
            highest_role = roles_to_remove[-1]

            if highest_role.position > rank.position:
                embed = discord.Embed(
                    description=f"You cannot request a rank lower than yours.",
                    color=discord.Color.red()
                )

                await interaction.followup.send(embed=embed)
                return
            
            if rank in roles_to_remove:
                embed = discord.Embed(
                    description=f"You cannot request a rank you already have.",
                    color=discord.Color.red()
                )

                await interaction.followup.send(embed=embed)
                return
        
        rank_requests_channel_id = self.bot.config['channels']['rank_requests']
        rank_requests_channel = await interaction.guild.fetch_channel(rank_requests_channel_id)

        if not rank_requests_channel:
            embed = discord.Embed(
                description=f"Internal system error occured.",
                color=discord.Color.red()
            )

            await interaction.followup.send(embed=embed)
            raise discord.NotFound()

        user_data = await roblox.get_users_by_ids([int(roblox_id)])
        user_data = user_data['data'][0]
        user_name = user_data['name']

        embed = discord.Embed(
            title="Rank Request - Pending",
            color=discord.Color.blue(),
        )
        embed.set_image(url=(proof.url))

        embed.add_field(name="Roblox User", value=f"[{user_name}]({await roblox.profile(roblox_id)})", inline=False)
        embed.add_field(name="Discord User", value=f"{interaction.user} | <@{interaction.user.id}> | `{interaction.user.id}`", inline=False)
        embed.add_field(name="Joined At", value=f"<t:{math.floor(member.joined_at.timestamp())}:d>", inline=False)

        embed.add_field(name="Rank Requesting", value=f"<@&{rank.id}> | {is_rank_role[0]['requirements']}")

        await rank_requests_channel.send(embed=embed, view=RankRequest(self.bot))

        embed = discord.Embed(
            description="Successfully sent rank request.",
            color=discord.Color.green()
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="member-count",
        description="Get the guild's member count"
    )
    @app_commands.guild_only()
    async def member_count(self, interaction: Interaction):
        member_count = interaction.guild.member_count
        bot_count = sum(i.bot for i in interaction.guild.members)
        real_members = member_count - bot_count

        embed = discord.Embed(
            color=discord.Color.blue(),
        )

        embed.add_field(name="Members", value=str(member_count), inline=True)
        embed.add_field(name="Bots", value=str(bot_count), inline=True)
        embed.add_field(name="Real Members", value=str(real_members), inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(General(bot))