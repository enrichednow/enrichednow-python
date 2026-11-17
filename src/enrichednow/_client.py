"""The two clients: `EnrichedNow` (sync) and `AsyncEnrichedNow` (async), with the same surface."""
from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Iterator, Mapping, Optional, Type

import httpx

from ._base import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RUN_TIMEOUT,
    DEFAULT_TIMEOUT,
    MAX_SERVER_WAIT,
    USE_CLIENT_TIMEOUT,
    BaseClient,
    Timeout,
    clean_params,
    error_from_response,
    error_from_transport,
    parse_json,
)
from ._exceptions import EnrichedNowError
from ._models import Health, Run
from ._pagination import AsyncPaginator, AsyncRecordsPage, SyncRecordsPage
from ._resources import (
    AsyncData,
    AsyncRuns,
    AsyncScrapers,
    AsyncUsageResource,
    Data,
    Runs,
    Scrapers,
    UsageResource,
)

__all__ = ["EnrichedNow", "AsyncEnrichedNow", "ScrapeResult", "AsyncScrapeResult"]


class ScrapeResult:
    """What `client.scrape()` returns: the run as it ended, and its records.

    `records` is fetched page by page as it is iterated; iterating the result itself does the same.
    """

    def __init__(self, client: "EnrichedNow", run: Run) -> None:
        self._client = client
        self.run = run
        self._records: Optional[SyncRecordsPage] = None

    @property
    def records(self) -> SyncRecordsPage:
        """The run's records: iterate for all of them, or use it as the first page."""
        if self._records is None:
            self._records = self._client.runs.records(self.run.id, limit=1000)
        return self._records

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self.records)

    def __repr__(self) -> str:
        return f"ScrapeResult(run={self.run.id!r}, status={self.run.status!r}, record_count={self.run.record_count!r})"


class AsyncScrapeResult:
    """What `await client.scrape()` returns: the run as it ended, and its records (`async for record in result.records`)."""

    def __init__(self, client: "AsyncEnrichedNow", run: Run) -> None:
        self._client = client
        self.run = run

    @property
    def records(self) -> AsyncPaginator[Dict[str, Any], AsyncRecordsPage]:
        """The run's records: `async for` for all of them, or `await` it for the first page."""
        return self._client.runs.records(self.run.id, limit=1000)

    def __aiter__(self) -> Any:
        return self.records.__aiter__()

    def __repr__(self) -> str:
        return f"AsyncScrapeResult(run={self.run.id!r}, status={self.run.status!r}, record_count={self.run.record_count!r})"


def _server_wait(timeout: Optional[float]) -> float:
    return MAX_SERVER_WAIT if timeout is None else max(0.0, min(MAX_SERVER_WAIT, float(timeout)))


