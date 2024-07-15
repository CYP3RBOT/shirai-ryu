import math
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands, Interaction
from discord.ext import commands

class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    warning = app_commands.Group(
        name="warning",
        description="Manage warnings of a user on a server."
    )

    @app_commands.command(
        name="kick",
        description="Kick a user out of the server.",
    )
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user that should be kicked.",
        reason="The reason why the user should be kicked.",
    )
    async def kick(
        self, interaction: Interaction, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(
            user.id
        )
        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="User has administrator permissions.", color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    description=f"**{member}** was kicked by **{interaction.user}**!",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="Reason:", value=reason)
                await interaction.response.send_message(embed=embed)
                try:
                    await member.send(
                        f"You were kicked by **{interaction.user}** from **{interaction.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.kick(reason=reason)
            except:
                embed = discord.Embed(
                    description="An error occurred while trying to kick the user. Make sure my role is above the role of the user you want to kick.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="ban",
        description="Bans a user from the server.",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user="The user that should be banned.",
        reason="The reason why the user should be banned.",
    )
    async def ban(
        self, interaction: Interaction, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(
            user.id
        )
        try:
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    description="User has administrator permissions.", color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(
                    description=f"**{member}** was banned by **{interaction.user}**!",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="Reason:", value=reason)
                await interaction.response.send_message(embed=embed)
                try:
                    await member.send(
                        f"You were banned by **{interaction.user}** from **{interaction.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.ban(reason=reason)
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user. Make sure my role is above the role of the user you want to ban.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)

    @warning.command(
        name="add",
        description="Adds a warning to a user in the server.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user that should be warned.",
        reason="The reason why the user should be warned.",
    )
    async def warning_add(
        self, interaction: Interaction, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(
            user.id
        )
        total = await self.bot.database.add_warn(
            str(user.id), str(interaction.guild.id), str(interaction.user.id), reason
        )
        embed = discord.Embed(
            description=f"**{member}** was warned by **{interaction.user}**!\nTotal warns for this user: {total}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Reason:", value=reason)
        await interaction.response.send_message(embed=embed)
        try:
            await member.send(
                f"You were warned by **{interaction.user}** in **{interaction.guild.name}**!\nReason: {reason}"
            )
        except:
            # Couldn't send a message in the private messages of the user
            await interaction.response.send_message(
                f"{member.mention}, you were warned by **{interaction.user}**!\nReason: {reason}"
            )

    @warning.command(
        name="remove",
        description="Removes a warning from a user in the server.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user that should get their warning removed.",
        warn_id="The ID of the warning that should be removed.",
    )
    async def warning_remove(
        self, interaction: Interaction, user: discord.User, warn_id: int
    ) -> None:
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(
            user.id
        )
        total = await self.bot.database.remove_warn(warn_id, str(user.id), str(interaction.guild.id))
        embed = discord.Embed(
            description=f"I've removed the warning **#{warn_id}** from **{member}**!\nTotal warns for this user: {total}",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    @warning.command(
        name="list",
        description="Shows the warnings of a user in the server.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.describe(user="The user you want to get the warnings of.")
    async def warning_list(self, interaction: Interaction, user: discord.User) -> None:
        warnings_list = await self.bot.database.get_warnings(str(user.id), str(interaction.guild.id))
        embed = discord.Embed(title=f"Warnings of {user}", color=discord.Color.blue())
        description = ""
        if len(warnings_list) == 0:
            description = "This user has no warnings."
        else:
            for warning in warnings_list:
                unix_timestamp = math.floor(warning['created_at'].timestamp())

                description += (
                    f"• Warned by <@{warning['moderator_id']}>: **{warning['reason']}** "
                    f"(<t:{unix_timestamp}>) - Warn ID #{warning['id']}\n"
                )
        embed.description = description
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="purge",
        description="Delete a number of messages.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, interaction: Interaction, amount: int) -> None:
        await interaction.response.send_message(
            "Deleting messages..."
        )  # Bit of a hacky way to make sure the bot responds to the interaction and doens't get a "Unknown Interaction" response
        purged_messages = await interaction.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{interaction.user}** cleared **{len(purged_messages)-1}** messages!",
            color=discord.Color.blue(),
        )
        await interaction.channel.send(embed=embed)

    @app_commands.command(
        name="hackban",
        description="Bans a user without the user having to be in the server.",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user_id="The user ID that should be banned.",
        reason="The reason why the user should be banned.",
    )
    async def hackban(
        self, interaction: Interaction, user_id: str, *, reason: str = "Not specified"
    ) -> None:
        try:
            await self.bot.http.ban(user_id, interaction.guild.id, reason=reason)
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(
                int(user_id)
            )
            embed = discord.Embed(
                description=f"**{user}** (ID: {user_id}) was banned by **{interaction.user}**!",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Reason:", value=reason)
            await interaction.response.send_message(embed=embed)
        except Exception:
            embed = discord.Embed(
                description="An error occurred while trying to ban the user. Make sure ID is an existing ID that belongs to a user.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="archive",
        description="Archives in a text file the last messages with a chosen limit of messages.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        limit="The limit of messages that should be archived.",
    )
    async def archive(self, interaction: Interaction, limit: int = 10) -> None:
        log_file = f"{interaction.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Archived messages from: #{interaction.channel} ({interaction.channel.id}) in the guild "{interaction.guild}" ({interaction.guild.id}) at {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in interaction.channel.history(
                limit=limit, before=interaction.message
            ):
                attachments = []
                for attachment in message.attachments:
                    attachments.append(attachment.url)
                attachments_text = (
                    f"[Attached File{'s' if len(attachments) >= 2 else ''}: {', '.join(attachments)}]"
                    if len(attachments) >= 1
                    else ""
                )
                f.write(
                    f"{message.created_at.strftime('%d.%m.%Y %H:%M:%S')} {message.author} {message.id}: {message.clean_content} {attachments_text}\n"
                )
        f = discord.File(log_file)
        await interaction.response.send_message(file=f)
        os.remove(log_file)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.checks.has_role(1261605836258803722)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.describe(
        member="The member to mute",
        duration="The duration of the mute",
        reason="The reason for the mute"
    )
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):
        # Check if the member trying to mute has a higher role than the target member
        if member.top_role >= interaction.user.top_role:
            embed = discord.Embed(
                description=f"Cannot mute {member.mention} because they have a higher role.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return

        # Check if the bot has a lower role than the target member
        if interaction.guild.me.top_role <= member.top_role:
            embed = discord.Embed(
                description=f"Cannot mute {member.mention} because they have a higher role than me.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return

        # Parse the duration
        time_unit = duration[-1]
        if not duration[:-1].isdigit():
            embed = discord.Embed(
                description="Invalid time unit. Use 'm' for minutes, 'h' for hours, or 'd' for days.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return

        time_value = int(duration[:-1])

        if time_unit == 'm':
            delta = timedelta(minutes=time_value)
        elif time_unit == 'h':
            delta = timedelta(hours=time_value)
        elif time_unit == 'd':
            delta = timedelta(days=time_value)
        else:
            embed = discord.Embed(
                description="Invalid time unit. Use 'm' for minutes, 'h' for hours, or 'd' for days.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return

        max_duration = timedelta(days=28)
        if delta > max_duration:
            embed = discord.Embed(
                description="Cannot mute someone for more than 28 days.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return

        # Timeout the member
        try:
            embed = discord.Embed(
                description=f"Muted {member.mention} for {duration}.",
                color=discord.Color.blue()
            )
            
            await member.edit(timed_out_until=(discord.utils.utcnow() + delta), reason=reason)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            print(e)
            embed = discord.Embed(
                description=f"An error occurred while trying to mute {member.mention}.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return      

async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))