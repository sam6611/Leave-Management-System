from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.enums import LeaveStatus, UserRole


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ApplyLeaveRequest(BaseModel):
    leave_type: str = Field(min_length=2, max_length=64)
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ApplyLeaveRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class LeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    days_requested: int
    reason: str | None
    status: LeaveStatus
    decision_source: str | None = None
    ai_reasoning: str | None = None
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    role: UserRole


class AdminOverrideRequest(BaseModel):
    status: LeaveStatus
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_override_status(self) -> "AdminOverrideRequest":
        if self.status not in (LeaveStatus.APPROVED, LeaveStatus.REJECTED):
            raise ValueError("override status must be APPROVED or REJECTED")
        return self


class LeaveListResponse(BaseModel):
    items: list[LeaveResponse]
    limit: int
    next_after_id: UUID | None = None
