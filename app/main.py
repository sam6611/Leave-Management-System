from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.models.schemas import ErrorResponse
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.leaves import router as leaves_router

app = FastAPI(title="Automated Leave Approval System")

app.include_router(auth_router)
app.include_router(leaves_router)
app.include_router(admin_router)

app.get("/")(lambda: JSONResponse(status_code=200, content={"message": "Hello, World!"}))


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(code=exc.code, message=exc.message, details=exc.details).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)
