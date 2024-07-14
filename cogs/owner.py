import discord
import math
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils import roblox

class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        """
        Synchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global` or `guild`.
        """

        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=discord.Color.blue(),
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=discord.Color.blue(),
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=discord.Color.red()
        )
        await context.send(embed=embed)

    @commands.command(
        name="unsync",
        description="Unsynchonizes the slash commands.",
    )
    @app_commands.describe(
        scope="The scope of the sync. Can be `global`, `current_guild` or `guild`"
    )
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        """
        Unsynchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global`, `current_guild` or `guild`.
        """

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally unsynchronized.",
                color=discord.Color.blue(),
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been unsynchronized in this guild.",
                color=discord.Color.blue(),
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=discord.Color.red()
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @commands.is_owner()
    async def load(self, context: Context, cog: str) -> None:
        """
        The bot will load the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog.lower()}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog.capitalize()}` cog.", color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully loaded the `{cog.capitalize()}` cog.", color=discord.Color.blue()
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @commands.is_owner()
    async def unload(self, context: Context, cog: str) -> None:
        """
        The bot will unload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to unload.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog.lower()}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog.capitalize()}` cog.", color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully unloaded the `{cog.capitalize()}` cog.", color=discord.Color.blue()
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:
        """
        The bot will reload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to reload.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog.lower()}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog.capitalize()}` cog.", color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully reloaded the `{cog.capitalize()}` cog.", color=discord.Color.blue()
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        """
        Shuts down the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=discord.Color.blue())
        await context.send(embed=embed)
        await self.bot.close()

    @commands.hybrid_command(
        name="embed",
        description="The bot will say anything you want, but within embeds.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @commands.is_owner()
    async def embed(self, context: Context, *, message: str) -> None:
        """
        The bot will say anything you want, but using embeds.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        """
        embed = discord.Embed(description=message, color=discord.Color.blue())
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="link",
        description="Link a ROBLOX account to a Discord account.",
    )
    @app_commands.describe(discord_user="The Discord user to bind")
    @app_commands.describe(roblox_user="The ROBLOX user to bind")
    @commands.has_permissions(administrator=True)
    async def link(self, context: Context, discord_user: discord.User, roblox_user: str) -> None:
        """
        Link a ROBLOX account to a Discord account.

        :param context: The hybrid command context.
        :param discord_user: The Discord user to bind.
        :param roblox_user: The ROBLOX user to bind.
        """

        if discord_user.bot:
            embed = discord.Embed(
                description="You cannot link a bot account.", color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        
        user_object = await roblox.get_user(roblox_user)

        if user_object is None:
            embed = discord.Embed(
                description=f"Roblox user \"{roblox_user}\" not found.", 
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        
        user_name = user_object["username"]
        user_id = user_object["id"]
        
        await self.bot.database.create_verification(str(discord_user.id), str(user_id))

        embed = discord.Embed(
            description=f"Successfully linked {discord_user.mention} with {user_name} ({user_id}).",
            color=discord.Color.blue(),
        )

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="links",
        description="View a user's linked accounts.",
    )
    @app_commands.describe(platform="The platform for the user queried")
    @app_commands.describe(user="The user to view the linked accounts for")
    @commands.has_permissions(administrator=True)
    async def links(self, context: Context, platform: str, user: str) -> None:
        """
        View a user's linked accounts.

        :param context: The hybrid command context.
        :param platform: The platform for the user queried.
        :param user: The user to view the linked accounts for.
        """
        
        if platform.lower() == "discord":
            user = user.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            try:
                user = await self.bot.fetch_user(user)
            except:
                embed = discord.Embed(
                    description=f"User \"{user}\" not found.", 
                    color=discord.Color.red()
                )
                await context.send(embed=embed)
                return
            
            accounts = await self.bot.database.get_verification_by_discord_id(str(user.id))

            if not accounts:
                embed = discord.Embed(
                    description=f"User \"{user}\" has no links.", 
                    color=discord.Color.red()
                )
                await context.send(embed=embed)
                return
                
            embed = discord.Embed(
                description=f"Linked ROBLOX accounts for {user}:\n\n",
                color=discord.Color.blue(),
            )

            user_ids = []
            for account in accounts:
                user_ids.append(int(account["roblox_id"]))

            users = await roblox.get_users_by_ids(user_ids)

            for i, u in enumerate(users["data"]):
                embed.description += f"- [{u['name']}](https://www.roblox.com/users/{u['id']}/profile) ({u['id']}) - <t:{math.floor(accounts[i]['verified_at'].timestamp())}:R>\n"

            await context.send(embed=embed)
            return
        elif platform.lower() == "roblox":
            user_object = await roblox.get_user(user)

            if user_object is None:
                embed = discord.Embed(
                    description=f"User \"{user}\" not found.", 
                    color=discord.Color.red()
                )
                await context.send(embed=embed)
                return
            
            user_name = user_object["username"]
            user_id = user_object["id"]

            links = await self.bot.database.get_verification_by_roblox_id(str(user_id))

            if not links:
                embed = discord.Embed(
                    description=f"User \"{user_name}\" has no links.", 
                    color=discord.Color.red()
                )
                await context.send(embed=embed)
                return
                
            embed = discord.Embed(
                description=f"Linked Discord accounts for {user_name}:\n\n",
                color=discord.Color.blue(),
            )

            for link in links:
                embed.description += f"- <@{link['discord_id']}> - <t:{math.floor(link["verified_at"].timestamp())}:R>\n"

            await context.send(embed=embed)
            return
        
        else:
            embed = discord.Embed(
                description="The platform must be `discord` or `roblox`.", color=discord.Color.red()
            )
            await context.send(embed=embed)
    
    @commands.hybrid_command(
        name="unlink",
        description="Unlink a ROBLOX account from its Discord account.",
    )
    @app_commands.describe(discord_user="The Discord user to unlink")
    @app_commands.describe(roblox_user="The ROBLOX user to unlink")
    @commands.has_permissions(administrator=True)
    async def unlink(self, context: Context, discord_user: discord.User, roblox_user: str) -> None:
        """
        Unlink a ROBLOX account to a Discord account.

        :param context: The hybrid command context.
        :param discord_user: The Discord user to unlink.
        :param roblox_user: The ROBLOX user to unlink.
        """

        user_object = await roblox.get_user(roblox_user)

        if user_object is None:
            embed = discord.Embed(
                description=f"Roblox user \"{roblox_user}\" not found.", 
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        
        user_name = user_object["username"]
        user_id = user_object["id"]
        
        await self.bot.database.delete_verification(str(discord_user.id), str(user_id))

        embed = discord.Embed(
            description=f"Successfully unlinked {discord_user.mention} with {user_name} ({user_id}).",
            color=discord.Color.blue(),
        )

        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))