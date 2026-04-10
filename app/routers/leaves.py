from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.dependencies import leave_service
from app.core.enums import LeaveStatus
from app.db.session import get_db
from app.models.schemas import ApplyLeaveRequest, ErrorResponse, LeaveListResponse, LeaveResponse

router = APIRouter(prefix="/api/leaves", tags=["leaves"])


@router.post(
    "",
    response_model=LeaveResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def apply_leave(
    payload: ApplyLeaveRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> LeaveResponse:
    return await leave_service.apply_leave(db=db, user=user, payload=payload)


@router.get(
    "/{leave_id}",
    response_model=LeaveResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_leave(
    leave_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> LeaveResponse:
    return await leave_service.get_leave(db=db, leave_id=leave_id, user=user)


@router.get(
    "",
    response_model=LeaveListResponse,
    responses={401: {"model": ErrorResponse}},
)
async def list_leaves(
    status: LeaveStatus | None = Query(default=None),
    department: str | None = Query(default=None, min_length=1, max_length=64),
    after_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> LeaveListResponse:
    return await leave_service.list_leaves(
        db=db,
        user=user,
        status=status,
        department=department,
        after_id=after_id,
        limit=limit,
    )
