# Job API

A read-only, public REST API for searching and browsing Korean/US job postings, backed by PostgreSQL with Redis caching and rate limiting.

## Features

- **Full-text search** across title, description, and company via PostgreSQL trigram indexes (`pg_trgm`)
- **Rich filtering** — source, company, language, location, salary range, job category, date range
- **Sorting** by any allowed field (relevance-based when searching, `post_date` default)
- **Paginated responses** (1–100 items per page)
- **Redis read-through caching** with configurable TTLs per endpoint type
- **IP-based rate limiting** (60 req/min window, sliding-window counter in Redis)
- **Dockerized** with a multi-stage build and non-root runtime user

## Tech Stack

| Layer          | Technology                                  |
|----------------|---------------------------------------------|
| Web framework  | FastAPI (Python 3.12+)                      |
| Database       | PostgreSQL 15+ with `asyncpg` driver        |
| ORM            | SQLAlchemy 2.0 (async)                      |
| Cache / Rate   | Redis 7+ with `hiredis`                     |
| Migrations     | Alembic (async)                             |
| Validation     | Pydantic v2 + pydantic-settings             |
| Package mgmt   | `uv`                                        |

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+

### Local Development

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd jobApi

# 2. Copy and edit environment variables
cp .env.example .env
# Set DATABASE_URL and REDIS_URL in .env

# 3. Install dependencies with uv
uv sync

# 4. Run migrations
uv run alembic upgrade head

# 5. Start the server
uv run fastapi run --host 0.0.0.0 --port 8000
```

The API is now available at `http://localhost:8000`. Open `http://localhost:8000/docs` for the interactive Swagger UI.

### Docker

```bash
docker build -t job-api .
docker run -p 8000:8000 --env-file .env job-api
```

The container runs as a non-root `appuser`, exposes port 8000, and includes a healthcheck on `/health` every 30 seconds.

## API Reference

Base URL: `http://localhost:8000`

### Health

```
GET /health
```

Returns `{"status": "ok"}`.

### Job Postings

All job endpoints are under `/api/v1/jobs`.

#### List Jobs

```
GET /api/v1/jobs/
```

Query parameters:

| Parameter         | Type    | Default       | Description                                      |
|-------------------|---------|---------------|--------------------------------------------------|
| `source`          | string  | —             | Filter by job source                             |
| `company`         | string  | —             | Filter by company name                           |
| `company_inferred`| bool    | —             | Filter by inferred company flag                  |
| `language`        | string  | —             | Filter by language (`ko`, `en`, etc.)            |
| `q`               | string  | —             | Trigram full-text search on title, description, company |
| `location_city`   | string  | —             | Filter by city                                   |
| `location_state`  | string  | —             | Filter by state                                  |
| `salary_min`      | float   | —             | Minimum salary                                   |
| `salary_max`      | float   | —             | Maximum salary                                   |
| `job_category`    | string  | —             | Filter by job category slug                      |
| `post_date_from`  | date    | —             | Post date lower bound (`YYYY-MM-DD`)             |
| `post_date_to`    | date    | —             | Post date upper bound (`YYYY-MM-DD`)             |
| `sort_by`         | string  | `post_date`   | Field to sort by (see allowed fields below)      |
| `sort_order`      | string  | `desc`        | Sort direction (`asc` or `desc`)                 |
| `page`            | int     | `1`           | Page number (≥1)                                 |
| `page_size`       | int     | `20`          | Items per page (1–100)                           |

When `q` is provided, sorting switches to relevance (trigram similarity). If `sort_by` is not an allowed field, it falls back to `post_date`.

Allowed sort fields: `id`, `title`, `company`, `post_date`, `created_at`, `updated_at`, `source`, `language`, `description_length`.

Response (`JobPostingListResponse`):

```json
{
  "items": [{ "id": 1, "title": "...", "company": "...", ... }],
  "total": 1500,
  "page": 1,
  "page_size": 20,
  "total_pages": 75
}
```

#### Get Job by ID

```
GET /api/v1/jobs/{job_id}
```

Returns full job detail including `description`, `contact`, `meta`, timestamps, etc.

#### Get Job by Record ID

