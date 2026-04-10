from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.core.enums import UserRole
from app.core.errors import UnauthorizedError
from app.models.schemas import LoginRequest, LoginResponse


class AuthService:
    async def login(self, db: AsyncSession, payload: LoginRequest) -> LoginResponse:
        row = (
            await db.execute(
                text("SELECT id, role FROM users WHERE email = :email"),
                {"email": payload.email},
            )
        ).mappings().first()
        if not row:
            raise UnauthorizedError("Invalid credentials")

        role = UserRole(row["role"])
        token = create_access_token(row["id"], role)
        return LoginResponse(access_token=token, user_id=row["id"], role=role)
