"""The official Python library for the EnrichedNow API.

    from enrichednow import EnrichedNow

    client = EnrichedNow()                              # reads ENRICHEDNOW_API_KEY
    result = client.scrape("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})
    for record in result.records:
        print(record)
"""
from ._client import AsyncEnrichedNow, AsyncScrapeResult, EnrichedNow, ScrapeResult
from ._exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    EnrichedNowError,
    MissingAPIKeyError,
    NotFoundError,
    PermissionDeniedError,
    QuotaExceededError,
    RateLimitError,
    RunFailedError,
    ServerError,
    ValidationError,
    WaitTimeoutError,
)
from ._models import (
    Change,
    Classification,
    Company,
    CompanyName,
    CompanyRef,
    Event,
    Health,
    History,
    LastRead,
    Location,
    Model,
    Period,
    Posting,
    PostingCounts,
    PostingDetail,
    Run,
    RunDiagnostics,
    Salary,
    Scraper,
    ScraperDetails,
    Sightings,
    Source,
    Usage,
    UsageRow,
)
from ._pagination import AsyncPage, AsyncPaginator, AsyncRecordsPage, SyncPage, SyncRecordsPage
from ._version import __version__

__all__ = [
    "__version__",
    # clients
    "EnrichedNow",
    "AsyncEnrichedNow",
    "ScrapeResult",
    "AsyncScrapeResult",
    # errors
    "EnrichedNowError",
    "MissingAPIKeyError",
    "APIConnectionError",
    "APITimeoutError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "QuotaExceededError",
    "ServerError",
    "RunFailedError",
    "WaitTimeoutError",
    # pagination
    "SyncPage",
    "AsyncPage",
    "SyncRecordsPage",
    "AsyncRecordsPage",
    "AsyncPaginator",
    # models
    "Model",
    "Health",
    "Scraper",
    "ScraperDetails",
    "Run",
    "RunDiagnostics",
    "Usage",
    "UsageRow",
    "Period",
    "Posting",
    "PostingDetail",
    "Company",
    "CompanyName",
    "CompanyRef",
    "Location",
    "Salary",
    "Source",
    "Classification",
    "History",
    "Event",
    "Change",
    "Sightings",
    "LastRead",
    "PostingCounts",
]
