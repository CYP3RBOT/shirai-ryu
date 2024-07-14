import discord
from discord import app_commands
from discord.ext import commands
from utils import roblox
import math

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
            return
        
        ranks = self.bot.config['ranks']
        rank_roles = [self.bot.config["roles"]["verification"]["outsider"]]

        for member_role in member.roles:
            for rank_obj in ranks:
                if str(member_role.id) == rank_obj['discord_role']:
                    rank_roles.append(member_role)    

        await member.remove_roles(*rank_roles)        
        await member.add_roles(rank, self.bot.config["roles"]["verification"]["member"], self.bot.config["roles"]["verification"]["lr_category"])

        embed.title = "Rank Request - Accepted"
        embed.add_field(name="Previous Rank", value=f"<@&{rank_roles[-1].id}>")
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

class Rank(commands.Cog, name="rank"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="rank-request",
        description="Request a new rank"
    )
    @app_commands.describe(rank="The rank to request", proof="The proof of points required for requested rank")
    @app_commands.guild_only()
    async def rank_request(self, interaction: discord.Interaction, rank: discord.Role, proof: discord.Attachment) -> None:
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

        rank_roles = []

        for member_role in member.roles:
            for rank_obj in ranks:
                if str(member_role.id) == rank_obj['discord_role']:
                    rank_roles.append(member_role)
        
        if len(rank_roles) > 0:
            highest_role = rank_roles[-1]

            if highest_role.position > rank.position:
                embed = discord.Embed(
                    description=f"You cannot request a rank lower than yours.",
                    color=discord.Color.red()
                )

                await interaction.followup.send(embed=embed)
                return
            
            if rank in rank_roles:
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

        embed.add_field(name="Rank Requesting", value=f"<@&{rank.id}> | {is_rank_role[0]['points']} points required")

        await rank_requests_channel.send(embed=embed, view=RankRequest(self.bot))

        embed = discord.Embed(
            description="Successfully sent rank request.",
            color=discord.Color.green()
        )

        await interaction.followup.send(embed=embed)




async def setup(bot) -> None:
    await bot.add_cog(Rank(bot))