class EnrichedNow(BaseClient):
    """The EnrichedNow API.

        client = EnrichedNow()                          # reads ENRICHEDNOW_API_KEY
        result = client.scrape("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})
        for record in result.records:
            print(record)

    `timeout` is the HTTP timeout of one request in seconds (or an `httpx.Timeout`). `max_retries` is how many times
    a request that failed in a way worth retrying is sent again. `http_client` is your own `httpx.Client`, for a
    custom transport or TLS settings; the library does not close a client it did not create.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(follow_redirects=False)
        self._sleep: Callable[[float], None] = time.sleep
        self.scrapers = Scrapers(self)
        self.runs = Runs(self)
        self.usage = UsageResource(self)
        self.data = Data(self)

    # --- transport ------------------------------------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        idempotent: bool = True,
        timeout: Any = USE_CLIENT_TIMEOUT,
    ) -> Any:
        headers = self._headers
        attempt = 0
        while True:
            error: EnrichedNowError
            try:
                response = self._http.request(
                    method,
                    self._url(path),
                    params=clean_params(params),
                    json=json,
                    headers=headers,
                    timeout=self.timeout if timeout is USE_CLIENT_TIMEOUT else timeout,
                )
            except httpx.TransportError as exc:
                error = error_from_transport(exc)
                error.__cause__ = exc
            else:
                if response.is_success:
                    return parse_json(response)
                error = error_from_response(response)
            delay = self._retry_delay(error, attempt=attempt, idempotent=idempotent)
            if delay is None:
                raise error
            self._sleep(delay)
            attempt += 1

    def close(self) -> None:
        """Close the connections. Not needed when the client is used as a context manager."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "EnrichedNow":
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]) -> None:
        self.close()

    # --- the service ----------------------------------------------------------------------------------------------

    def health(self) -> Health:
        """`GET /v1/health`: is the service up."""
        return Health.from_dict(self._request("GET", "/v1/health"))

    def scrape(
        self,
        scraper_id: str,
        input: Mapping[str, Any],
        *,
        timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        raise_on_failure: bool = True,
    ) -> ScrapeResult:
        """Start a run, wait for it to end, and return it with its records.

        Raises `RunFailedError` when the run ends `failed`, `unsupported` or `cancelled` (pass
        `raise_on_failure=False` to get the result instead), and `WaitTimeoutError` when it has not ended after
        `timeout` seconds (`None`: wait as long as it takes). A run that ends `partial` is returned: it has records.
        """
        started = time.monotonic()
        run = self.scrapers.run(scraper_id, input, wait=_server_wait(timeout))
        if run.is_active:
            remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - started))
            run = self.runs.wait(run.id, timeout=remaining, poll_interval=poll_interval)
        if raise_on_failure:
            run.raise_for_status()
        return ScrapeResult(self, run)


class AsyncEnrichedNow(BaseClient):
    """The EnrichedNow API, for `asyncio`. The same surface as `EnrichedNow`; every call is awaited.

        async with AsyncEnrichedNow() as client:
            result = await client.scrape("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})
            async for record in result.records:
                print(record)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries)
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(follow_redirects=False)
        self._sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
        self.scrapers = AsyncScrapers(self)
        self.runs = AsyncRuns(self)
        self.usage = AsyncUsageResource(self)
        self.data = AsyncData(self)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        idempotent: bool = True,
        timeout: Any = USE_CLIENT_TIMEOUT,
    ) -> Any:
        headers = self._headers
        attempt = 0
        while True:
            error: EnrichedNowError
            try:
                response = await self._http.request(
                    method,
                    self._url(path),
                    params=clean_params(params),
                    json=json,
                    headers=headers,
                    timeout=self.timeout if timeout is USE_CLIENT_TIMEOUT else timeout,
                )
            except httpx.TransportError as exc:
                error = error_from_transport(exc)
                error.__cause__ = exc
            else:
                if response.is_success:
                    return parse_json(response)
                error = error_from_response(response)
            delay = self._retry_delay(error, attempt=attempt, idempotent=idempotent)
            if delay is None:
                raise error
            await self._sleep(delay)
            attempt += 1

    async def close(self) -> None:
        """Close the connections. Not needed when the client is used as a context manager."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> "AsyncEnrichedNow":
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]) -> None:
        await self.close()

    async def health(self) -> Health:
        """`GET /v1/health`: is the service up."""
        return Health.from_dict(await self._request("GET", "/v1/health"))

    async def scrape(
        self,
        scraper_id: str,
        input: Mapping[str, Any],
        *,
        timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        raise_on_failure: bool = True,
    ) -> AsyncScrapeResult:
        """Start a run, wait for it to end, and return it with its records.

        Raises `RunFailedError` when the run ends `failed`, `unsupported` or `cancelled` (pass
        `raise_on_failure=False` to get the result instead), and `WaitTimeoutError` when it has not ended after
        `timeout` seconds (`None`: wait as long as it takes). A run that ends `partial` is returned: it has records.
        """
        started = time.monotonic()
        run = await self.scrapers.run(scraper_id, input, wait=_server_wait(timeout))
        if run.is_active:
            remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - started))
            run = await self.runs.wait(run.id, timeout=remaining, poll_interval=poll_interval)
        if raise_on_failure:
            run.raise_for_status()
        return AsyncScrapeResult(self, run)
