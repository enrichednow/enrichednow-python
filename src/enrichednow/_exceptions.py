"""Everything this library raises.

    EnrichedNowError
    ├── MissingAPIKeyError
    ├── APIConnectionError            the request never got an answer
    │   └── APITimeoutError
    ├── APIError                      the API answered with an error
    │   ├── AuthenticationError       401
    │   │   └── PermissionDeniedError 403
    │   │       └── PlanLimitReachedError       403 `plan_limit_reached`: the plan allows no more of this
    │   ├── NotFoundError             404 (also `formula_not_found`)
    │   ├── ConflictError             409
    │   │   ├── AttestationRequiredError        409 `attestation_required`: the formula's terms are not accepted
    │   │   ├── FormulaUnavailableError         409 `formula_unavailable`: the formula cannot be run now
    │   │   ├── RequirementMissingError         409 `requirement_missing`: it needs something the account lacks
    │   │   └── SavedFormulaArchivedError       409 `saved_formula_archived`
    │   ├── RateLimitError            429
    │   ├── ValidationError           any other 4xx (422 `invalid_input`, `unit_cap_too_low`)
    │   │   └── QuotaExceededError    402 `quota_exceeded`
    │   │       └── LimitReachedError 402 `limit_reached`: a spend limit of the account's own, of the key, or of a
    │   │                                 saved formula
    │   └── ServerError               5xx
    ├── RunFailedError                a run ended failed, unsupported or cancelled
    │   └── FormulaRunFailedError     a formula run did
    ├── WaitTimeoutError              a run did not end within the time given
    └── WebhookVerificationError      a webhook request is not one this API signed
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Union

import httpx

if TYPE_CHECKING:
    from ._models import FormulaRun, Run

__all__ = [
    "EnrichedNowError",
    "MissingAPIKeyError",
    "APIConnectionError",
    "APITimeoutError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ValidationError",
    "QuotaExceededError",
    "LimitReachedError",
    "ServerError",
    "RunFailedError",
    "WaitTimeoutError",
    "WebhookVerificationError",
    "PlanLimitReachedError",
    "AttestationRequiredError",
    "FormulaUnavailableError",
    "RequirementMissingError",
    "SavedFormulaArchivedError",
    "FormulaRunFailedError",
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


class PlanLimitReachedError(PermissionDeniedError):
    """403 `plan_limit_reached`: the account's plan allows no more of this. `limit` says which: `schedules` (saved
    formulas with an active schedule at once), `min_interval_minutes` (the shortest cadence) or `destinations`;
    `allowed` is what the plan allows. Pause another schedule, choose a longer cadence, or change the plan."""

    @property
    def limit(self) -> Optional[str]:
        value = self.details.get("limit")
        return value if isinstance(value, str) else None

    @property
    def allowed(self) -> Optional[int]:
        value = self.details.get("allowed")
        return value if isinstance(value, int) else None

    @property
    def current(self) -> Optional[int]:
        """How many there are now (for `schedules` and `destinations`)."""
        value = self.details.get("current")
        return value if isinstance(value, int) else None

    @property
    def asked(self) -> Optional[int]:
        """The interval asked for, in minutes (for `min_interval_minutes`)."""
        value = self.details.get("asked")
        return value if isinstance(value, int) else None


class NotFoundError(APIError):
    """404: there is no such scraper, run, posting, company, formula (`formula_not_found`) or saved formula."""


class ConflictError(APIError):
    """409. `idempotency_conflict`: the idempotency key was already used, in the last 24 hours, for a different
    request; `details["run_id"]` is the run that key started. The formula conflicts are subclasses of this one."""


class AttestationRequiredError(ConflictError):
    """409 `attestation_required`: the formula returns people's contact details, and an owner or an admin of the
    account must first accept its terms, in the console. Nothing was started or charged.
    `client.attestations.list()` shows the terms and whether they are accepted."""

    @property
    def kind(self) -> Optional[str]:
        """The terms needed: `personal_data`."""
        value = self.details.get("kind")
        return value if isinstance(value, str) else None

    @property
    def text_version(self) -> Optional[str]:
        value = self.details.get("text_version")
        return value if isinstance(value, str) else None


class FormulaUnavailableError(ConflictError):
    """409 `formula_unavailable`: the formula cannot be run now: it is deprecated (`formula_status`), formulas are
    off for the moment, or a saved formula's version is no longer offered (`formula_id`, `major`)."""

    @property
    def formula_status(self) -> Optional[str]:
        value = self.details.get("status")
        return value if isinstance(value, str) else None

    @property
    def formula_id(self) -> Optional[str]:
        value = self.details.get("formula_id")
        return value if isinstance(value, str) else None

    @property
    def major(self) -> Optional[int]:
        value = self.details.get("major")
        return value if isinstance(value, int) else None


