"""What the sync and the async client share: configuration, building a request, reading an error, deciding on a retry."""
from __future__ import annotations

import email.utils
import os
import random
import time
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Mapping, Optional, Type, TypeVar, Union
from urllib.parse import quote

import httpx

from ._exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AttestationRequiredError,
    AuthenticationError,
    EnrichedNowError,
    FormulaUnavailableError,
    MissingAPIKeyError,
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    PlanLimitReachedError,
    LimitReachedError,
    QuotaExceededError,
    RateLimitError,
    RequirementMissingError,
    SavedFormulaArchivedError,
    ServerError,
    ValidationError,
)
from ._models import RECORD_FORMATS, RecordsExport, Standing
from ._pagination import _Page
from ._version import __version__

DEFAULT_BASE_URL = "https://api.enrichednow.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
API_KEY_ENV = "ENRICHEDNOW_API_KEY"
BASE_URL_ENV = "ENRICHEDNOW_BASE_URL"

MAX_SERVER_WAIT = 300.0            # the most `wait` the API accepts, on starting a run and on reading one
SCRAPE_SERVER_WAIT = 60.0          # what `scrape()` asks the API to hold a request for, before it polls
WAIT_HEADROOM = 30.0               # how much longer than `wait` the HTTP request itself may take
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_RUN_TIMEOUT = 600.0

INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
MAX_RETRY_AFTER = 60.0             # a longer Retry-After is not waited for: the error is raised

Timeout = Union[float, httpx.Timeout, None]
USE_CLIENT_TIMEOUT: Any = object()   # "no timeout of its own": the request takes the client's
Params = Dict[str, Any]
P = TypeVar("P", bound="_Page[Any]")


def path_segment(value: str) -> str:
    """A value as one segment of a path: an id with a `/` in it never reaches another address."""
    if not isinstance(value, str) or not value:
        raise ValueError("an id must be a non-empty string")
    return quote(value, safe="")


def query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return ",".join(str(item) for item in value)
    return value


def clean_params(params: Optional[Mapping[str, Any]]) -> Optional[Params]:
    """Query parameters as sent: what is `None` is left out, booleans are `true`/`false`, dates are ISO 8601."""
    if not params:
        return None
    return {name: query_value(value) for name, value in params.items() if value is not None} or None


def posting_params(
    *,
    company_domain: Optional[str] = None,
    title: Optional[str],
    location: Optional[str],
    country: Optional[str],
    remote: Optional[bool],
    employment_type: Optional[str],
    seniority: Optional[str],
    function: Optional[str],
    status: Optional[str],
    source: Optional[str],
    provenance: Any,
    unmatched: Optional[bool],
    posted_from: Any,
    posted_to: Any,
    first_seen_from: Any,
    first_seen_to: Any,
    last_seen_from: Any,
    last_seen_to: Any,
    sort: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Params:
    return {
        "company_domain": company_domain, "title": title, "location": location, "country": country, "remote": remote,
        "employment_type": employment_type, "seniority": seniority, "function": function, "status": status,
        "source": source, "provenance": provenance, "unmatched": unmatched, "posted_from": posted_from,
        "posted_to": posted_to, "first_seen_from": first_seen_from, "first_seen_to": first_seen_to,
        "last_seen_from": last_seen_from, "last_seen_to": last_seen_to, "sort": sort, "limit": limit, "cursor": cursor,
    }


def build_page(cls: Type[P], payload: Any, key: str, convert: Optional[Callable[[Any], Any]], fetch: Callable[[Optional[str]], Any]) -> P:
    data: Dict[str, Any] = dict(payload) if isinstance(payload, Mapping) else {}
    rows = data.get(key)
    items: List[Any] = [convert(row) if convert else row for row in rows] if isinstance(rows, list) else []
    cursor = data.get("next_cursor")
    page = cls(items, cursor if isinstance(cursor, str) and cursor else None, data)
    page._fetch = fetch  # type: ignore[attr-defined]
    if "expired" in data and hasattr(page, "expired"):
        page.expired = bool(data["expired"])
    return page


def _retry_after(response: httpx.Response) -> Optional[float]:
    value = response.headers.get("retry-after")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, when.timestamp() - time.time())


_CONFLICTS: Dict[str, Type[ConflictError]] = {
    "attestation_required": AttestationRequiredError,
    "formula_unavailable": FormulaUnavailableError,
    "requirement_missing": RequirementMissingError,
    "saved_formula_archived": SavedFormulaArchivedError,
}
"""The 409s that have an error of their own; any other 409 (`idempotency_conflict`) is a `ConflictError`."""


def error_from_response(response: httpx.Response) -> APIError:
    """The typed error for an answer of 4xx or 5xx. The API's errors are `{"error": {"code", "message", "details"}}`."""
    body: Any
    try:
        body = response.json()
    except ValueError:
        body = response.text
    error = body.get("error") if isinstance(body, Mapping) else None
    code = message = None
    details: Mapping[str, Any] = {}
    if isinstance(error, Mapping):
        code = error.get("code") if isinstance(error.get("code"), str) else None
        message = error.get("message") if isinstance(error.get("message"), str) else None
        if isinstance(error.get("details"), Mapping):
            details = error["details"]
    status = response.status_code
    common: Dict[str, Any] = {
        "status_code": status,
        "code": code,
        "details": details,
        "request_id": response.headers.get("x-request-id") or response.headers.get("request-id"),
        "body": body,
        "response": response,
    }
    text = message or f"The API answered {status} {response.reason_phrase}".rstrip() + "."
    if status == 401:
        return AuthenticationError(text, **common)
    if status == 403:
        return (PlanLimitReachedError if code == "plan_limit_reached" else PermissionDeniedError)(text, **common)
    if status == 404:
        return NotFoundError(text, **common)
    if status == 409:
        return _CONFLICTS.get(code or "", ConflictError)(text, **common)
    if status == 429:
        return RateLimitError(text, retry_after=_retry_after(response), **common)
    if status == 402:
        return (LimitReachedError if code == "limit_reached" else QuotaExceededError)(text, **common)
    if 400 <= status < 500:
        return ValidationError(text, **common)
    if status >= 500:
        return ServerError(text, **common)
    return APIError(text, **common)


