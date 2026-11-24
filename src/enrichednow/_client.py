"""The two clients: `EnrichedNow` (sync) and `AsyncEnrichedNow` (async), with the same surface."""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from types import TracebackType
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Iterator, Mapping, Optional, Type, Union, cast

import httpx

from ._base import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RUN_TIMEOUT,
    DEFAULT_TIMEOUT,
    SCRAPE_SERVER_WAIT,
    USE_CLIENT_TIMEOUT,
    BaseClient,
    Timeout,
    clean_params,
    error_from_response,
    error_from_transport,
    parse_json,
)
from ._exceptions import EnrichedNowError
from ._formulas import (
    ROWS_PAGE,
    AsyncAttestations,
    AsyncFormulaRows,
    AsyncFormulaRuns,
    AsyncFormulas,
    AsyncSavedFormulas,
    AsyncSuppressions,
    Attestations,
    Fields,
    FormulaRows,
    FormulaRuns,
    Formulas,
    Params,
    RowFormat,
    RowView,
    SavedFormulas,
    Suppressions,
)
from ._models import FormulaRow, FormulaRun, Health, Run
from ._pagination import AsyncPage, AsyncPaginator, AsyncRecordsPage, SyncPage, SyncRecordsPage
from ._resources import (
    AsyncData,
    AsyncRuns,
    AsyncScrapers,
    AsyncUsageResource,
    AsyncWebhooks,
    Data,
    Runs,
    Scrapers,
    UsageResource,
    Webhooks,
)

__all__ = ["EnrichedNow", "AsyncEnrichedNow", "ScrapeResult", "AsyncScrapeResult", "FormulaResult", "AsyncFormulaResult"]

_SUFFIXES = {".csv": "csv", ".ndjson": "ndjson", ".jsonl": "ndjson"}


def _download_format(path: "Union[str, os.PathLike[str]]", format: Optional[RowFormat]) -> RowFormat:
    if format is not None:
        return format
    found = _SUFFIXES.get(Path(path).suffix.lower())
    if found is None:
        raise ValueError("give format='csv' or 'ndjson': the file's name does not say which")
    return cast(RowFormat, found)


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


class FormulaResult:
    """What `client.run_formula()` returns: the run as it ended, and its rows.

    Iterating the result walks every row, best first, fetched a page at a time; `rows()` narrows them, `export()` and
    `download()` write the whole run as one CSV or NDJSON file.
    """

    def __init__(self, client: "EnrichedNow", run: FormulaRun) -> None:
        self._client = client
        self.run = run

    def rows(self, *, fields: Optional[Fields] = None, min_score: Optional[float] = None, view: Optional[RowView] = None,
             limit: int = ROWS_PAGE) -> SyncPage[FormulaRow]:
        """The run's rows: iterate for all of them. `fields` keeps those columns, `min_score` the rows scored at least
        that, and `view="company"` gives one row per company (for a formula with a `company_view`)."""
        return self._client.formula_runs.rows(self.run.id, fields=fields, min_score=min_score, view=view, limit=limit)

    def __iter__(self) -> Iterator[FormulaRow]:
        return iter(self.rows())

    def export(self, format: RowFormat = "csv", *, fields: Optional[Fields] = None, min_score: Optional[float] = None,
               view: Optional[RowView] = None) -> Iterator[bytes]:
        """The whole run as `csv` or `ndjson`, written by the API, a page at a time: the pieces make one file."""
        return self._client.formula_runs.export_all(self.run.id, format, fields=fields, min_score=min_score, view=view)

    def download(self, path: "Union[str, os.PathLike[str]]", format: Optional[RowFormat] = None, *, fields: Optional[Fields] = None,
                 min_score: Optional[float] = None, view: Optional[RowView] = None) -> Path:
        """Write the whole run to `path`, as `csv` or `ndjson` (by default, as the file's name says), and return it."""
        chosen = _download_format(path, format)
        with open(path, "wb") as out:
            for chunk in self.export(chosen, fields=fields, min_score=min_score, view=view):
                out.write(chunk)
        return Path(path)

    def __repr__(self) -> str:
        return f"FormulaResult(run={self.run.id!r}, status={self.run.status!r}, rows_total={self.run.rows_total!r})"