class RequirementMissingError(ConflictError):
    """409 `requirement_missing`: the formula needs something this account or the service does not have. `missing`
    names each: a product (`product:data`) or a source that is not offered."""

    @property
    def missing(self) -> List[str]:
        value = self.details.get("missing")
        return [str(item) for item in value] if isinstance(value, list) else []


class SavedFormulaArchivedError(ConflictError):
    """409 `saved_formula_archived`: the saved formula is archived and cannot run or change. Duplicate it to use it
    again."""

    @property
    def saved_formula_id(self) -> Optional[str]:
        value = self.details.get("saved_formula_id")
        return value if isinstance(value, str) else None


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
    """The request does not fit (422 `invalid_input`, or any other 4xx). `fields` lists what is wrong. A formula's
    unit cap below the least it can do anything with is `unit_cap_too_low`, with `min_unit_cap`."""

    @property
    def fields(self) -> List[Dict[str, str]]:
        """`[{"path": "input.board_url", "message": "..."}]`; empty when the API named no field."""
        fields = self.details.get("fields")
        if not isinstance(fields, list):
            return []
        return [dict(item) for item in fields if isinstance(item, Mapping)]

    @property
    def min_unit_cap(self) -> Optional[int]:
        """For `unit_cap_too_low`: the least unit cap the formula takes."""
        value = self.details.get("min_unit_cap")
        return value if isinstance(value, int) else None


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

    @property
    def topup_units(self) -> Optional[int]:
        """The top-up units left (0: spent too), when starting a run was refused."""
        value = self.details.get("topup_units")
        return value if isinstance(value, int) else None

    @property
    def units_needed(self) -> Optional[int]:
        """The least the run would have cost: its scraper's units per request, or per record for one record."""
        value = self.details.get("units_needed")
        return value if isinstance(value, int) else None


class LimitReachedError(QuotaExceededError):
    """402 `limit_reached`: the run would go past a spend limit set on purpose: the account's monthly limit (`scope`
    `"account"`), the API key's (`scope` `"key"`, with `key_id`), or a saved formula's monthly cap (`scope`
    `"saved_formula"`, with `saved_formula_id`). Units may be left on the plan: raising the limit is what helps.
    Nothing was created or charged. A `QuotaExceededError`, so code that catches that one catches this too."""

    @property
    def scope(self) -> Optional[str]:
        """`"account"`, `"key"`, `"saved_formula"` or `"formula_run"`: whose limit was reached."""
        value = self.details.get("scope")
        return value if isinstance(value, str) else None

    @property
    def key_id(self) -> Optional[str]:
        """The API key whose limit was reached, when `scope` is `"key"`."""
        value = self.details.get("key_id")
        return value if isinstance(value, str) else None

    @property
    def saved_formula_id(self) -> Optional[str]:
        """The saved formula whose monthly cap was reached, when `scope` is `"saved_formula"`."""
        value = self.details.get("saved_formula_id")
        return value if isinstance(value, str) else None

    @property
    def limit_units(self) -> Optional[int]:
        """The limit, in units a calendar month."""
        value = self.details.get("limit_units")
        return value if isinstance(value, int) else None


class ServerError(APIError):
    """5xx: something went wrong on the API's side (`internal`, `data_unavailable`)."""


class RunFailedError(EnrichedNowError):
    """A run ended `failed`, `unsupported` or `cancelled`. The request itself was fine; the run is on `run`."""

    run: Any

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


class FormulaRunFailedError(RunFailedError):
    """A formula run ended `failed`, `unsupported` or `cancelled`: `client.run_formula()` raises it. The run is on
    `run`; a `RunFailedError`, so code that catches that one catches this too."""

    run: "FormulaRun"

    def __init__(self, run: "FormulaRun") -> None:
        self.run = run
        self.run_id = run.id
        self.status = run.status
        self.reason = run.reason
        text = f"Formula run {run.id} of {run.formula_id} ended {run.status}"
        if run.reason:
            text += f" ({run.reason})"
        self.message = text + "."
        EnrichedNowError.__init__(self, self.message)


class WaitTimeoutError(EnrichedNowError):
    """A run was still `queued` or `running` when the time given to wait ran out. The run carries on; it is on `run`
    (a `Run`, or a `FormulaRun` when it was a formula run)."""

    def __init__(self, run: "Union[Run, FormulaRun]", timeout: float) -> None:
        self.run = run
        self.run_id = run.id
        self.status = run.status
        self.timeout = timeout
        self.message = f"Run {run.id} was still {run.status} after {timeout:g} seconds."
        super().__init__(self.message)


class WebhookVerificationError(EnrichedNowError):
    """A webhook request did not verify: its signature is not this secret's over this timestamp and body, its
    timestamp is too far from now, or what was signed is not an event. Answer `400` and do nothing with it."""

    def __init__(self, message: str = "The webhook request did not verify.") -> None:
        self.message = message
        super().__init__(message)
