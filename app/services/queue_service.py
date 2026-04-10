import json
import redis.asyncio as redis

REDIS_URL = "redis://localhost:6379"


class QueueService:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)

    async def push_ai_job(self, leave_id: str):
        job = {
            "leave_id": str(leave_id),
            "attempt": 1
        }
        await self.client.lpush("queue:ai_jobs", json.dumps(job))