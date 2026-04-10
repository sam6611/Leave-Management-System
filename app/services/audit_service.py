from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AuditService:
    async def log_state_change(
        self,
        db: AsyncSession,
        entity_id: UUID,
        actor_id: UUID | None,
        actor_type: str,
        action: str,
        prev_state: dict[str, Any] | None,
        new_state: dict[str, Any] | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    entity_type, entity_id, actor_id, actor_type, action, prev_state, new_state, metadata
                ) VALUES (
                    'leave_request', :entity_id, :actor_id, :actor_type, :action, :prev_state, :new_state, :metadata
                )
                """
            ),
            {
                "entity_id": entity_id,
                "actor_id": actor_id,
                "actor_type": actor_type,
                "action": action,
                "prev_state": prev_state,
                "new_state": new_state,
                "metadata": metadata,
            },
        )
