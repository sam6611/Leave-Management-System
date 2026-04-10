import json
from uuid import UUID

import redis.asyncio as redis

REDIS_URL = "redis://localhost:6379"


class CacheService:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)

    async def get_leave(self, leave_id: UUID):
        data = await self.client.get(f"leave:{leave_id}")
        return json.loads(data) if data else None

    async def set_leave(self, leave_id: UUID, data: dict):
        await self.client.setex(f"leave:{leave_id}", 60, json.dumps(data))

    async def invalidate_leave(self, leave_id: UUID):
        await self.client.delete(f"leave:{leave_id}")