```
GET /api/v1/jobs/record/{record_id}
```

Same response as above, looked up by the unique `record_id` string.

#### Stats

```
GET /api/v1/jobs/stats
```

Returns aggregated counts and salary statistics:

```json
{
  "total_jobs": 50000,
  "by_source": { "saramin": 20000, "wanted": 15000, ... },
  "by_language": { "ko": 35000, "en": 15000 },
  "by_company": { "Samsung": 500, "Naver": 400, ... },
  "salary_stats": { "min_salary": 24000, "max_salary": 250000, "avg_salary": 85000 }
}
```

### Rate Limiting

Rate limit: **60 requests per 60-second window** per client IP. Exceeding returns HTTP 429 with a `Retry-After` header. Rate limiting is controlled by `RATE_LIMIT_ENABLED` in `.env`.

## Configuration

All settings are loaded from environment variables via `.env`.

| Variable                    | Default                                                  | Description                        |
|-----------------------------|----------------------------------------------------------|------------------------------------|
| `APP_NAME`                  | `Job API`                                                | FastAPI app title                  |
| `DEBUG`                     | `false`                                                  | Debug mode                         |
| `DATABASE_URL`              | `postgresql+asyncpg://postgres:postgres@localhost:5432/jobs` | PostgreSQL connection string   |
| `REDIS_URL`                 | `redis://localhost:6379/0`                               | Redis connection string            |
| `REDIS_MAX_CONNECTIONS`     | `10`                                                     | Redis connection pool size         |
| `REDIS_SOCKET_TIMEOUT`      | `5`                                                      | Redis socket timeout (seconds)     |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | `5`                                                   | Redis connect timeout (seconds)    |
| `RATE_LIMIT_ENABLED`        | `true`                                                   | Enable/disable rate limiting       |

Supports TLS Redis via `rediss://` scheme (e.g., Upstash, Redis Cloud).

## Architecture

```
Request → RateLimitMiddleware → CORSMiddleware → Router → Service → Repository → DB
                                                    ↓
                                                 Redis Cache (read-through)
```

### Layers

- **Routers** — HTTP handlers, parameter parsing, response marshalling
- **Services** — business logic, cache orchestration
- **Repositories** — SQLAlchemy queries, filtering, sorting, pagination
- **Middleware** — CORS (wide open), IP-based rate limiting

The service and repository are wired via FastAPI's dependency injection chain: `get_db() → get_repository() → get_service() → router`.

### Caching

Read-through Redis cache with TTLs: lists=60s, detail=300s, stats=120s. Cache keys use SHA-256 hashes of query parameters for list endpoints and simple `job:id:{n}` / `job:rid:{id}` keys for direct lookups. Redis unavailability is handled gracefully — the service falls back to direct DB queries.

## Project Structure

```
jobApi/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, router registration
│   ├── config.py                # Pydantic settings from env vars
│   ├── constants.py             # Limits, defaults, sort fields, sources
│   ├── database.py              # Async SQLAlchemy engine + session
│   ├── dependencies.py          # DI chain (db → repo → service)
│   ├── exceptions.py            # Custom exceptions + global handlers
│   ├── redis_client.py          # Lazy-init Redis connection pool
│   ├── middleware/
│   │   └── rate_limit.py        # IP-based sliding-window rate limiter
│   ├── models/
│   │   └── job_posting.py       # JobPosting ORM model
│   ├── schemas/
│   │   └── job_posting.py       # Pydantic request/response models
│   ├── routers/
│   │   └── job_postings.py      # /api/v1/jobs/* endpoints
│   ├── services/
│   │   └── job_posting.py       # Business logic + cache orchestration
│   └── repositories/
│       └── job_posting.py       # SQL queries, filtering, sorting
├── alembic/
│   ├── env.py                   # Async Alembic environment
│   └── versions/
│       └── 001_initial_job_postings.py
├── scripts/
│   └── entrypoint.sh            # Docker entrypoint (stamp + run)
├── Dockerfile                   # Multi-stage build (uv + Python 3.12-slim)
├── pyproject.toml               # Project metadata, deps, tool config
├── alembic.ini
└── .env.example
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Lint
uv run ruff check .
```
