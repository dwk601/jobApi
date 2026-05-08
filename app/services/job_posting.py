from __future__ import annotations

import hashlib
import json
import math

from app.constants import CACHE_TTL_DETAIL, CACHE_TTL_LIST, CACHE_TTL_STATS, MAX_PAGE_SIZE
from app.redis_client import get_redis
from app.repositories.job_posting import JobPostingRepository
from app.schemas.job_posting import (
    JobPostingDetail,
    JobPostingListResponse,
    JobPostingQueryParams,
    JobPostingStats,
    JobPostingSummary,
)


class JobPostingService:
    def __init__(self, repo: JobPostingRepository):
        self.repo = repo

    async def list_jobs(self, params: JobPostingQueryParams) -> JobPostingListResponse:
        redis_client = get_redis()
        if redis_client is not None:
            cache_key = self._build_cache_key("list", params)
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return JobPostingListResponse(**data)

        items, total = await self.repo.find_all(params)
        page_size = min(params.page_size, MAX_PAGE_SIZE)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        response = JobPostingListResponse(
            items=[JobPostingSummary.model_validate(item) for item in items],
            total=total,
            page=params.page,
            page_size=page_size,
            total_pages=total_pages,
        )

        if redis_client is not None:
            await redis_client.setex(
                cache_key, CACHE_TTL_LIST, response.model_dump_json()
            )
        return response

    async def get_job_by_id(self, job_id: int) -> JobPostingDetail | None:
        redis_client = get_redis()
        cache_key = f"job:id:{job_id}"
        if redis_client is not None:
            cached = await redis_client.get(cache_key)
            if cached:
                return JobPostingDetail(**json.loads(cached))

        job = await self.repo.find_by_id(job_id)
        if job is None:
            return None

        detail = JobPostingDetail.model_validate(job)
        if redis_client is not None:
            await redis_client.setex(cache_key, CACHE_TTL_DETAIL, detail.model_dump_json())
        return detail

    async def get_job_by_record_id(self, record_id: str) -> JobPostingDetail | None:
        redis_client = get_redis()
        cache_key = f"job:rid:{record_id}"
        if redis_client is not None:
            cached = await redis_client.get(cache_key)
            if cached:
                return JobPostingDetail(**json.loads(cached))

        job = await self.repo.find_by_record_id(record_id)
        if job is None:
            return None

        detail = JobPostingDetail.model_validate(job)
        if redis_client is not None:
            await redis_client.setex(cache_key, CACHE_TTL_DETAIL, detail.model_dump_json())
        return detail

    async def get_stats(self) -> JobPostingStats:
        redis_client = get_redis()
        cache_key = "job:stats"
        if redis_client is not None:
            cached = await redis_client.get(cache_key)
            if cached:
                return JobPostingStats(**json.loads(cached))

        stats = await self.repo.get_stats()
        if redis_client is not None:
            await redis_client.setex(cache_key, CACHE_TTL_STATS, stats.model_dump_json())
        return stats

    async def invalidate_stats_cache(self) -> None:
        redis_client = get_redis()
        if redis_client is not None:
            await redis_client.delete("job:stats")

    @staticmethod
    def _build_cache_key(prefix: str, params: JobPostingQueryParams) -> str:
        raw = params.model_dump_json(exclude_none=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"job:{prefix}:{digest}"
