import discord
from discord.ext import commands

from utils import roblox

async def update_user(bot: commands.Bot, member: discord.Member, roblox_id: str | None = None) -> dict | None:
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
    roles_to_add = [bot.config["roles"]["verification"]["verified"], bot.config["roles"]["verification"]["outsider"], bot.config["roles"]["verification"]["basic_category"]]
    roles_to_remove = [bot.config["roles"]["verification"]["unverified"]]

    community_groups = await roblox.get_community_groups(bot, roblox_id)
    if community_groups:
        community_groups = list(community_groups)
        in_shirai_ryu = filter(lambda group: str(group["group"]["id"]) == bot.config["community_groups"][0], community_groups)

        if in_shirai_ryu:
            in_shirai_ryu = list(in_shirai_ryu)
            
            shirai_ryu_rank_name = in_shirai_ryu[0]["role"]["name"] # The role name (Ex. Technician)
            shirai_ryu_rank = in_shirai_ryu[0]["role"]["rank"] # The rank number (Ex. 254)
            shirai_ryu_rank_id = in_shirai_ryu[0]["role"]["id"] # The role ID (Ex. 112572242)

            rank_role_obj = filter(lambda r: r.group_role == str(shirai_ryu_rank_id), bot.config.ranks)
            rank_type = rank_role_obj.type

            if not rank_role_obj and str(shirai_ryu_rank_id) != bot.config['roles']['verification']['faction_supporter_group_role']:
                return
            elif str(shirai_ryu_rank_id) == bot.config['roles']['verification']['faction_supporter_group_role']:
                rank_role_id = bot.config['roles']['verification']['faction_supporter_group_role']
                roles_to_add.append(rank_role_id)
            else:
                rank_role_id = rank_role_obj[0].role_id
                roles_to_add.append(rank_role_id)

            other_ranks = filter(lambda r: r.group_role != str(shirai_ryu_rank_id), bot.config.ranks)

            for rank in other_ranks:
                roles_to_remove.append(rank.role_id)

            if rank_type == "lr":
                roles_to_add.append(bot.config["roles"]["verification"]["lr_category"])
                roles_to_remove.remove(bot.config["roles"]["verification"]["mr_category"])
            elif rank_type == "mr":
                roles_to_add.remove(bot.config["roles"]["verification"]["lr_category"])
                roles_to_remove.append(bot.config["roles"]["verification"]["mr_category"])
            else:
                roles_to_remove.remove(bot.config["roles"]["verification"]["lr_category"])
                roles_to_remove.remove(bot.config["roles"]["verification"]["mr_category"])

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
    
    
