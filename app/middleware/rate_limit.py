from __future__ import annotations

import time

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.constants import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW
from app.redis_client import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time()) // RATE_LIMIT_WINDOW
        key = f"rl:{client_ip}:{window}"

        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, RATE_LIMIT_WINDOW + 1, nx=True)
            result = await pipe.execute()

        if result[0] > RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )

        return await call_next(request)
