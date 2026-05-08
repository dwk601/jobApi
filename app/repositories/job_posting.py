from __future__ import annotations

from sqlalchemy import Float, String, func, or_, select, text
from sqlalchemy import cast as sa_cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ALLOWED_SORT_FIELDS, MAX_PAGE_SIZE
from app.models.job_posting import JobPosting
from app.schemas.job_posting import CategoryCount, JobPostingQueryParams, JobPostingStats


class JobPostingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(
        self,
        params: JobPostingQueryParams,
    ) -> tuple[list[JobPosting], int]:
        page = params.page
        page_size = min(params.page_size, MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        count_query = select(func.count()).select_from(JobPosting)
        query = select(JobPosting)

        count_query = self._apply_filters(count_query, params)
        query = self._apply_filters(query, params)

        total = await self.db.scalar(count_query) or 0

        query = self._apply_sorting(query, params)
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def find_by_id(self, job_id: int) -> JobPosting | None:
        result = await self.db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        return result.scalar_one_or_none()

    async def find_by_record_id(self, record_id: str) -> JobPosting | None:
        result = await self.db.execute(
            select(JobPosting).where(JobPosting.record_id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_distinct_sources(self) -> list[str]:
        result = await self.db.execute(
            select(JobPosting.source).distinct().order_by(JobPosting.source)
        )
        return [row[0] for row in result.all()]

    async def get_stats(self) -> JobPostingStats:
        total_result = await self.db.scalar(select(func.count()).select_from(JobPosting))
        total = total_result or 0

        source_result = await self.db.execute(
            select(JobPosting.source, func.count())
            .group_by(JobPosting.source)
            .order_by(func.count().desc())
            .limit(10)
        )
        by_source = [CategoryCount(name=row[0], count=row[1]) for row in source_result.all()]

        lang_result = await self.db.execute(
            select(JobPosting.language, func.count())
            .where(JobPosting.language.isnot(None))
            .group_by(JobPosting.language)
            .order_by(func.count().desc())
        )
        by_language = [CategoryCount(name=row[0], count=row[1]) for row in lang_result.all()]

        company_result = await self.db.execute(
            select(JobPosting.company, func.count())
            .where(JobPosting.company.isnot(None))
            .group_by(JobPosting.company)
            .order_by(func.count().desc())
            .limit(20)
        )
        by_company = [CategoryCount(name=row[0], count=row[1]) for row in company_result.all()]

        salary_result = await self.db.execute(
            text(
                """
                SELECT
                    MIN((salary ->> 'min')::FLOAT) FILTER (WHERE (salary ->> 'min') IS NOT NULL),
                    MAX((salary ->> 'max')::FLOAT) FILTER (WHERE (salary ->> 'max') IS NOT NULL),
                    AVG((salary ->> 'min')::FLOAT),
                    AVG((salary ->> 'max')::FLOAT)
                FROM job_postings
                WHERE salary IS NOT NULL
                """
            )
        )
        salary_row = salary_result.one_or_none()
        salary_stats = None
        if salary_row and any(v is not None for v in salary_row):
            salary_stats = {
                "min_salary_min": salary_row[0],
                "min_salary_max": salary_row[1],
                "avg_salary_min": float(salary_row[2]) if salary_row[2] else None,
                "avg_salary_max": float(salary_row[3]) if salary_row[3] else None,
            }

        return JobPostingStats(
            total_jobs=total,
            by_source=by_source,
            by_language=by_language,
            by_company=by_company,
            salary_stats=salary_stats,
        )

    def _apply_filters(self, stmt, params: JobPostingQueryParams):
        if params.source:
            stmt = stmt.where(JobPosting.source == params.source)
        if params.company:
            stmt = stmt.where(JobPosting.company.ilike(f"%{params.company}%"))
        if params.company_inferred is not None:
            stmt = stmt.where(JobPosting.company_inferred == params.company_inferred)
        if params.language:
            stmt = stmt.where(JobPosting.language == params.language)
        if params.location_city:
            stmt = stmt.where(
                sa_cast(JobPosting.location["city"], String).ilike(f"%{params.location_city}%")
            )
        if params.location_state:
            stmt = stmt.where(
                sa_cast(JobPosting.location["state"], String).ilike(f"%{params.location_state}%")
            )
        if params.salary_min is not None:
            stmt = stmt.where(
                JobPosting.salary.isnot(None),
                sa_cast(JobPosting.salary["max"].as_string(), Float)
                >= params.salary_min,
            )
        if params.salary_max is not None:
            stmt = stmt.where(
                JobPosting.salary.isnot(None),
                sa_cast(JobPosting.salary["min"].as_string(), Float)
                <= params.salary_max,
            )
        if params.job_category:
            stmt = stmt.where(
                sa_cast(JobPosting.job_category["slug"], String) == params.job_category
            )
        if params.post_date_from:
            stmt = stmt.where(JobPosting.post_date >= params.post_date_from)
        if params.post_date_to:
            stmt = stmt.where(JobPosting.post_date <= params.post_date_to)
        if params.q:
            search_term = params.q
            stmt = stmt.where(
                or_(
                    JobPosting.title.op("%")(search_term),
                    JobPosting.description.op("%")(search_term),
                    JobPosting.company.op("%")(search_term),
                )
            )
        return stmt

    def _apply_sorting(self, stmt, params: JobPostingQueryParams):
        sort_by = params.sort_by
        sort_order = params.sort_order

        if params.q:
            relevance = func.greatest(
                func.similarity(JobPosting.title, params.q),
                func.similarity(JobPosting.description, params.q),
                func.similarity(JobPosting.company, params.q),
            )
            return stmt.order_by(relevance.desc())
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = "post_date"
        if sort_order not in ("asc", "desc"):
            sort_order = "desc"

        col = getattr(JobPosting, sort_by)
        return stmt.order_by(col.desc() if sort_order == "desc" else col.asc())
