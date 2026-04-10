import json
import redis.asyncio as redis

REDIS_URL = "redis://localhost:6379"


class NotificationService:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)

    async def notify(self, user_id: str, message: str):
        job = {
            "user_id": user_id,
            "message": message
        }
        await self.client.lpush("queue:notifications", json.dumps(job))
        