from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import auth_service
from app.db.session import get_db
from app.models.schemas import ErrorResponse, LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    return await auth_service.login(db=db, payload=payload)
