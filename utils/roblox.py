import requests
import os
import json
from discord.ext import commands

async def get_users_by_ids(user_ids: list[int]) -> dict:
    """
    Get the ROBLOX user by ID.

    :param user_id: The user ID.
    :return: The ROBLOX user.
    """
    
    url = "https://users.roblox.com/v1/users"
    
    data = json.dumps({
        "userIds": user_ids
    })

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=data)

    return response.json()

async def get_user_by_name(user_name: str) -> dict:
    """
    Get the ROBLOX user by name.

    :param user_name: The user name.
    :return: The ROBLOX user.
    """
    
    url = "https://users.roblox.com/v1/usernames/users"
    
    data = json.dumps({
        "usernames": [user_name]
    })

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=data)

    return response.json()

async def get_user_avatar(user_id: str) -> dict:
    response = requests.get(
      f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=48x48&format=Png&isCircular=false"
    )

    data = response.json()

    data = data['data'][0]
    
    return data['imageUrl']

async def get_user_presences_by_ids(user_ids: list[int]) -> dict:
    """
    Get ROBLOX user presences by IDs.

    :param user_id: The user IDs.
    :return: The ROBLOX user presences.
    """
    
    url = "https://presence.roblox.com/v1/presence/users"
    
    data = json.dumps({
        "userIds": user_ids
    })

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Cookie": f".ROBLOSECURITY={os.getenv('ROBLOX_COOKIE')}"
    }

    response = requests.post(url, headers=headers, data=data)

    return response.json()

async def get_user(user_input: str) -> dict:
    """
    Get the ROBLOX user from the user input.

    :param user_input: The user input.
    :return: The ROBLOX user.
    """
    user_id = None
    user_name = None

    if user_input.startswith("#"):
        user_id = user_input[1:]

        if user_id is not None:
            user = await get_users_by_ids([int(user_id)])

            if not user["data"]:
                return None

            user = user["data"][0]
            user_id = user["id"]
            user_name = user["name"]
            
    else:
        user_name = user_input
        
        if user_name is not None:
            user = await get_user_by_name(user_name)

            if not user["data"]:
                return None
            
            user = user["data"][0]
            user_id = user["id"]
            user_name = user["name"]
    
    if user_id is None or user_name is None:
        return None
    
    return {
        "id": user_id,
        "username": user_name
    }

async def get_user_information(user_id: int) -> dict:
    """
    Get the ROBLOX user information by ID.

    :param user_id: The user ID.
    :return: The ROBLOX user information.
    """
    
    url = f"https://users.roblox.com/v1/users/{user_id}"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()

async def get_user_groups(user_id: str) -> dict:
    """
    Get the ROBLOX user groups by ID.

    :param user_id: The user ID.
    :return: The ROBLOX user groups.
    """
    
    url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()

async def get_user_friends(user_id: str) -> list:
    """
    Get the ROBLOX user friends by ID.

    :param user_id: The user ID.
    """

    url = f"https://friends.roblox.com/v1/users/{user_id}/friends"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["data"]
    return []

async def profile(user_id: str) -> str:
    """
    Return a ROBLOX user's profile link.

    :param user_id: The user ID.
    :return: The profile link.
    """

    return f"https://www.roblox.com/users/{user_id}/profile"

async def get_community_groups(bot: commands.Bot, user_id: str) -> list:
    """
    Get the ROBLOX community groups by ID.

    :param bot: The Discord bot.
    :param user_id: The user ID.
    :return: The ROBLOX community groups.
    """
    
    groups = await get_user_groups(user_id)
    groups = groups["data"]

    community_groups = list(filter(lambda group: str(group["group"]["id"]) in bot.config["community_groups"], groups))
    
    return community_groups

async def get_bloxlink_bind(guild_id: str, discord_id: str) -> dict:
    url = f"https://api.blox.link/v4/public/guilds/{guild_id}/discord-to-roblox/{discord_id}"

    response = requests.get(url, headers = {"Authorization": os.getenv("BLOXLINK_API_TOKEN")})

    if response.status_code == 200:
        return response.json()
    return []