class AsyncFormulaResult:
    """What `await client.run_formula()` returns: the run as it ended, and its rows (`async for row in result`)."""

    def __init__(self, client: "AsyncEnrichedNow", run: FormulaRun) -> None:
        self._client = client
        self.run = run

    def rows(self, *, fields: Optional[Fields] = None, min_score: Optional[float] = None, view: Optional[RowView] = None,
             limit: int = ROWS_PAGE) -> AsyncPaginator[FormulaRow, AsyncPage[FormulaRow]]:
        """The run's rows: `async for` over all of them, or await it for the first page; see `FormulaResult.rows`."""
        return self._client.formula_runs.rows(self.run.id, fields=fields, min_score=min_score, view=view, limit=limit)

    def __aiter__(self) -> AsyncIterator[FormulaRow]:
        return self.rows().__aiter__()

    def export(self, format: RowFormat = "csv", *, fields: Optional[Fields] = None, min_score: Optional[float] = None,
               view: Optional[RowView] = None) -> AsyncIterator[bytes]:
        """The whole run as `csv` or `ndjson`, a page at a time (`async for`)."""
        return self._client.formula_runs.export_all(self.run.id, format, fields=fields, min_score=min_score, view=view)

    async def download(self, path: "Union[str, os.PathLike[str]]", format: Optional[RowFormat] = None, *,
                       fields: Optional[Fields] = None, min_score: Optional[float] = None, view: Optional[RowView] = None) -> Path:
        """Write the whole run to `path`, as `csv` or `ndjson` (by default, as the file's name says), and return it."""
        chosen = _download_format(path, format)
        with open(path, "wb") as out:
            async for chunk in self.export(chosen, fields=fields, min_score=min_score, view=view):
                out.write(chunk)
        return Path(path)

    def __repr__(self) -> str:
        return f"AsyncFormulaResult(run={self.run.id!r}, status={self.run.status!r}, rows_total={self.run.rows_total!r})"


