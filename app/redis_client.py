from __future__ import annotations

import redis.asyncio as redis

from app.config import settings

redis_client = redis.Redis.from_url(
    settings.redis_url,
    max_connections=settings.redis_max_connections,
    socket_timeout=settings.redis_socket_timeout,
    socket_connect_timeout=settings.redis_socket_connect_timeout,
    decode_responses=True,
)
