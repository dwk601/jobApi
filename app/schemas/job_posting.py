from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class JobPostingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: str
    source: str
    title: str | None
    company: str | None
    location: dict | None
    salary: dict | None
    language: str | None
    post_date: date | None
    link: str | None
    job_category: dict | list | None


class JobPostingDetail(JobPostingSummary):
    model_config = ConfigDict(from_attributes=True)

    company_inferred: bool
    description: str | None
    description_length: int | None
    contact: str | None
    post_date_raw: str | None
    scraped_at: datetime
    meta: dict | list | None
    created_at: datetime
    updated_at: datetime


class JobPostingListResponse(BaseModel):
    items: list[JobPostingSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobPostingQueryParams(BaseModel):
    source: Annotated[str | None, Field(description="Filter by job source")]
    company: Annotated[str | None, Field(description="Filter by company name (case-insensitive)")]
    company_inferred: Annotated[bool | None, Field(description="Filter by inferred company flag")]
    language: Annotated[str | None, Field(description="Filter by job language")]
    q: Annotated[
        str | None, Field(description="Full-text search across title, description, company")
    ]
    location_city: Annotated[str | None, Field(description="Filter by city in location JSONB")]
    location_state: Annotated[str | None, Field(description="Filter by state in location JSONB")]
    salary_min: Annotated[float | None, Field(description="Minimum salary from salary JSONB")]
    salary_max: Annotated[float | None, Field(description="Maximum salary from salary JSONB")]
    job_category: Annotated[str | None, Field(description="Filter by job category slug")]
    post_date_from: Annotated[date | None, Field(description="Filter by post date (from)")]
    post_date_to: Annotated[date | None, Field(description="Filter by post date (to)")]
    sort_by: Annotated[str, Field(default="post_date", description="Sort field")]
    sort_order: Annotated[str, Field(default="desc", description="Sort order: asc or desc")]
    page: Annotated[int, Field(default=1, ge=1, description="Page number")]
    page_size: Annotated[int, Field(default=20, ge=1, le=100, description="Items per page")]


class CategoryCount(BaseModel):
    name: str
    count: int


class JobPostingStats(BaseModel):
    total_jobs: int
    by_source: list[CategoryCount]
    by_language: list[CategoryCount]
    by_company: list[CategoryCount]
    salary_stats: dict | None
