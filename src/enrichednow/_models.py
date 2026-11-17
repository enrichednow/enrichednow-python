"""What the API returns, as frozen dataclasses.

Every model keeps the JSON it was built from on `.raw`, so a field the API adds later is never lost, and a field this
version of the library does not know never breaks parsing. A field the API left out is `None`.
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Mapping, Optional, Type, TypeVar

__all__ = [
    "Model",
    "Health",
    "Scraper",
    "ScraperDetails",
    "RunDiagnostics",
    "Run",
    "Period",
    "UsageRow",
    "Usage",
    "CompanyRef",
    "Location",
    "Salary",
    "Source",
    "Posting",
    "Classification",
    "Event",
    "Change",
    "Sightings",
    "History",
    "PostingDetail",
    "CompanyName",
    "LastRead",
    "PostingCounts",
    "Company",
    "ACTIVE_STATUSES",
    "TERMINAL_STATUSES",
    "FAILURE_STATUSES",
]

ACTIVE_STATUSES = frozenset({"queued", "running"})
TERMINAL_STATUSES = frozenset({"ok", "partial", "failed", "unsupported", "cancelled"})
FAILURE_STATUSES = frozenset({"failed", "unsupported", "cancelled"})

M = TypeVar("M", bound="Model")
_FRACTION = re.compile(r"\.(\d+)")


def _datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    # Python 3.9 and 3.10 read only 3 or 6 fractional digits: give them 6.
    text = _FRACTION.sub(lambda m: "." + (m.group(1) + "000000")[:6], text, count=1)
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _date(value: Any) -> Optional[date]:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of(convert: Callable[[Any], Any]) -> Callable[[Any], List[Any]]:
    def run(value: Any) -> List[Any]:
        return [convert(item) for item in value] if isinstance(value, list) else []

    return run


def _f(convert: Optional[Callable[[Any], Any]] = None, *, key: Optional[str] = None, empty: Optional[Callable[[], Any]] = None) -> Any:
    """A model field: `convert` builds it from JSON, `key` is its JSON name when that differs, `empty` is its value
    when the API left it out (default `None`)."""
    return field(metadata={"convert": convert, "key": key, "empty": empty})


@dataclass(frozen=True)
class Model:
    raw: Dict[str, Any] = field(repr=False, compare=False)
    """The JSON object as the API returned it."""

    @classmethod
    def from_dict(cls: Type[M], data: Any) -> M:
        source: Mapping[str, Any] = data if isinstance(data, Mapping) else {}
        values: Dict[str, Any] = {}
        for item in dataclasses.fields(cls):
            if item.name == "raw":
                continue
            value = source.get(item.metadata.get("key") or item.name)
            convert = item.metadata.get("convert")
            empty = item.metadata.get("empty")
            if value is None:
                value = empty() if empty else None
            elif convert is not None:
                value = convert(value)
            values[item.name] = value
        return cls(raw=dict(source), **values)

    def to_dict(self) -> Dict[str, Any]:
        """The JSON object as the API returned it."""
        return dict(self.raw)


# --- service ----------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Health(Model):
    status: str = _f()


# --- scrapers ---------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Scraper(Model):
    """A scraper as the catalogue lists it."""

    id: str = _f()
    version: int = _f()
    title: str = _f()
    summary: str = _f()
    mode: str = _f()
    """`sync` or `job`."""
    billing_unit: str = _f()
    """`request` or `record`."""
    data_class: str = _f()
    availability: str = _f()


@dataclass(frozen=True)
class ScraperDetails(Scraper):
    """One scraper, with the JSON Schema of its input and of one record."""

    input_schema: Dict[str, Any] = _f(_dict, empty=dict)
    record_schema: Dict[str, Any] = _f(_dict, empty=dict)


# --- runs -------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RunDiagnostics(Model):
    requests: int = _f()
    bytes: Optional[int] = _f()
    wall_ms: Optional[int] = _f()
    facts: Dict[str, Any] = _f(_dict, empty=dict)


@dataclass(frozen=True)
class Run(Model):
    """One execution of one scraper with one input."""

    id: str = _f()
    scraper_id: str = _f()
    scraper_version: int = _f()
    status: str = _f()
    """`queued`, `running`, `ok`, `partial`, `failed`, `unsupported` or `cancelled`."""
    reason: Optional[str] = _f()
    """A stable code whenever the status is not `ok`."""
    input: Dict[str, Any] = _f(_dict, empty=dict)
    record_count: int = _f()
    units: int = _f()
    """Units charged: 0 until the run ends `ok` or `partial`."""
    diagnostics: Optional[RunDiagnostics] = _f(RunDiagnostics.from_dict)
    created_at: Optional[datetime] = _f(_datetime)
    started_at: Optional[datetime] = _f(_datetime)
    finished_at: Optional[datetime] = _f(_datetime)

    @property
    def is_terminal(self) -> bool:
        """True once the run has ended, however it ended."""
        return self.status not in ACTIVE_STATUSES

    @property
    def is_active(self) -> bool:
        """True while the run is `queued` or `running`."""
        return self.status in ACTIVE_STATUSES

    @property
    def succeeded(self) -> bool:
        """True when the run ended `ok` or `partial`."""
        return self.status in ("ok", "partial")

    @property
    def failed(self) -> bool:
        """True when the run ended `failed`, `unsupported` or `cancelled`."""
        return self.status in FAILURE_STATUSES

    def raise_for_status(self) -> "Run":
        """Raise `RunFailedError` when the run ended `failed`, `unsupported` or `cancelled`; otherwise return it."""
        if self.failed:
            from ._exceptions import RunFailedError

            raise RunFailedError(self)
        return self


# --- usage ------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Period(Model):
    from_: Optional[date] = _f(_date, key="from")
    """First day (UTC), included. `from` in the API."""
    to: Optional[date] = _f(_date)
    """Last day (UTC), included."""


@dataclass(frozen=True)
class UsageRow(Model):
    key: str = _f()
    """A day (`YYYY-MM-DD`), a scraper id, or a product, depending on `group_by`."""
    units: int = _f()
    runs: int = _f()


@dataclass(frozen=True)
class Usage(Model):
    period: Period = _f(Period.from_dict, empty=lambda: Period.from_dict({}))
    total_units: int = _f()
    allowance_units: int = _f()
    rows: List[UsageRow] = _f(_list_of(UsageRow.from_dict), empty=list)


# --- datasets ---------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CompanyRef(Model):
    domain: Optional[str] = _f()
    name: Optional[str] = _f()


@dataclass(frozen=True)
class Location(Model):
    raw_text: Optional[str] = _f(key="raw")
    """The location as the source wrote it. `raw` in the API."""
    city: Optional[str] = _f()
    region: Optional[str] = _f()
    country: Optional[str] = _f()
    country_code: Optional[str] = _f()
    remote: Optional[bool] = _f()


@dataclass(frozen=True)
class Salary(Model):
    raw_text: Optional[str] = _f(key="raw")
    """The salary as the source wrote it. `raw` in the API."""
    min: Optional[float] = _f()
    max: Optional[float] = _f()
    currency: Optional[str] = _f()
    period: Optional[str] = _f()


@dataclass(frozen=True)
class Source(Model):
    name: str = _f()
    provenance: str = _f()
    """`feed`, `page` or `board`."""
    trusted: bool = _f()
    external_id: Optional[str] = _f()


@dataclass(frozen=True)
class Posting(Model):
    """A job posting, as a list returns it."""

    id: str = _f()
    title: str = _f()
    title_clean: str = _f()
    company: CompanyRef = _f(CompanyRef.from_dict, empty=lambda: CompanyRef.from_dict({}))
    location: Location = _f(Location.from_dict, empty=lambda: Location.from_dict({}))
    employment_type: Optional[str] = _f()
    salary: Optional[Salary] = _f(Salary.from_dict)
    posted_at: Optional[date] = _f(_date)
    valid_through: Optional[date] = _f(_date)
    seniority: Optional[str] = _f()
    function: Optional[str] = _f()
    url: str = _f()
    apply_url: Optional[str] = _f()
    source: Source = _f(Source.from_dict, empty=lambda: Source.from_dict({}))
    status: str = _f()
    """`open` or `closed`."""
    first_seen_at: Optional[datetime] = _f(_datetime)
    last_seen_at: Optional[datetime] = _f(_datetime)
    closed_at: Optional[datetime] = _f(_datetime)


@dataclass(frozen=True)
class Classification(Model):
    seniority_rule: Optional[str] = _f()
    function_rule: Optional[str] = _f()


@dataclass(frozen=True)
class Event(Model):
    kind: str = _f()
    """`first_seen`, `seen_earlier`, `closed` or `reopened`."""
    at: Optional[datetime] = _f(_datetime)


@dataclass(frozen=True)
class Change(Model):
    field: str = _f()
    old: Any = _f()
    new: Any = _f()
    at: Optional[datetime] = _f(_datetime)


@dataclass(frozen=True)
class Sightings(Model):
    count: int = _f()
    recent: List[datetime] = _f(lambda value: [d for d in map(_datetime, value if isinstance(value, list) else []) if d], empty=list)


@dataclass(frozen=True)
class History(Model):
    events: List[Event] = _f(_list_of(Event.from_dict), empty=list)
    changes: List[Change] = _f(_list_of(Change.from_dict), empty=list)
    sightings: Sightings = _f(Sightings.from_dict, empty=lambda: Sightings.from_dict({}))
    reopened_count: int = _f()


@dataclass(frozen=True)
class PostingDetail(Posting):
    """One posting, with its description and its history."""

    description: Optional[str] = _f()
    classification: Classification = _f(Classification.from_dict, empty=lambda: Classification.from_dict({}))
    history: History = _f(History.from_dict, empty=lambda: History.from_dict({}))


@dataclass(frozen=True)
class CompanyName(Model):
    name: str = _f()
    first_seen_at: Optional[datetime] = _f(_datetime)
    last_seen_at: Optional[datetime] = _f(_datetime)


@dataclass(frozen=True)
class LastRead(Model):
    at: Optional[datetime] = _f(_datetime)
    status: Optional[str] = _f()
    """`complete`, `incomplete` or `failed`."""
    last_complete_at: Optional[datetime] = _f(_datetime)


@dataclass(frozen=True)
class PostingCounts(Model):
    open: int = _f()
    closed: int = _f()


@dataclass(frozen=True)
class Company(Model):
    domain: str = _f()
    name: Optional[str] = _f()
    names: List[CompanyName] = _f(_list_of(CompanyName.from_dict), empty=list)
    careers_url: Optional[str] = _f()
    ats: Optional[str] = _f()
    first_seen_at: Optional[datetime] = _f(_datetime)
    last_seen_at: Optional[datetime] = _f(_datetime)
    last_read: LastRead = _f(LastRead.from_dict, empty=lambda: LastRead.from_dict({}))
    postings: PostingCounts = _f(PostingCounts.from_dict, empty=lambda: PostingCounts.from_dict({}))