def _server_wait(timeout: Optional[float]) -> float:
    return SCRAPE_SERVER_WAIT if timeout is None else max(0.0, min(SCRAPE_SERVER_WAIT, float(timeout)))


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
        self.webhooks = Webhooks(self)
        self.formulas = Formulas(self)
        self.formula_runs = FormulaRuns(self)
        self.saved_formulas = SavedFormulas(self)
        self.suppressions = Suppressions(self)
        self.attestations = Attestations(self)
        self.formula_rows = FormulaRows(self)

    # --- transport ------------------------------------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        idempotent: bool = True,
        timeout: Any = USE_CLIENT_TIMEOUT,
        headers: Optional[Mapping[str, str]] = None,
        raw: bool = False,
    ) -> Any:
        """The answer's JSON (`raw`: the answer itself, for a body that is not JSON). `content` is a body sent as it is."""
        headers = {**self._headers, **headers} if headers else self._headers
        attempt = 0
        while True:
            error: EnrichedNowError
            try:
                response = self._http.request(
                    method,
                    self._url(path),
                    params=clean_params(params),
                    json=json,
                    content=content,
                    headers=headers,
                    timeout=self.timeout if timeout is USE_CLIENT_TIMEOUT else timeout,
                )
            except httpx.TransportError as exc:
                error = error_from_transport(exc)
                error.__cause__ = exc
            else:
                self._note(response)
                if response.is_success:
                    if raw:
                        return response
                    return None if response.status_code == 204 else parse_json(response)
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
        webhook_url: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ScrapeResult:
        """Start a run, wait for it to end, and return it with its records.

        Raises `RunFailedError` when the run ends `failed`, `unsupported` or `cancelled` (pass
        `raise_on_failure=False` to get the result instead), and `WaitTimeoutError` when it has not ended after
        `timeout` seconds (`None`: wait as long as it takes). A run that ends `partial` is returned: it has records.

        `webhook_url` is an `https` URL that is also told when the run ends: see `client.scrapers.run`.
        `idempotency_key` names this call so that it can be repeated without a second run: see `client.scrapers.run`.
        """
        started = time.monotonic()
        run = self.scrapers.run(scraper_id, input, wait=_server_wait(timeout), webhook_url=webhook_url,
                                idempotency_key=idempotency_key)
        if run.is_active:
            remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - started))
            run = self.runs.wait(run.id, timeout=remaining, poll_interval=poll_interval)
        if raise_on_failure:
            run.raise_for_status()
        return ScrapeResult(self, run)

    def run_formula(
        self,
        formula_id: str,
        params: Optional[Params] = None,
        *,
        preview: bool = False,
        unit_cap: Optional[int] = None,
        row_cap: Optional[int] = None,
        timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        raise_on_failure: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> FormulaResult:
        """Run a formula, wait for it to end, and return it with its rows.

            result = client.run_formula("job-order-hunter", {"job_titles": ["Java Developer"], "locations": ["London"]})
            for row in result:
                print(row.data["company_name"], row.data["job_title"])

        `params`, `preview`, `unit_cap`, `row_cap` and `idempotency_key` are those of `client.formulas.run`. Raises
        `FormulaRunFailedError` when the run ends `failed`, `unsupported` or `cancelled` (pass `raise_on_failure=False`
        to get the result instead), and `WaitTimeoutError` when it has not ended after `timeout` seconds (`None`: wait
        as long as it takes). A run that ends `partial` is returned: it has rows, and `run.reasons` says what is missing.
        """
        started = time.monotonic()
        run = self.formulas.run(formula_id, params, preview=preview, unit_cap=unit_cap, row_cap=row_cap, wait=_server_wait(timeout),
                                idempotency_key=idempotency_key)
        if run.is_active:
            remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - started))
            run = self.formula_runs.wait(run.id, timeout=remaining, poll_interval=poll_interval)
        if raise_on_failure:
            run.raise_for_status()
        return FormulaResult(self, run)


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
        self.webhooks = AsyncWebhooks(self)
        self.formulas = AsyncFormulas(self)
        self.formula_runs = AsyncFormulaRuns(self)
        self.saved_formulas = AsyncSavedFormulas(self)
        self.suppressions = AsyncSuppressions(self)
        self.attestations = AsyncAttestations(self)
        self.formula_rows = AsyncFormulaRows(self)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        content: Optional[bytes] = None,
        idempotent: bool = True,
        timeout: Any = USE_CLIENT_TIMEOUT,
        headers: Optional[Mapping[str, str]] = None,
        raw: bool = False,
    ) -> Any:
        """The answer's JSON (`raw`: the answer itself, for a body that is not JSON). `content` is a body sent as it is."""
        headers = {**self._headers, **headers} if headers else self._headers
        attempt = 0
        while True:
            error: EnrichedNowError
            try:
                response = await self._http.request(
                    method,
                    self._url(path),
                    params=clean_params(params),
                    json=json,
                    content=content,
                    headers=headers,
                    timeout=self.timeout if timeout is USE_CLIENT_TIMEOUT else timeout,
                )
            except httpx.TransportError as exc:
                error = error_from_transport(exc)
                error.__cause__ = exc
            else:
                self._note(response)
                if response.is_success:
                    if raw:
                        return response
                    return None if response.status_code == 204 else parse_json(response)
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
        webhook_url: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> AsyncScrapeResult:
        """Start a run, wait for it to end, and return it with its records.

        Raises `RunFailedError` when the run ends `failed`, `unsupported` or `cancelled` (pass
        `raise_on_failure=False` to get the result instead), and `WaitTimeoutError` when it has not ended after
        `timeout` seconds (`None`: wait as long as it takes). A run that ends `partial` is returned: it has records.

        `webhook_url` is an `https` URL that is also told when the run ends: see `client.scrapers.run`.
        `idempotency_key` names this call so that it can be repeated without a second run: see `client.scrapers.run`.
        """
        started = time.monotonic()
        run = await self.scrapers.run(scraper_id, input, wait=_server_wait(timeout), webhook_url=webhook_url,
                                idempotency_key=idempotency_key)
        if run.is_active:
            remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - started))
            run = await self.runs.wait(run.id, timeout=remaining, poll_interval=poll_interval)
        if raise_on_failure:
            run.raise_for_status()
        return AsyncScrapeResult(self, run)

    async def run_formula(
        self,
        formula_id: str,
        params: Optional[Params] = None,
        *,
        preview: bool = False,
        unit_cap: Optional[int] = None,
        row_cap: Optional[int] = None,
        timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        raise_on_failure: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> AsyncFormulaResult:
        """Run a formula, wait for it to end, and return it with its rows (`async for row in result`); see
        `EnrichedNow.run_formula`."""
        started = time.monotonic()
        run = await self.formulas.run(formula_id, params, preview=preview, unit_cap=unit_cap, row_cap=row_cap,
                                      wait=_server_wait(timeout), idempotency_key=idempotency_key)
        if run.is_active:
            remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - started))
            run = await self.formula_runs.wait(run.id, timeout=remaining, poll_interval=poll_interval)
        if raise_on_failure:
            run.raise_for_status()
        return AsyncFormulaResult(self, run)
