import discord
import math
from discord import app_commands, Interaction
from discord.ext import commands

from utils import _discord, roblox

class AccountSelection(discord.ui.Select):
    def __init__(self, bot: commands.Bot, purpose: str, accounts: list, users: list):
        self.bot = bot
        self.purpose = purpose

        options = []

        if not users["data"]:
            return
        
        # Set the options that will be presented inside the dropdown
        for i, user in enumerate(users["data"]):
            options.append(discord.SelectOption(label=f"{user['name']} ({user['id']})", description=f"Verified on {accounts[i]['verified_at'].strftime("%m-%d-%Y")}"))

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose your account..', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        # Use the interaction object to send a response message containing
        # the user's choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.

        user_name = self.values[0].split(" (")[0]
        user_id = self.values[0].split(" (")[1][:-1]
        
        embed = discord.Embed(
            description=f"{'Verified as' if self.purpose == 'Verified' else 'Unverified from'} [{user_name}]({await roblox.profile(user_id)}).",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        if self.purpose == "Unverified":
            await self.bot.database.delete_verification(str(interaction.user.id), user_id)

            guild_member: discord.Member = await interaction.guild.fetch_member(interaction.user.id)
            
            if guild_member:            
                role = discord.utils.get(interaction.guild.roles, id=int(self.bot.config['roles']['verification']['unverified']))

                await guild_member.edit(roles=[role])
        else:
            member = interaction.guild.get_member(interaction.user.id)
            data = await _discord.update_user(self.bot, member, user_id)

            embed = discord.Embed(
                title="Update",
                color=discord.Color.green(),
            )

            roles_added = ""
            roles_removed = ""

            for role in data["roles_added"]:
                roles_added += f"- <@&{role}>\n"
            for role in data["roles_removed"]:
                roles_removed += f"- <@&{role}>\n"

            roles_added = roles_added or "None"
            roles_removed = roles_removed or "None"

            embed.add_field(name="Nickname", value=data['nickname'], inline=False)
            embed.add_field(name="Roles Added", value=roles_added, inline=False)
            embed.add_field(name="Roles Removed", value=roles_removed, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

class DropdownView(discord.ui.View):
    def __init__(self, bot: commands.Bot, purpose: str, accounts: list, users: list):
        super().__init__()
        # Adds the dropdown to our view object.
        self.add_item(AccountSelection(
            bot=bot,
            purpose=purpose,
            accounts=accounts,
            users=users
        ))

class Confirm(discord.ui.View):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: Interaction, button: discord.ui.Button
    ) -> None:
        active_code = await self.bot.database.get_verification_code(str(interaction.user.id))
        
        user_id = active_code[1]
        code = active_code[2]

        user_information = await roblox.get_user_information(str(user_id))

        user_description = user_information['description']

        if code in user_description:
            verification = await self.bot.database.create_verification(str(interaction.user.id), str(user_id))
            deletion = await self.bot.database.delete_verification_code(str(interaction.user.id))

            embed = discord.Embed(
                description="An unexpected error occured when saving user to database!",
                color=discord.Color.red()
            )

            if verification and deletion:
                embed = discord.Embed(
                    description="You have been successfully verified!",
                    color=discord.Color.green()
                )

            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.defer(ephemeral=False, thinking=False)
        else:
            embed = discord.Embed(
                description="Code not found in description.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(
        self, interaction: Interaction, button: discord.ui.Button
    ) -> None:
        self.stop()
        await self.bot.database.delete_verification_code(str(interaction.user.id))
        await interaction.message.delete()

class VerificationModal(discord.ui.Modal, title='Verification'):
    def __init__(self, bot):
        super().__init__()

        self.bot = bot
        self.name = discord.ui.TextInput(label='Name', style=discord.TextStyle.short, placeholder="Enter your ROBLOX username or #[ROBLOX id] here...")
        self.add_item(self.name)

    async def on_submit(self, interaction: Interaction):
        user_input = self.name.value

        roblox_user = await roblox.get_user(user_input)

        if roblox_user is None:
            embed = discord.Embed(
                description=f"User \"{user_input}\" not found.",
                color=discord.Color.red(),
            )      
            await interaction.response.send_message(embed=embed)      
            return
        
        user_id = roblox_user["id"]
        user_name = roblox_user["username"]

        code = await self.bot.database.create_verification_code(str(interaction.user.id), str(user_id))

        embed = discord.Embed(
            description=f"Success! I have sent you a verification code. Please check your DMs.",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)
        
        confirmation_buttons = Confirm(self.bot)

        try:
            embed = discord.Embed(
                description=f"""
                Please place the following code in the \"About Me\" section of your [ROBLOX profile]({await roblox.profile(user_id)}). Select "Confirm" when you are done, or "Cancel" to cancel the verification process. Note, you are verifying as: [{user_name}]({await roblox.profile(user_id)}).
                
                Your verification code is: ```{code}```
                """,
                color=discord.Color.blue(),
            )
            await interaction.user.send(embed=embed, view=confirmation_buttons)
        except discord.Forbidden:
            await interaction.response.send_message("I cannot send you DMs. Please enable DMs from server members.")

class BloxlinkBind(discord.ui.View):
    def __init__(self, bot: commands.Bot, user: discord.User, user_id: str) -> None:
        super().__init__()
        self.bot = bot
        self.user = user
        self.user_id = user_id

        self.error_embed = discord.Embed(
            description="You cannot use this button!",
            color=discord.Color.red()
        )

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user != self.user:
            await interaction.response.send_message(embed=self.error_embed, ephemeral=True)
            return
        
        success = await self.bot.database.create_verification(str(self.user.id), self.user_id)
        
        if success:
            embed = discord.Embed(
                description="You have been successfully verified!",
                color=discord.Color.green()
            )

            await interaction.message.edit(embed=embed, view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def cancel(
        self, interaction: Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user != self.user:
            await interaction.response.send_message(embed=self.error_embed, ephemeral=True)
            return
        
        await interaction.message.edit(embed=interaction.message.embeds[0], view=None)
        await interaction.response.send_modal(VerificationModal(self.bot))

class Verification(commands.Cog, name="verification"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
            name="verify",
            description="Initiate the verification sequence."
    )
    @app_commands.guild_only()
    async def verify(self, interaction: Interaction) -> None:
        accounts = await self.bot.database.get_verification_by_discord_id(str(interaction.user.id))
        
        if accounts:
            if len(accounts) > 1:
                embed = discord.Embed(
                    description=f"Select an account to verify with.",
                    color=discord.Color.blue(),
                )

                user_ids = []
                for account in accounts:
                    user_ids.append(int(account["roblox_id"]))

                users = await roblox.get_users_by_ids(user_ids)
                    
                view = DropdownView(bot=self.bot, purpose="Verified", accounts=accounts, users=users)

                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return
            else:
                user_id = accounts[0]["roblox_id"]
        
                member = interaction.guild.get_member(interaction.user.id)
                data = await _discord.update_user(self.bot, member, user_id)

                embed = discord.Embed(
                    title="Update",
                    color=discord.Color.green(),
                )

                roles_added = ""
                roles_removed = ""

                for role in data["roles_added"]:
                    roles_added += f"- <@&{role}>\n"
                for role in data["roles_removed"]:
                    roles_removed += f"- <@&{role}>\n"

                roles_added = roles_added or "None"
                roles_removed = roles_removed or "None"

                embed.add_field(name="Nickname", value=data['nickname'], inline=False)
                embed.add_field(name="Roles Added", value=roles_added, inline=False)
                embed.add_field(name="Roles Removed", value=roles_removed, inline=False)

                await interaction.response.send_message(embed=embed) 
                return
        
        confirmation_buttons = Confirm(self.bot)

        active_code = await self.bot.database.get_verification_code(str(interaction.user.id))

        user_id = None
        user_name = None
        code = None

        if active_code is not None:
            embed = discord.Embed(
                description=f"You are already in the verification process. Please check your DMs for the code.",
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)

            user_id = active_code[1]
            code = active_code[2]

            user_information = await roblox.get_users_by_ids([int(user_id)])

            user_name = user_information['data'][0]['name']

            try:
                embed = discord.Embed(
                    description=f"""
                    Please place the following code in the \"About Me\" section of your [ROBLOX profile]({await roblox.profile(user_id)}). Select "Confirm" when you are done, or "Cancel" to cancel the verification process. Note, you are verifying as: [{user_name}]({await roblox.profile(user_id)}).
                    
                    Your verification code is: ```{active_code[2]}```
                    """,
                    color=discord.Color.blue(),
                )
                await interaction.user.send(embed=embed, view=confirmation_buttons)
            except discord.Forbidden:
                await interaction.response.send_message("I cannot send you DMs. Please enable DMs from server members.")
        else:
            data = await roblox.get_bloxlink_bind(str(interaction.guild.id), str(interaction.user.id))

            if data:
                if data['robloxID']:
                    user_id = int(data['robloxID'])

                    verification = await self.bot.database.get_verification_by_roblox_id(str(user_id))

                    if verification:
                        user_id = None
                        await interaction.response.send_modal(VerificationModal(self.bot))

                    user_name = await roblox.get_users_by_ids([user_id])

                    if not user_name:
                        user_id = None
                        await interaction.response.send_modal(VerificationModal(self.bot))
                    
                    user_name = user_name['data'][0]

                    embed = discord.Embed(
                        description=f"Bloxlink bind found. Would you like to verify as: [{user_name['name']}]({await roblox.profile(str(user_id))})",
                        color=discord.Color.blue()
                    )

                    await interaction.response.send_message(embed=embed, view=BloxlinkBind(self.bot, interaction.user, str(user_id)))

            

    @app_commands.command(
        name="unverify",
        description="Initiate the unverification sequence.",
    )
    @app_commands.guild_only()
    async def unverify(self, interaction: Interaction) -> None:
        accounts = await self.bot.database.get_verification_by_discord_id(str(interaction.user.id))

        if not accounts:
            embed = discord.Embed(
                description=f"You are not verified.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return
        
        if len(accounts) > 1:
            embed = discord.Embed(
                description=f"Select an account to unverify.",
                color=discord.Color.blue(),
            )

            user_ids = []
            for account in accounts:
                user_ids.append(int(account["roblox_id"]))

            users = await roblox.get_users_by_ids(user_ids)
                
            view = DropdownView(bot=self.bot, purpose="Unverified", accounts=accounts, users=users)

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await self.bot.database.delete_verification(str(interaction.user.id), str(accounts[0]["roblox_id"]))

            embed = discord.Embed(
                description=f"You have been unverified.",
                color=discord.Color.green(),
            )

            await interaction.response.send_message(embed=embed)
        
    @app_commands.command(
        name="update",
        description="Update a guild member."
    )
    @app_commands.describe(
        member="The member to update."
    )
    @app_commands.guild_only()
    async def update(self, interaction: Interaction, member: discord.Member = None) -> None:
        if member is None:
            member = interaction.user
            member = interaction.guild.get_member(member.id)
            data = await _discord.update_user(self.bot, member)
        else:
            data = await _discord.update_user(self.bot, member)

        if not data:
            embed = discord.Embed(
                description="User is not verified.",
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)
            return


        embed = discord.Embed(
            title="Update",
            color=discord.Color.green(),
            )

        roles_added = ""
        roles_removed = ""

        for role in data["roles_added"]:
            roles_added += f"- <@&{role}>\n"
        for role in data["roles_removed"]:
            roles_removed += f"- <@&{role}>\n"

        roles_added = roles_added or "None"
        roles_removed = roles_removed or "None"

        embed.add_field(name="Nickname", value=data['nickname'], inline=False)
        embed.add_field(name="Roles Added", value=roles_added, inline=False)
        embed.add_field(name="Roles Removed", value=roles_removed, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="link",
        description="Link a ROBLOX account to a Discord account.",
    )
    @app_commands.describe(discord_user="The Discord user to bind", roblox_user="The ROBLOX user to bind")
    @app_commands.checks.has_permissions(administrator=True)
    async def link(self, interaction: Interaction, discord_user: discord.User, roblox_user: str) -> None:
        if discord_user.bot:
            embed = discord.Embed(
                description="You cannot link a bot account.", color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        user_object = await roblox.get_user(roblox_user)

        if user_object is None:
            embed = discord.Embed(
                description=f"Roblox user \"{roblox_user}\" not found.", 
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        user_name = user_object["username"]
        user_id = user_object["id"]
        
        await self.bot.database.create_verification(str(discord_user.id), str(user_id))

        embed = discord.Embed(
            description=f"Successfully linked {discord_user.mention} with {user_name} ({user_id}).",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="links",
        description="View a user's linked accounts.",
    )
    @app_commands.describe(platform="The platform for the user queried")
    @app_commands.describe(user="The user to view the linked accounts for")
    @app_commands.checks.has_permissions(administrator=True)
    async def links(self, interaction: Interaction, platform: str, user: str) -> None:
        if platform.lower() == "discord":
            user = user.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            try:
                user = await self.bot.fetch_user(user)
            except:
                embed = discord.Embed(
                    description=f"User \"{user}\" not found.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            accounts = await self.bot.database.get_verification_by_discord_id(str(user.id))

            if not accounts:
                embed = discord.Embed(
                    description=f"User \"{user}\" has no links.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
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

            await interaction.response.send_message(embed=embed)
            return
        elif platform.lower() == "roblox":
            user_object = await roblox.get_user(user)

            if user_object is None:
                embed = discord.Embed(
                    description=f"User \"{user}\" not found.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            user_name = user_object["username"]
            user_id = user_object["id"]

            links = await self.bot.database.get_verification_by_roblox_id(str(user_id))

            if not links:
                embed = discord.Embed(
                    description=f"User \"{user_name}\" has no links.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return
                
            embed = discord.Embed(
                description=f"Linked Discord accounts for {user_name}:\n\n",
                color=discord.Color.blue(),
            )

            for link in links:
                embed.description += f"- <@{link['discord_id']}> - <t:{math.floor(link["verified_at"].timestamp())}:R>\n"

            await interaction.response.send_message(embed=embed)
            return
        
        else:
            embed = discord.Embed(
                description="The platform must be `discord` or `roblox`.", color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="unlink",
        description="Unlink a ROBLOX account from its Discord account.",
    )
    @app_commands.describe(discord_user="The Discord user to unlink")
    @app_commands.describe(roblox_user="The ROBLOX user to unlink")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlink(self, interaction: Interaction, discord_user: discord.User, roblox_user: str) -> None:
        user_object = await roblox.get_user(roblox_user)

        if user_object is None:
            embed = discord.Embed(
                description=f"Roblox user \"{roblox_user}\" not found.", 
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        user_name = user_object["username"]
        user_id = user_object["id"]
        
        await self.bot.database.delete_verification(str(discord_user.id), str(user_id))

        embed = discord.Embed(
            description=f"Successfully unlinked {discord_user.mention} with {user_name} ({user_id}).",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed)
    
async def setup(bot) -> None:
    await bot.add_cog(Verification(bot))