def error_from_transport(exc: httpx.TransportError) -> APIConnectionError:
    request: Optional[httpx.Request]
    try:
        request = exc.request
    except RuntimeError:
        request = None
    if isinstance(exc, httpx.TimeoutException):
        return APITimeoutError(request=request)
    return APIConnectionError(f"Could not reach the EnrichedNow API: {exc}" if str(exc) else "Could not reach the EnrichedNow API.",
                              request=request)


class BaseClient:
    """Configuration and policy. Neither sends anything: `EnrichedNow` and `AsyncEnrichedNow` do."""

    def __init__(self, *, api_key: Optional[str], base_url: Optional[str], timeout: Timeout, max_retries: int) -> None:
        key = api_key if api_key is not None else os.environ.get(API_KEY_ENV)
        if not key or not key.strip():
            raise MissingAPIKeyError(
                f"No API key. Pass api_key=... or set the {API_KEY_ENV} environment variable. "
                "Create a key in the console under API keys; it starts with en_live_."
            )
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise ValueError("max_retries must be a whole number, 0 or more")
        self.api_key = key.strip()
        self.base_url = (base_url or os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/")
        self.timeout: Timeout = timeout
        self.max_retries = max_retries
        self._standing: Optional[Standing] = None

    @property
    def standing(self) -> Optional[Standing]:
        """Where the account stood at the last answer that said so: every answer about runs carries the account's
        units and runs in progress in its headers. `None` until such an answer has come; `usage.standing()` asks."""
        return self._standing

    def _note(self, response: httpx.Response) -> None:
        standing = Standing.from_headers(response.headers)
        if standing is not None:
            self._standing = standing

    def __repr__(self) -> str:
        return f"{type(self).__name__}(base_url={self.base_url!r}, api_key='{self.api_key[:8]}…')"

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": f"enrichednow-python/{__version__}",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _timeout_for(self, wait: Optional[float]) -> Timeout:
        """The HTTP timeout of a request the API holds open for `wait` seconds: never shorter than the hold."""
        if not wait:
            return self.timeout
        needed = float(wait) + WAIT_HEADROOM
        current = self.timeout
        if current is None:
            return None
        if isinstance(current, httpx.Timeout):
            if current.read is None or current.read >= needed:
                return current
            return httpx.Timeout(connect=current.connect, read=needed, write=current.write, pool=current.pool)
        return max(float(current), needed)

    # --- retries ----------------------------------------------------------------------------------------------------

    def _backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter: about 0.5 s, 1 s, 2 s, … up to 8 s; each between half of that and all of it."""
        ceiling: float = min(MAX_RETRY_DELAY, INITIAL_RETRY_DELAY * float(2 ** attempt))
        return ceiling * (0.5 + random.random() / 2)

    def _retry_delay(self, error: EnrichedNowError, *, attempt: int, idempotent: bool) -> Optional[float]:
        """Seconds to wait before sending the request again, or `None` to raise the error.

        Retried: a connection that failed, a timeout, 429 and 5xx. A request that is not safe to repeat (starting a
        run) is sent again only when it is certain that the API did not act on it: the connection was never made, or
        the answer was 429 (no run was created).
        """
        if attempt >= self.max_retries:
            return None
        if isinstance(error, APIConnectionError):
            cause = error.__cause__
            never_sent = isinstance(cause, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout))
            return self._backoff(attempt) if idempotent or never_sent else None
        if isinstance(error, RateLimitError):
            if error.retry_after is None:
                return self._backoff(attempt)
            return error.retry_after if error.retry_after <= MAX_RETRY_AFTER else None
        if isinstance(error, ServerError):
            if not idempotent:
                return None
            retry_after = _retry_after(error.response) if error.response is not None else None
            if retry_after is not None:
                return retry_after if retry_after <= MAX_RETRY_AFTER else None
            return self._backoff(attempt)
        return None


def parse_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        raise APIError(
            "The API answered with something that is not JSON.",
            status_code=response.status_code,
            body=response.text,
            response=response,
        ) from None


def validate_format(format: str) -> str:
    if format not in RECORD_FORMATS:
        raise ValueError(f"format must be one of {', '.join(RECORD_FORMATS)}; for JSON use client.runs.records")
    return format


def records_export(format: str, response: httpx.Response) -> RecordsExport:
    return RecordsExport(format=format, content=response.content, next_cursor=response.headers.get("x-next-cursor") or None,
                         expired=response.headers.get("x-records-expired") == "true")


def without_header(chunk: bytes) -> bytes:
    """A CSV page after the first, without the header row every page starts with (the columns are the same)."""
    end = chunk.find(b"\n")
    return b"" if end < 0 else chunk[end + 1:]


def validate_wait(wait: Optional[float]) -> Optional[float]:
    if wait is None:
        return None
    if isinstance(wait, bool) or not isinstance(wait, (int, float)) or not 0 <= wait <= MAX_SERVER_WAIT:
        raise ValueError(f"wait must be a number of seconds from 0 to {MAX_SERVER_WAIT:g}")
    return wait
