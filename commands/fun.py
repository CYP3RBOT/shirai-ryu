import random

import requests
import discord
from discord import app_commands
from discord.ext import commands
from discord import Interaction


class Choice(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.value = None

    @discord.ui.button(label="Heads", style=discord.ButtonStyle.blurple)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.value = "heads"
        self.stop()

    @discord.ui.button(label="Tails", style=discord.ButtonStyle.blurple)
    async def cancel(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.value = "tails"
        self.stop()

class Fun(commands.Cog, name="fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="coinflip", description="Make a coin flip, but give your bet before."
    )
    async def coinflip(self, interaction: Interaction) -> None:
        """
        Make a coin flip, but give your bet before.
        """

        buttons = Choice()
        embed = discord.Embed(description="What is your bet?", color=discord.Color.blue())
        message = await interaction.response.send_message(embed=embed, view=buttons)
        await buttons.wait()  # We wait for the user to click a button.
        result = random.choice(["heads", "tails"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"Correct! You guessed `{buttons.value}` and I flipped the coin to `{result}`.",
                color=discord.Color.blue(),
            )
        else:
            embed = discord.Embed(
                description=f"Woops! You guessed `{buttons.value}` and I flipped the coin to `{result}`, better luck next time!",
                color=discord.Color.blue(),
            )
        await message.edit(embed=embed, view=None, content=None)

    
    @app_commands.command(
        name="8ball",
        description="Ask any question to the bot.",
    )
    @app_commands.describe(question="The question you want to ask.")
    async def eight_ball(self, interaction: Interaction, *, question: str) -> None:
        answers = [
            "It is certain.",
            "It is decidedly so.",
            "You may rely on it.",
            "Without a doubt.",
            "Yes - definitely.",
            "As I see, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again later.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        embed = discord.Embed(
            title="**My Answer:**",
            description=f"{random.choice(answers)}",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"The question was: {question}")
        await interaction.response.send_message(embed=embed)


    @app_commands.command(
        name="giveaway",
        description="Select a winner from a giveaway poll"
    )
    @app_commands.describe(message="The message link with the poll")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, message: str):
        """
        Select a winner from a giveaway via a poll
        """
        
        if not message.startswith("https://discord.com/channels/"):
            embed = discord.Embed(
                description="Not a valid message link.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
        
        guild_id = message.split("discord.com/channels/")[1].split("/")[0]
        channel_id = message.split(str(guild_id) + "/")[1].split("/")[0]
        message_id = message.split(str(guild_id) + "/")[1].split("/")[1]

        try:
            channel = interaction.guild.get_channel_or_thread(int(channel_id))
        except:
            embed = discord.Embed(
                description="Channel not found.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
        
        try:
            message_obj = await channel.fetch_message(int(message_id))
        except:
            embed = discord.Embed(
                description="Message not found.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            

        message_poll = message_obj.poll

        if not message_poll:
            embed = discord.Embed(
                description="Poll not found.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)    
        
        poll_duration = message_poll.duration
        poll_question = message_poll.question
        poll_answer = message_poll.answers[0]
        total_votes = message_poll.total_votes

        embed = discord.Embed(
            title="Giveaway",
            description=f"`Title`: {poll_question}\n`Total Votes`: {total_votes}",
            color=discord.Color.blue()
        )

        embed.set_footer(text="Giveaway lasted " + str(poll_duration.seconds) + " seconds.")

        try:
            voters = [voter async for voter in poll_answer.voters()]
        except:
            embed = discord.Embed(
                description="There are no voters.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)

        winner = random.choice(voters)

        embed.add_field(name="Winner", value=f"<@{winner.id}>")

        await interaction.response.send_message(embed=embed)
        
async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))