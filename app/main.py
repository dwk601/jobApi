from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import http_exception_handler, unhandled_exception_handler
from app.middleware.rate_limit import RateLimitMiddleware
from app.redis_client import redis_client
from app.routers import job_postings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(job_postings.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
