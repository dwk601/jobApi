from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ValidationError(HTTPException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=422, detail=detail)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
