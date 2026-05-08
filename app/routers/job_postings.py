from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import ServiceDep
from app.exceptions import NotFoundError
from app.schemas.job_posting import (
    JobPostingDetail,
    JobPostingListResponse,
    JobPostingQueryParams,
    JobPostingStats,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Postings"])


@router.get("/", response_model=JobPostingListResponse)
async def list_jobs(
    service: ServiceDep,
    source: Annotated[str | None, Query(description="Filter by job source")] = None,
    company: Annotated[str | None, Query(description="Filter by company name")] = None,
    company_inferred: Annotated[
        bool | None, Query(description="Filter by inferred company")
    ] = None,
    language: Annotated[str | None, Query(description="Filter by language")] = None,
    q: Annotated[
        str | None, Query(description="Trigram search on title, description, company")
    ] = None,
    location_city: Annotated[str | None, Query(description="Filter by city")] = None,
    location_state: Annotated[str | None, Query(description="Filter by state")] = None,
    salary_min: Annotated[float | None, Query(description="Minimum salary")] = None,
    salary_max: Annotated[float | None, Query(description="Maximum salary")] = None,
    job_category: Annotated[str | None, Query(description="Filter by job category slug")] = None,
    post_date_from: Annotated[str | None, Query(description="Post date from (YYYY-MM-DD)")] = None,
    post_date_to: Annotated[str | None, Query(description="Post date to (YYYY-MM-DD)")] = None,
    sort_by: Annotated[str, Query(description="Sort field")] = "post_date",
    sort_order: Annotated[str, Query(description="Sort order (asc/desc)")] = "desc",
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> JobPostingListResponse:
    from datetime import date

    params = JobPostingQueryParams(
        source=source,
        company=company,
        company_inferred=company_inferred,
        language=language,
        q=q,
        location_city=location_city,
        location_state=location_state,
        salary_min=salary_min,
        salary_max=salary_max,
        job_category=job_category,
        post_date_from=date.fromisoformat(post_date_from) if post_date_from else None,
        post_date_to=date.fromisoformat(post_date_to) if post_date_to else None,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return await service.list_jobs(params)


@router.get("/stats", response_model=JobPostingStats)
async def get_stats(service: ServiceDep) -> JobPostingStats:
    return await service.get_stats()


@router.get("/{job_id}", response_model=JobPostingDetail)
async def get_job(service: ServiceDep, job_id: int) -> JobPostingDetail:
    job = await service.get_job_by_id(job_id)
    if job is None:
        raise NotFoundError(detail=f"Job posting with id {job_id} not found")
    return job


@router.get("/record/{record_id}", response_model=JobPostingDetail)
async def get_job_by_record_id(service: ServiceDep, record_id: str) -> JobPostingDetail:
    job = await service.get_job_by_record_id(record_id)
    if job is None:
        raise NotFoundError(detail=f"Job posting with record_id '{record_id}' not found")
    return job
