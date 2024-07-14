import asyncpg
import random
import datetime

class DatabaseManager:
    def __init__(self, *, connection: asyncpg.pool.Pool) -> None:
        self.connection = connection

#   ==============================
#   ========== WARNINGS ==========
#   ==============================

    async def add_warn(
        self, discord_id: str, server_id: str, moderator_id: str, reason: str
    ) -> int:
        async with self.connection.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT id FROM warns WHERE discord_id=$1 AND server_id=$2 ORDER BY id DESC LIMIT 1",
                discord_id,
                server_id,
            )
            warn_id = result['id'] + 1 if result is not None else 1
            await conn.execute(
                "INSERT INTO warns(id, discord_id, server_id, moderator_id, reason) VALUES ($1, $2, $3, $4, $5)",
                warn_id,
                discord_id,
                server_id,
                moderator_id,
                reason,
            )
            return warn_id

    async def remove_warn(self, warn_id: int, discord_id: str, server_id: str) -> int:
        async with self.connection.acquire() as conn:
            await conn.execute(
                "DELETE FROM warns WHERE id=$1 AND discord_id=$2 AND server_id=$3",
                warn_id,
                discord_id,
                server_id,
            )
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM warns WHERE discord_id=$1 AND server_id=$2",
                discord_id,
                server_id,
            )
            return result if result is not None else 0

    async def get_warnings(self, discord_id: str, server_id: str) -> list:
        async with self.connection.acquire() as conn:
            rows = await conn.fetch(
                "SELECT discord_id, server_id, moderator_id, reason, created_at, EXTRACT(epoch FROM created_at)::int, id FROM warns WHERE discord_id=$1 AND server_id=$2",
                discord_id,
                server_id,
            )
            return [dict(row) for row in rows]


#   ==============================
#   ======== VERIFICATION ========
#   ==============================

    async def create_verification_code(self, discord_id: str, roblox_id: str) -> str:
        safe_words = [
            "adventure", "build", "create", "explore", "fun", "game", "happy", "island", 
            "jump", "kind", "magic", "nice", "ocean", "play", "quest", "run", "smile", 
            "team", "universe", "victory", "collect", "dream", "enjoy", "friendly", 
            "hero", "join", "laugh", "meet", "open", "race"
        ]
        code = " ".join(random.choices(safe_words, k=random.randint(5, 9)))

        async with self.connection.acquire() as conn:
            await conn.execute(
                "INSERT INTO verification_codes(discord_id, roblox_id, code, created_at) VALUES ($1, $2, $3, $4)",
                discord_id,
                roblox_id,
                code,
                datetime.datetime.now()
            )
        return code

    async def delete_verification_code(self, discord_id: str) -> bool:
        async with self.connection.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM verification_codes WHERE discord_id=$1",
                discord_id,
            )
        
            if result: return True
            return False

    async def get_verification_code(self, discord_id: str) -> asyncpg.Record:
        async with self.connection.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT discord_id, roblox_id, code, created_at FROM verification_codes WHERE discord_id=$1",
                discord_id,
            )
            return result

    async def create_verification(self, discord_id: str, roblox_id: str) -> bool:
        async with self.connection.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT id FROM verifications ORDER BY id DESC LIMIT 1"
            )
            verification_id = result['id'] + 1 if result is not None else 1

            result = await conn.execute(
                "INSERT INTO verifications(id, discord_id, roblox_id, verified_at) VALUES ($1, $2, $3, $4)",
                verification_id,
                discord_id,
                roblox_id,
                datetime.datetime.now()
            )

            if result: return True
            return False

    async def get_verification_by_discord_id(self, discord_id: str) -> list:
        async with self.connection.acquire() as conn:
            rows = await conn.fetch(
                "SELECT discord_id, roblox_id, verified_at FROM verifications WHERE discord_id=$1",
                discord_id,
            )
            return [dict(row) for row in rows]

    async def get_verification_by_roblox_id(self, roblox_id: str) -> list:
        async with self.connection.acquire() as conn:
            rows = await conn.fetch(
                "SELECT discord_id, roblox_id, verified_at FROM verifications WHERE roblox_id=$1",
                roblox_id,
            )
            return [dict(row) for row in rows]

    async def get_all_verifications(self) -> list:
        async with self.connection.acquire() as conn:
            rows = await conn.fetch(
                "SELECT discord_id, roblox_id, verified_at FROM verifications",
            )
            return [dict(row) for row in rows]

    async def delete_verification(self, discord_id: str, roblox_id: str) -> None:
        async with self.connection.acquire() as conn:
            await conn.execute(
                "DELETE FROM verifications WHERE discord_id=$1 AND roblox_id=$2",
                discord_id,
                roblox_id
            )

#   ==============================
#   ========== TRACKER ===========
#   ==============================

    async def get_tracked_user(self, roblox_id: str) -> asyncpg.Record:
        async with self.connection.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT roblox_id, posted, moderator_id, reason, created_at FROM tracked_users WHERE roblox_id=$1",
                roblox_id,
            )
            return result

    async def get_tracked_users(self) -> list[asyncpg.Record]:
        async with self.connection.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM tracked_users",
            )
            return [dict(row) for row in rows]

    async def track_user(self, roblox_id: str, moderator_id: str, reason: str) -> bool:
        async with self.connection.acquire() as conn:
            result = await conn.execute(
                "INSERT INTO tracked_users(roblox_id, posted, moderator_id, reason, created_at) VALUES ($1, $2, $3, $4, $5)",
                roblox_id,
                False,
                moderator_id,
                reason,
                datetime.datetime.now()
            )

        if result: return True
        return False
    
    async def untrack_user(self, roblox_id: str) -> bool:
        async with self.connection.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM tracked_users WHERE roblox_id=$1",
                roblox_id
            )

            if result: return True
            return False
        
    async def modify_tracked_user(self, roblox_id: str, posted: bool) -> bool:
        async with self.connection.acquire() as conn:
            result = await conn.execute(
                "UPDATE tracked_users SET posted=$1 WHERE roblox_id=$2",
                posted,
                roblox_id
            )

            if result: return True
            return False