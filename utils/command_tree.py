import discord
from discord import app_commands, Interaction

class BotCommandTree(app_commands.CommandTree):
  async def on_error(self, interaction: Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
      await interaction.response.send_message(f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.", )
    elif isinstance(error, app_commands.MissingRole):
        embed = discord.Embed(
            description="Missing required role to execute this command.", 
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)