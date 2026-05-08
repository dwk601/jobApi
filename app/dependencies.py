from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.job_posting import JobPostingRepository
from app.services.job_posting import JobPostingService

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


def get_repository(db: DatabaseDep) -> JobPostingRepository:
    return JobPostingRepository(db)


RepositoryAnnotated = Annotated[JobPostingRepository, Depends(get_repository)]


def get_service(repo: RepositoryAnnotated) -> JobPostingService:
    return JobPostingService(repo)


RepositoryDep = Annotated[JobPostingRepository, Depends(get_repository)]
ServiceDep = Annotated[JobPostingService, Depends(get_service)]
