import discord
from discord.ext import commands

class Log(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member) -> None:
        """
        The code in this event is executed every time a member joins the guild.

        :param member: The member who joined the guild.
        """
        
        try:
            await member.add_roles(
                member.guild.get_role(int(self.bot.config['roles']['verification']['unverified'])),
                member.guild.get_role(int(self.bot.config['roles']['verification']['basic_category']))
            )
        except:
            pass  

        created = member.created_at
        now = discord.utils.utcnow()

        delta = now - created
        total_days = delta.days

        # Initialize years, months, and days
        years = 0
        months = 0
        days = 0

        # Calculate the number of years
        if total_days >= 365:
            years = total_days // 365
            total_days %= 365

        # Calculate the number of months
        if total_days >= 30:
            months = total_days // 30
            total_days %= 30

        # Remaining days
        days = total_days

        # Format the difference as a string
        formatted_parts = []
        if years > 0:
            formatted_parts.append(f"{years} years")
        if months > 0:
            formatted_parts.append(f"{months} months")
        formatted_parts.append(f"{days} days")

        formatted_string = ", ".join(formatted_parts)

        embed = discord.Embed(
            description=f"{member.mention} {member.name}",
            color=discord.Color.green()
        )
        embed.set_author(
            name="Member Joined",
            icon_url=member.display_avatar.url
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="Account Age",
            value=formatted_string 
        )

        jlbu_channel = self.bot.config['channels']['logs_jlbu']
        
        try:
            jlbu_channel = member.guild.get_channel(int(jlbu_channel))
        except:
            pass

        await jlbu_channel.send(embed=embed)
    
    @commands.Cog.listener("on_member_remove")
    async def on_member_remove(self, member: discord.Member) -> None:
        embed = discord.Embed(
            description=f"{member.mention} {member.name}",
            color=discord.Color.red()
        )
        embed.set_author(
            name="Member Left",
            icon_url=member.display_avatar.url
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        jlbu_channel = self.bot.config['channels']['logs_jlbu']
        
        try:
            jlbu_channel = member.guild.get_channel(int(jlbu_channel))
        except:
            pass

        await jlbu_channel.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Log(bot))