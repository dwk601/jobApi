from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    company_inferred: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[dict | None] = mapped_column(JSON)
    salary: Mapped[dict | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    description_length: Mapped[int | None] = mapped_column(Integer)
    job_category: Mapped[dict | None] = mapped_column(JSON)
    language: Mapped[str | None] = mapped_column(String(20))
    post_date: Mapped[date | None] = mapped_column(Date)
    post_date_raw: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(Text)
    contact: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
