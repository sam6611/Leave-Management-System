from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_admin
from app.core.dependencies import leave_service
from app.db.session import get_db
from app.models.schemas import AdminOverrideRequest, ErrorResponse, LeaveResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.patch(
    "/leaves/{leave_id}/override",
    response_model=LeaveResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def override_leave(
    leave_id: UUID,
    payload: AdminOverrideRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: CurrentUser = Depends(require_admin),
) -> LeaveResponse:
    return await leave_service.override_leave(
        db=db,
        leave_id=leave_id,
        admin_user=admin_user,
        new_status=payload.status,
        reason=payload.reason,
    )
