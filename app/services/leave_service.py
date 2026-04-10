from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.enums import DecisionSource, LeaveStatus, RuleDecision
from app.core.errors import NotFoundError
from app.models.schemas import ApplyLeaveRequest, LeaveListResponse, LeaveResponse

from app.services.audit_service import AuditService
from app.services.rule_engine import RuleContext, RuleEngine
from app.services.cache_service import CacheService
from app.services.queue_service import QueueService
from app.services.notification_service import NotificationService


class LeaveService:
    def __init__(
        self,
        rule_engine: RuleEngine,
        audit_service: AuditService,
        cache_service: CacheService,
        queue_service: QueueService,
        notification_service: NotificationService,
    ):
        self.rule_engine = rule_engine
        self.audit_service = audit_service
        self.cache_service = cache_service
        self.queue_service = queue_service
        self.notification_service = notification_service

    async def apply_leave(self, db: AsyncSession, user: CurrentUser, payload: ApplyLeaveRequest) -> LeaveResponse:

        async with db.begin():   # 🔥 TRANSACTION FIX

            insert_row = (
                await db.execute(
                    text("""
                        INSERT INTO leave_requests (
                            user_id, leave_type, start_date, end_date, reason, status
                        )
                        VALUES (:user_id, :leave_type, :start_date, :end_date, :reason, :status)
                        RETURNING *
                    """),
                    {
                        "user_id": user.user_id,
                        "leave_type": payload.leave_type,
                        "start_date": payload.start_date,
                        "end_date": payload.end_date,
                        "reason": payload.reason,
                        "status": LeaveStatus.PENDING.value,
                    },
                )
            ).mappings().one()

            await self.audit_service.log_state_change(
                db=db,
                entity_id=insert_row["id"],
                actor_id=user.user_id,
                actor_type="system",
                action="status_change",
                prev_state=None,
                new_state={"status": LeaveStatus.PENDING.value},
            )

            rules = await self.rule_engine.load_cached_rules(db, self.cache_service)

            decision = self.rule_engine.evaluate(
                RuleContext(
                    role=user.role,
                    leave_type=payload.leave_type,
                    start_date=payload.start_date,
                    end_date=payload.end_date,
                    days_requested=insert_row["days_requested"],
                    balance_remaining=0,
                    pending_count=0,
                ),
                rules,
            )

            if decision == RuleDecision.UNCERTAIN:
                status = LeaveStatus.PROCESSING
                source = None
            elif decision == RuleDecision.APPROVED:
                status = LeaveStatus.APPROVED
                source = DecisionSource.RULE_ENGINE
            else:
                status = LeaveStatus.REJECTED
                source = DecisionSource.RULE_ENGINE

            updated = (
                await db.execute(
                    text("""
                        UPDATE leave_requests
                        SET status = :status,
                            decision_source = :source,
                            updated_at = now()
                        WHERE id = :id
                        RETURNING *
                    """),
                    {
                        "status": status.value,
                        "source": source.value if source else None,
                        "id": insert_row["id"],
                    },
                )
            ).mappings().one()

            # 🔥 CACHE INVALIDATION
            await self.cache_service.invalidate_leave(updated["id"])

            await self.audit_service.log_state_change(
                db=db,
                entity_id=updated["id"],
                actor_id=user.user_id,
                actor_type="rule_engine" if source else "system",
                action="status_change",
                prev_state={"status": LeaveStatus.PENDING.value},
                new_state={"status": status.value},
            )

        # 🔥 OUTSIDE TRANSACTION → SAFE

        if status == LeaveStatus.PROCESSING:
            await self.queue_service.push_ai_job(updated["id"])

        # 🔥 NOTIFICATION
        await self.notification_service.notify(
            str(user.user_id),
            f"Your leave is {status.value}"
        )

        return LeaveResponse.model_validate(updated)

    async def get_leave(self, db: AsyncSession, leave_id: UUID, user: CurrentUser) -> LeaveResponse:

        cached = await self.cache_service.get_leave(leave_id)
        if cached:
            return LeaveResponse.model_validate(cached)

        row = (
            await db.execute(
                text("SELECT * FROM leave_requests WHERE id = :id"),
                {"id": leave_id},
            )
        ).mappings().first()

        if not row:
            raise NotFoundError("Leave request not found")

        if user.role.value != "admin" and row["user_id"] != user.user_id:
            raise NotFoundError("Leave request not found")

        await self.cache_service.set_leave(leave_id, dict(row))

        return LeaveResponse.model_validate(row)