"""Everything this library raises.

    EnrichedNowError
    ├── MissingAPIKeyError
    ├── APIConnectionError            the request never got an answer
    │   └── APITimeoutError
    ├── APIError                      the API answered with an error
    │   ├── AuthenticationError       401
    │   │   └── PermissionDeniedError 403
    │   ├── NotFoundError             404
    │   ├── RateLimitError            429
    │   ├── ValidationError           any other 4xx (422 `invalid_input`)
    │   │   └── QuotaExceededError    402
    │   └── ServerError               5xx
    ├── RunFailedError                a run ended failed, unsupported or cancelled
    └── WaitTimeoutError              a run did not end within the time given
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional

import httpx

if TYPE_CHECKING:
    from ._models import Run

__all__ = [
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
]


class EnrichedNowError(Exception):
    """The base of every error this library raises."""


class MissingAPIKeyError(EnrichedNowError):
    """No API key was given and `ENRICHEDNOW_API_KEY` is not set."""


class APIConnectionError(EnrichedNowError):
    """The request did not get an answer: the connection failed or was cut."""

    def __init__(self, message: str = "Could not reach the EnrichedNow API.", *, request: Optional[httpx.Request] = None) -> None:
        super().__init__(message)
        self.message = message
        self.request = request


class APITimeoutError(APIConnectionError):
    """The request did not get an answer in time."""

    def __init__(self, message: str = "The request to the EnrichedNow API timed out.", *, request: Optional[httpx.Request] = None) -> None:
        super().__init__(message, request=request)


class APIError(EnrichedNowError):
    """The API answered with an HTTP status of 4xx or 5xx.

    `code` is the API's stable error code (`not_found`, `invalid_input`, …): match on it. `message` is a sentence for
    a person. `details` is always a dict; what it holds depends on the code.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: Optional[str] = None,
        details: Optional[Mapping[str, Any]] = None,
        request_id: Optional[str] = None,
        body: Any = None,
        response: Optional[httpx.Response] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details: Dict[str, Any] = dict(details or {})
        self.request_id = request_id
        self.body = body
        self.response = response

    @property
    def reason(self) -> Optional[str]:
        """`details.reason`, when the API gives one (e.g. `email_not_verified` on a 403)."""
        value = self.details.get("reason")
        return value if isinstance(value, str) else None

    def __str__(self) -> str:
        head = f"{self.status_code}"
        if self.code:
            head += f" {self.code}"
        text = f"{head}: {self.message}"
        if self.request_id:
            text += f" (request id: {self.request_id})"
        return text


class AuthenticationError(APIError):
    """401: the API key is missing, mistyped or revoked. Also the base of `PermissionDeniedError` (403)."""


class PermissionDeniedError(AuthenticationError):
    """403: the key is valid but this is not allowed for the account. `reason` says why when the API does."""


class NotFoundError(APIError):
    """404: there is no such scraper, run, posting or company."""


class RateLimitError(APIError):
    """429: `too_many_runs` (wait for one of your runs to end) or `rate_limited` (wait `retry_after` seconds)."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

    @property
    def active_runs(self) -> Optional[int]:
        value = self.details.get("active_runs")
        return value if isinstance(value, int) else None

    @property
    def max_concurrent_runs(self) -> Optional[int]:
        value = self.details.get("max_concurrent_runs")
        return value if isinstance(value, int) else None


class ValidationError(APIError):
    """The request does not fit (422 `invalid_input`, or any other 4xx). `fields` lists what is wrong."""

    @property
    def fields(self) -> List[Dict[str, str]]:
        """`[{"path": "input.board_url", "message": "..."}]`; empty when the API named no field."""
        fields = self.details.get("fields")
        if not isinstance(fields, list):
            return []
        return [dict(item) for item in fields if isinstance(item, Mapping)]


class QuotaExceededError(ValidationError):
    """402 `quota_exceeded`: this month's allowance is used up. Nothing was created or charged."""

    @property
    def used_units(self) -> Optional[int]:
        value = self.details.get("used_units")
        return value if isinstance(value, int) else None

    @property
    def allowance_units(self) -> Optional[int]:
        value = self.details.get("allowance_units")
        return value if isinstance(value, int) else None


class ServerError(APIError):
    """5xx: something went wrong on the API's side (`internal`, `data_unavailable`)."""


class RunFailedError(EnrichedNowError):
    """A run ended `failed`, `unsupported` or `cancelled`. The request itself was fine; the run is on `run`."""

    def __init__(self, run: "Run") -> None:
        self.run = run
        self.run_id = run.id
        self.status = run.status
        self.reason = run.reason
        text = f"Run {run.id} of {run.scraper_id} ended {run.status}"
        if run.reason:
            text += f" ({run.reason})"
        self.message = text + "."
        super().__init__(self.message)


class WaitTimeoutError(EnrichedNowError):
    """A run was still `queued` or `running` when the time given to wait ran out. The run carries on; it is on `run`."""

    def __init__(self, run: "Run", timeout: float) -> None:
        self.run = run
        self.run_id = run.id
        self.status = run.status
        self.timeout = timeout
        self.message = f"Run {run.id} was still {run.status} after {timeout:g} seconds."
        super().__init__(self.message)
