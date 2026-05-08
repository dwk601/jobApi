from __future__ import annotations

import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            decode_responses=True,
        )
        return _redis_client
    except (ValueError, Exception) as exc:
        logger.warning("Redis unavailable: %s. Caching and rate limiting disabled.", exc)
        return None


async def close_redis() -> None:
    if _redis_client is not None:
        await _redis_client.aclose()
