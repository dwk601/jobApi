DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

CACHE_TTL_LIST = 60
CACHE_TTL_DETAIL = 300
CACHE_TTL_STATS = 120

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 60

ALLOWED_SORT_FIELDS = {
    "id",
    "title",
    "company",
    "post_date",
    "created_at",
    "updated_at",
    "source",
    "language",
    "description_length",
}

SUPPORTED_SOURCES = {
    "saramin",
    "wanted",
    "jobplanet",
    "programmers",
    "jumpit",
    "linkedin",
    "indeed",
    "glassdoor",
    "rocketpunch",
    "remember",
}
