from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RuleDecision, UserRole


@dataclass
class RuleContext:
    role: UserRole
    leave_type: str
    start_date: date
    end_date: date
    days_requested: int
    balance_remaining: int
    pending_count: int


class RuleEngine:
    async def load_active_rules(self, db: AsyncSession) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT rule_key, rule_value, priority
                    FROM leave_rules
                    WHERE is_active = true
                    ORDER BY priority ASC
                    """
                )
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    def evaluate(self, ctx: RuleContext, rules: list[dict[str, Any]]) -> RuleDecision:
        for rule in rules:
            key = rule["rule_key"]
            value = rule["rule_value"] or {}

            if key == "max_auto_approve_days":
                max_days = value.get(ctx.role.value)
                if isinstance(max_days, int) and ctx.days_requested <= max_days:
                    return RuleDecision.APPROVED

            elif key == "blackout_dates":
                dates = set(value.get("dates", []))
                if ctx.start_date.isoformat() in dates or ctx.end_date.isoformat() in dates:
                    return RuleDecision.REJECTED

            elif key == "min_advance_days":
                # HLD says same-day request can be rejected by rule.
                if isinstance(value.get("value"), int) and value["value"] >= 1 and ctx.start_date <= date.today():
                    return RuleDecision.REJECTED

            elif key == "max_pending_requests":
                threshold = value.get("value")
                if isinstance(threshold, int) and ctx.pending_count >= threshold:
                    return RuleDecision.REJECTED

            elif key == "balance_required":
                if bool(value.get("value")) and ctx.balance_remaining < ctx.days_requested:
                    return RuleDecision.REJECTED

            elif key == "medical_auto_approve_days":
                medical_days = value.get("value")
                if ctx.leave_type == "medical" and isinstance(medical_days, int) and ctx.days_requested <= medical_days:
                    return RuleDecision.APPROVED

        return RuleDecision.UNCERTAIN
