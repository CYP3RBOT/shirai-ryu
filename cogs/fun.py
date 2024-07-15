import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


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

class RockPaperScissors(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label="Scissors", description="You choose scissors.", emoji="✂"
            ),
            discord.SelectOption(
                label="Rock", description="You choose rock.", emoji="🪨"
            ),
            discord.SelectOption(
                label="Paper", description="You choose paper.", emoji="🧻"
            ),
        ]
        super().__init__(
            placeholder="Choose...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        choices = {
            "rock": 0,
            "paper": 1,
            "scissors": 2,
        }
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]

        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]

        result_embed = discord.Embed(color=discord.Color.blue())
        result_embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.display_avatar.url
        )

        winner = (3 + user_choice_index - bot_choice_index) % 3
        if winner == 0:
            result_embed.description = f"**That's a draw!**\nYou've chosen {user_choice} and I've chosen {bot_choice}."
            result_embed.colour = discord.Color.orange()
        elif winner == 1:
            result_embed.description = f"**You won!**\nYou've chosen {user_choice} and I've chosen {bot_choice}."
            result_embed.colour = discord.Color.green()
        else:
            result_embed.description = f"**You lost!**\nYou've chosen {user_choice} and I've chosen {bot_choice}."
            result_embed.colour = discord.Color.red()

        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None
        )

class RockPaperScissorsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.add_item(RockPaperScissors())

class Fun(commands.Cog, name="fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="randomfact", description="Get a random fact.")
    async def randomfact(self, context: Context) -> None:
        """
        Get a random fact.

        :param context: The hybrid command context.
        """
        # This will prevent your bot from stopping everything when doing a web request - see: https://discordpy.readthedocs.io/en/stable/faq.html#how-do-i-make-a-web-request
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    embed = discord.Embed(description=data["text"], color=0xD75BF4)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=discord.Color.blue(),
                    )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="coinflip", description="Make a coin flip, but give your bet before."
    )
    async def coinflip(self, context: Context) -> None:
        """
        Make a coin flip, but give your bet before.

        :param context: The hybrid command context.
        """
        buttons = Choice()
        embed = discord.Embed(description="What is your bet?", color=discord.Color.blue())
        message = await context.send(embed=embed, view=buttons)
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

    @commands.hybrid_command(
        name="rps", description="Play the rock paper scissors game against the bot."
    )
    async def rock_paper_scissors(self, context: Context) -> None:
        """
        Play the rock paper scissors game against the bot.

        :param context: The hybrid command context.
        """
        view = RockPaperScissorsView()
        await context.send("Please make your choice", view=view)

    @app_commands.command(
        name="giveaway",
        description="Select a winner from a giveaway poll"
    )
    @app_commands.describe(message="The message link with the poll")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, message: str):
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