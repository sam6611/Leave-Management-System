from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import UserRole
from app.core.errors import ForbiddenError, UnauthorizedError
from app.db.session import get_db


security = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user_id: UUID, role: UserRole, department: str | None = None):
        self.user_id = user_id
        self.role = role
        self.department = department


def create_access_token(user_id: UUID, role: UserRole) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_exp_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if creds is None:
        raise UnauthorizedError("Missing bearer token")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id or not role:
            raise UnauthorizedError("Invalid token payload")
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    row = (
        await db.execute(
            text("SELECT id, role, department FROM users WHERE id = :id"),
            {"id": user_id},
        )
    ).mappings().first()
    if not row:
        raise UnauthorizedError("User not found")
    return CurrentUser(user_id=row["id"], role=UserRole(row["role"]), department=row["department"])


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")
    return user
