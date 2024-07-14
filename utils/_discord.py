import discord
from discord.ext import commands

from utils import roblox

async def update_user(bot: commands.Bot, member: discord.Member, roblox_id: str | None = None) -> dict:
    """
    Update a Discord user's nickname and roles from ID in a guild.
    
    :param bot: The Discord bot.
    :param member: The guild member.
    :param roblox_id: (Optional) The member's roblox id.

    :return: The return data.
    """

    if not roblox_id:
        user_data = await bot.database.get_verification_by_discord_id(str(member.id))

        if not user_data:
            return 

        roblox_id = user_data[0]["roblox_id"]

    # ====================
    # ====== GROUPS ======
    # ====================

    current_roles = member.roles
    roles_to_add = [bot.config["roles"]["verification"]["verified"], bot.config["roles"]["verification"]["outsider"]]
    roles_to_remove = [bot.config["roles"]["verification"]["unverified"]]

    # community_groups = await roblox.get_community_groups(bot, roblox_id)

    # if community_groups:
    #     community_groups = list(community_groups)
    #     in_imperium = filter(lambda group: str(group["group"]["id"]) == bot.config["community_groups"][0], community_groups)

    #     if in_imperium:
    #         in_imperium = list(in_imperium)
            
    #         rank_name = in_imperium[0]["role"]["name"]
    #         rank = in_imperium[0]["role"]["rank"] # TODO: Give appropriate roles based on rank

    #         role = discord.utils.get(member.guild.roles, name=rank_name)

    #         if role:
    #             roles_to_add.append(str(role.id))

    #             for imperium_role in imperium_roles_list:
    #                 if imperium_role != role:
    #                     roles_to_remove.append(imperium_role)


    #     else:
    #         roles_to_remove.extend(imperium_roles_list)

    # ====================
    # ===== NICKNAME =====
    # ====================

    nickname = ""

    user_information = await roblox.get_user_information(roblox_id)

    if user_information:
        nickname = user_information["name"]

    # Update the user's nickname
    nick_error = False # If the bot doesn't have permission to change the nickname
    if member.nick != nickname:
        try:
            await member.edit(nick=nickname)
        except discord.Forbidden:
            nick_error = True

    # --------------------------

    # Get the roles that need to be added and removed
    roles_added = [role for role in roles_to_add if role not in [str(role.id) for role in current_roles]] 
    roles_removed = [role for role in roles_to_remove if role in [str(role.id) for role in current_roles]]

    member_roles = [role for role in current_roles if str(role.id) not in roles_removed] + [discord.utils.get(member.guild.roles, id=int(role)) for role in roles_added]
    
    await member.edit(roles=member_roles)

    return {
        "nickname": nickname,
        "roles_added": roles_added,
        "roles_removed": roles_removed,
        "nick_error": nick_error
    }
    
        
    
