import asyncio
import json
import random
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import text

from app.core.enums import DecisionSource, LeaveStatus
from app.db.session import AsyncSessionLocal
from app.services.audit_service import AuditService
from app.services.cache_service import CacheService
from app.services.notification_service import NotificationService

REDIS_URL = "redis://localhost:6379"
AI_QUEUE_KEY = "queue:ai_jobs"
AI_DLQ_KEY = "queue:ai_dlq"
MAX_RETRIES = 3


async def ai_decide(leave: dict[str, Any]) -> tuple[LeaveStatus, str]:
    """
    Mock AI decision function.
    Returns APPROVED/REJECTED randomly with generated reasoning.
    """
    await asyncio.sleep(0.2)
    decision = random.choice([LeaveStatus.APPROVED, LeaveStatus.REJECTED])
    reasoning = (
        f"AI mock decision for leave_type={leave['leave_type']} "
        f"from {leave['start_date']} to {leave['end_date']}: {decision.value}"
    )
    return decision, reasoning


class AIWorker:
    def __init__(self) -> None:
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.audit_service = AuditService()
        self.cache_service = CacheService()
        self.notification_service = NotificationService()

    async def run(self) -> None:
        print("[worker][INFO] started, waiting for jobs on queue:ai_jobs")
        while True:
            try:
                item = await self.redis.brpop(AI_QUEUE_KEY, timeout=5)
                if not item:
                    continue

                _, raw_job = item
                await self._process_job(raw_job)
            except Exception as exc:
                # Never crash the worker loop.
                print(f"[worker][ERROR] loop error: {exc}")
                await asyncio.sleep(1)

    async def _retry_later(self, job: dict[str, Any], delay: int) -> None:
        # Non-blocking retry scheduling: does not block main consumer loop.
        await asyncio.sleep(delay)
        await self.redis.lpush(AI_QUEUE_KEY, json.dumps(job))

    async def _process_job(self, raw_job: str) -> None:
        try:
            job = json.loads(raw_job)
            leave_id = UUID(job["leave_id"])
            attempt = int(job.get("attempt", 1))
        except Exception as exc:
            print(f"[worker][ERROR] invalid job payload, moving to DLQ: {exc}")
            await self.redis.lpush(AI_DLQ_KEY, raw_job)
            print("[metrics] job_dlq += 1")
            return

        # HLD-compatible retry semantics: attempt > MAX_RETRIES goes to DLQ.
        if attempt > MAX_RETRIES:
            print(f"[worker][ERROR] job exceeded max retries, pushing to DLQ: leave_id={leave_id}")
            await self.redis.lpush(AI_DLQ_KEY, raw_job)
            print("[metrics] job_dlq += 1")
            return

        print(f"[worker][INFO] job start: leave_id={leave_id}, attempt={attempt}")

        try:
            async with AsyncSessionLocal() as db:
                leave_row = (
                    await db.execute(
                        text(
                            """
                            SELECT id, user_id, status, leave_type, start_date, end_date
                            FROM leave_requests
                            WHERE id = :id
                            """
                        ),
                        {"id": leave_id},
                    )
                ).mappings().first()

                if not leave_row:
                    print(f"[worker][WARN] leave not found, skipping: leave_id={leave_id}")
                    return

                if leave_row["status"] != LeaveStatus.PROCESSING.value:
                    print(
                        f"[worker][INFO] skip non-processing leave: leave_id={leave_id}, "
                        f"status={leave_row['status']}"
                    )
                    return

                decision_status, ai_reasoning = await ai_decide(dict(leave_row))
                prev_status = leave_row["status"]

                async with db.begin():
                    updated_row = (
                        await db.execute(
                            text(
                                """
                                UPDATE leave_requests
                                SET status = :status,
                                    decision_source = :decision_source,
                                    ai_reasoning = :ai_reasoning,
                                    updated_at = now()
                                WHERE id = :id
                                RETURNING *
                                """
                            ),
                            {
                                "id": leave_id,
                                "status": decision_status.value,
                                "decision_source": DecisionSource.AI.value,
                                "ai_reasoning": ai_reasoning,
                            },
                        )
                    ).mappings().one()

                    await self.audit_service.log_state_change(
                        db=db,
                        entity_id=leave_id,
                        actor_id=None,
                        actor_type="ai",
                        action="status_change",
                        prev_state={"status": prev_status},
                        new_state={"status": decision_status.value},
                        metadata={"attempt": attempt},
                    )

                # Side effects after successful DB transaction.
                await self.cache_service.invalidate_leave(leave_id)
                await self.notification_service.notify(
                    user_id=str(updated_row["user_id"]),
                    message=f"Your leave request {leave_id} is {decision_status.value}",
                )

            print(f"[worker][INFO] success: leave_id={leave_id}, status={decision_status.value}")
            print("[metrics] job_success += 1")

        except Exception as exc:
            delay = 2 ** attempt  # 2s, 4s, 8s
            retry_job = {"leave_id": str(leave_id), "attempt": attempt + 1}
            print(
                f"[worker][ERROR] retry: leave_id={leave_id}, "
                f"attempt={attempt + 1}, delay={delay}s, error={exc}"
            )
            print("[metrics] job_retry += 1")
            asyncio.create_task(self._retry_later(retry_job, delay))


async def main() -> None:
    worker = AIWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
