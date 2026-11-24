"""Formulas: the catalogue and runs (`client.formulas`, `client.formula_runs`), saved formulas (`client.saved_formulas`),
the suppression list (`client.suppressions`), the terms some formulas need (`client.attestations`) and what is wrong
with a row (`client.formula_rows`). Each exists twice, sync and async.

A formula is a ready-made workflow: a few parameters in, a finished, deduplicated list of rows out. A run of one spends
at most its unit cap and counts as one run in progress, whatever it does inside.
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import date, datetime
from typing import (TYPE_CHECKING, Any, AsyncIterator, BinaryIO, Dict, Iterable, Iterator, List, Literal, Mapping, Optional,
                    Tuple, Union)

from ._base import DEFAULT_POLL_INTERVAL, DEFAULT_RUN_TIMEOUT, build_page, path_segment, validate_wait, without_header
from ._exceptions import WaitTimeoutError
from ._models import (
    Attestation,
    Formula,
    FormulaDetails,
    FormulaEstimate,
    FormulaRow,
    FormulaRun,
    PlanLimits,
    RowFeedback,
    RowsExport,
    SavedFormula,
    SeenReset,
    Snapshot,
    Suppression,
    SuppressionUpload,
)
from ._pagination import AsyncPage, AsyncPaginator, SyncPage

if TYPE_CHECKING:
    import httpx

    from ._client import AsyncEnrichedNow, EnrichedNow

__all__ = [
    "NOT_GIVEN", "NotGiven", "RowFormat", "RowView", "Verdict", "SuppressionKind", "ScheduleSpec",
    "Formulas", "AsyncFormulas", "FormulaRuns", "AsyncFormulaRuns", "SavedFormulas", "AsyncSavedFormulas",
    "Suppressions", "AsyncSuppressions", "Attestations", "AsyncAttestations", "FormulaRows", "AsyncFormulaRows",
]

RowFormat = Literal["csv", "ndjson"]
"""How the API writes rows for a download: `csv` (a header row, then a row a line) or `ndjson` (a row's columns a line)."""
RowView = Literal["rows", "company"]
"""`company`: one row per company, for a formula that offers it (`FormulaDetails.company_view`)."""
Verdict = Literal["good", "wrong_company", "wrong_contact", "not_relevant"]
SuppressionKind = Literal["domain", "email", "company_name"]
Params = Mapping[str, Any]
"""A formula's parameters: a dict, or the formula's own type from `enrichednow.formula_params`."""
Fields = Union[str, Iterable[str]]
"""Column keys: a list, or one string of them comma-separated."""
Moment = Union[datetime, date, str]
"""A time: a `datetime`, a `date` (its start, UTC) or an ISO 8601 string."""
ScheduleSpec = Mapping[str, Any]
"""`{"cadence": "weekdays", "local_time": "07:30", "timezone": "Europe/London"}`; `day_of_week` (0 is Monday) for
`weekly`, `day_of_month` for `monthly`. Cadences: `hourly`, `daily`, `weekdays`, `weekly`, `monthly`."""
CsvFile = Union[bytes, str, "os.PathLike[str]", BinaryIO]
"""A CSV file: its bytes, its text, a path (`pathlib.Path`), or a file opened in binary mode."""

LONG_POLL = 60              # seconds the API is asked to hold each look at a run that is still going
ROWS_PAGE = 1000            # rows a page when a whole run is read or written: the API's largest page
_ACCEPT = {"csv": "text/csv", "ndjson": "application/x-ndjson"}
_FORMATS = ("csv", "ndjson")
_VIEWS = ("rows", "company")


class NotGiven:
    """The default of a field of `saved_formulas.update` that is left as it is. `None` is something else there: it
    removes the schedule or the monthly cap, or takes the name back to one made from the parameters."""

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN: Any = NotGiven()


# --- what the requests are made of ----------------------------------------------------------------------------------------


def _params(params: Optional[Params]) -> Dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, Mapping):
        raise TypeError("params must be a mapping: the formula's parameters, as its `parameters` schema describes them")
    return dict(params)


def _cap(name: str, value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a whole number, 1 or more")
    return value


def _run_body(params: Optional[Params], *, preview: bool, unit_cap: Optional[int], row_cap: Optional[int]) -> Dict[str, Any]:
    """What starting or estimating a run sends: only what was given, so the API's defaults apply to the rest."""
    body: Dict[str, Any] = {"params": _params(params)}
    if preview:
        body["mode"] = "preview"
    if _cap("unit_cap", unit_cap) is not None:
        body["unit_cap"] = unit_cap
    if _cap("row_cap", row_cap) is not None:
        body["row_cap"] = row_cap
    return body


def _fields(fields: Optional[Fields]) -> Optional[str]:
    if fields is None:
        return None
    names = [fields] if isinstance(fields, str) else [str(name) for name in fields]
    joined = ",".join(name.strip() for name in names if name.strip())
    return joined or None


def _view(view: Optional[str]) -> Optional[str]:
    if view is not None and view not in _VIEWS:
        raise ValueError("view must be 'rows' or 'company'")
    return view


def _format(format: str) -> str:
    if format not in _FORMATS:
        raise ValueError(f"format must be one of {', '.join(_FORMATS)}; for rows as objects use .rows()")
    return format


def _rows_query(*, fields: Optional[Fields], min_score: Optional[float], view: Optional[str] = None, limit: Optional[int],
                cursor: Optional[str], since: Optional[Moment] = None, order: Optional[str] = None) -> Dict[str, Any]:
    if order is not None and order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    return {"since": since, "order": order, "fields": _fields(fields), "min_score": min_score, "view": _view(view), "limit": limit,
            "cursor": cursor}


def _export(format: str, response: "httpx.Response") -> RowsExport:
    return RowsExport(format=format, content=response.content, next_cursor=response.headers.get("x-next-cursor") or None)


def _schedule(schedule: Optional[ScheduleSpec]) -> Optional[Dict[str, Any]]:
    if schedule is None:
        return None
    if not isinstance(schedule, Mapping):
        raise TypeError('schedule must be a mapping: {"cadence": ..., "local_time": "HH:MM", "timezone": ...}')
    return {key: value for key, value in schedule.items() if value is not None}


def _given(body: Dict[str, Any], **values: Any) -> Dict[str, Any]:
    """`body` with each value that was given: `None` is sent as null, `NOT_GIVEN` is left out."""
    for name, value in values.items():
        if value is not NOT_GIVEN:
            body[name] = value
    return body


def _entries(entries: Iterable[Union[Mapping[str, Any], Tuple[str, str]]]) -> List[Dict[str, str]]:
    if isinstance(entries, (str, bytes, Mapping)):
        raise TypeError('entries must be a list of {"kind": ..., "value": ...} or of (kind, value)')
    out = []
    for entry in entries:
        if isinstance(entry, Mapping):
            kind, value = entry.get("kind"), entry.get("value")
        elif isinstance(entry, tuple) and len(entry) == 2:
            kind, value = entry
        else:
            raise TypeError('each entry must be {"kind": ..., "value": ...} or (kind, value)')
        out.append({"kind": str(kind), "value": str(value)})
    if not out:
        raise ValueError("give at least one entry")
    return out


def _csv_bytes(file: CsvFile) -> bytes:
    if isinstance(file, bytes):
        return file
    if isinstance(file, str):
        return file.encode("utf-8")
    if isinstance(file, os.PathLike):
        with open(file, "rb") as handle:
            return handle.read()
    read = getattr(file, "read", None)
    if callable(read):
        data = read()
        return data.encode("utf-8") if isinstance(data, str) else bytes(data)
    raise TypeError("file must be bytes, text, a pathlib.Path or a file opened for reading")


def _poll_interval(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError("poll_interval must be a number of seconds, 0 or more")
    return float(value)


def _hold(deadline: Optional[float]) -> Optional[int]:
    """How long the API is asked to hold the next look: up to a minute, never past the deadline."""
    if deadline is None:
        return LONG_POLL
    return int(max(0.0, min(LONG_POLL, deadline - time.monotonic()))) or None


def _formulas(payload: Any) -> List[Formula]:
    rows = payload.get("formulas") if isinstance(payload, Mapping) else None
    return [Formula.from_dict(row) for row in rows] if isinstance(rows, list) else []


def _list(payload: Any, key: str, convert: Any) -> List[Any]:
    rows = payload.get(key) if isinstance(payload, Mapping) else None
    return [convert(row) for row in rows] if isinstance(rows, list) else []


# ======================================================================================================================
# sync
# ======================================================================================================================


class Formulas:
    """The catalogue of formulas, what a run would cost, and starting one."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self, *, query: Optional[str] = None, category: Optional[str] = None, persona: Optional[str] = None,
             status: Optional[str] = None) -> List[Formula]:
        """`GET /v1/formulas`: the catalogue. `query` is what you want, in your own words ("companies hiring Java
        developers in London with HR contacts"): the formulas that match come best first. `category`, `persona` and
        `status` (`beta`, `live`) narrow it too. Free to read."""
        return _formulas(self._client._request("GET", "/v1/formulas", params={
            "query": query, "category": category, "persona": persona, "status": status}))

    def get(self, formula_id: str) -> FormulaDetails:
        """`GET /v1/formulas/{id}`: one formula, with the JSON Schema of its parameters, its presets, columns, what it
        needs and whether this account has it, and 20 sample rows. Free to read."""
        return FormulaDetails.from_dict(self._client._request("GET", f"/v1/formulas/{path_segment(formula_id)}"))

    def estimate(self, formula_id: str, params: Optional[Params] = None, *, unit_cap: Optional[int] = None,
                 row_cap: Optional[int] = None, preview: bool = False) -> FormulaEstimate:
        """`POST /v1/formulas/{id}/estimate`: what a run with these parameters would cost. Free; spends nothing.

        Parameters that cannot run are not an error: the answer's `valid` is false and `errors` says what to change.
        Units are an estimate: `estimate.max_units` is the only promise, and a run never passes its unit cap.
        """
        return FormulaEstimate.from_dict(self._client._request(
            "POST", f"/v1/formulas/{path_segment(formula_id)}/estimate",
            json=_run_body(params, preview=preview, unit_cap=unit_cap, row_cap=row_cap)))

    def run(self, formula_id: str, params: Optional[Params] = None, *, preview: bool = False, unit_cap: Optional[int] = None,
            row_cap: Optional[int] = None, wait: Optional[float] = None, idempotency_key: Optional[str] = None) -> FormulaRun:
        """`POST /v1/formulas/{id}/runs`: start a run.

        `params` are the formula's parameters (only its required ones are needed): a dict, or its type from
        `enrichednow.formula_params`. `preview` runs at most 10 rows and 50 units, charged as usual. `unit_cap` is the
        most the run may spend (default: the formula's): it stops there, keeps what it has, and ends `partial`.
        `row_cap` is the most rows it may make.

        `wait` (0 to 300 seconds) asks the API to hold the request until the run ends or the time is up; the run
        that comes back may still be `queued` or `running`: follow it with `client.formula_runs.wait(run.id)`, or use
        `client.run_formula()` to do both.

        The request carries an `Idempotency-Key`, as starting a scraper run does: retried after a timeout or a 5xx
        with the same key, it gives the run the first attempt started, never a second one. Pass `idempotency_key` to
        make a call of yours repeatable across processes for 24 hours.
        """
        wait = validate_wait(wait)
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        return FormulaRun.from_dict(self._client._request(
            "POST", f"/v1/formulas/{path_segment(formula_id)}/runs", params={"wait": wait},
            json=_run_body(params, preview=preview, unit_cap=unit_cap, row_cap=row_cap), headers={"Idempotency-Key": key},
            timeout=self._client._timeout_for(wait)))


class FormulaRuns:
    """Formula runs: following one, reading its rows, writing them as a file, and stopping one."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self, *, formula_id: Optional[str] = None, saved_formula_id: Optional[str] = None, status: Optional[str] = None,
             limit: Optional[int] = None, cursor: Optional[str] = None) -> SyncPage[FormulaRun]:
        """`GET /v1/formula-runs`: the account's formula runs, newest first. Iterate it for every run. `limit` is the
        size of a page (1 to 100, default 20)."""
        def fetch(at: Optional[str]) -> SyncPage[FormulaRun]:
            payload = self._client._request("GET", "/v1/formula-runs", params={
                "formula_id": formula_id, "saved_formula_id": saved_formula_id, "status": status, "limit": limit, "cursor": at})
            return build_page(SyncPage, payload, "runs", FormulaRun.from_dict, fetch)

        return fetch(cursor)

    def get(self, run_id: str, *, wait: Optional[float] = None) -> FormulaRun:
        """`GET /v1/formula-runs/{id}`: the run as it is now, with each step's records, calls and units. `wait` (0 to
        300 seconds) holds the request until the run has ended or the time is up."""
        wait = validate_wait(wait)
        return FormulaRun.from_dict(self._client._request("GET", f"/v1/formula-runs/{path_segment(run_id)}", params={"wait": wait},
                                                          timeout=self._client._timeout_for(wait)))

    def wait(self, run_id: str, *, timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
             poll_interval: float = DEFAULT_POLL_INTERVAL) -> FormulaRun:
        """Follow a run until it has ended, and return it, however it ended.

        Each look asks the API to hold the request for up to a minute, so a run is seen the moment it ends; a look
        answered sooner is followed by a pause of `poll_interval`. Raises `WaitTimeoutError` when the run is still
        going after `timeout` seconds (`None`: no limit). The run itself carries on.
        """
        poll_interval = _poll_interval(poll_interval)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            asked = time.monotonic()
            run = self.get(run_id, wait=_hold(deadline))
            if run.is_terminal:
                return run
            pause = max(0.0, poll_interval - (time.monotonic() - asked))
            if deadline is not None and time.monotonic() + pause >= deadline:
                raise WaitTimeoutError(run, float(timeout or 0))
            if pause:
                self._client._sleep(pause)

    def rows(self, run_id: str, *, fields: Optional[Fields] = None, min_score: Optional[float] = None, view: Optional[RowView] = None,
             limit: Optional[int] = None, cursor: Optional[str] = None) -> SyncPage[FormulaRow]:
        """`GET /v1/formula-runs/{id}/rows`: a run's rows, best first; readable while it is still going.

        Iterate the result for every row; pages are fetched as they are reached. `fields` keeps those columns;
        `min_score` keeps rows scored at least that; `view="company"` gives one row per company, its other columns
        gathered into lists (for a formula with a `company_view`). `limit` is the size of a page (1 to 1000, default
        100). Rows are kept 90 days.
        """
        path = f"/v1/formula-runs/{path_segment(run_id)}/rows"
        query = _rows_query(fields=fields, min_score=min_score, view=view, limit=limit, cursor=None)

        def fetch(at: Optional[str]) -> SyncPage[FormulaRow]:
            payload = self._client._request("GET", path, params={**query, "cursor": at})
            return build_page(SyncPage, payload, "rows", FormulaRow.from_dict, fetch)

        return fetch(cursor)

    def export(self, run_id: str, format: RowFormat, *, fields: Optional[Fields] = None, min_score: Optional[float] = None,
               view: Optional[RowView] = None, limit: Optional[int] = None, cursor: Optional[str] = None) -> RowsExport:
        """`GET /v1/formula-runs/{id}/rows?format=`: one page of a run's rows written by the API, as `csv` or `ndjson`.

        The CSV has the formula's columns in its order (or `fields`'), every page starts with the header row, and a
        cell a spreadsheet would run as a formula starts with an apostrophe. `next_cursor` continues; `export_all`
        follows it for you.
        """
        query = {**_rows_query(fields=fields, min_score=min_score, view=view, limit=limit, cursor=cursor), "format": _format(format)}
        response = self._client._request("GET", f"/v1/formula-runs/{path_segment(run_id)}/rows", params=query,
                                         headers={"Accept": _ACCEPT[format]}, raw=True)
        return _export(format, response)

    def export_all(self, run_id: str, format: RowFormat, *, fields: Optional[Fields] = None, min_score: Optional[float] = None,
                   view: Optional[RowView] = None, limit: int = ROWS_PAGE) -> Iterator[bytes]:
        """Every row of a run, as `csv` or `ndjson`, page by page: write the pieces one after the other and the result
        is one file (a CSV has its header row once)."""
        cursor: Optional[str] = None
        first = True
        while True:
            page = self.export(run_id, format, fields=fields, min_score=min_score, view=view, limit=limit, cursor=cursor)
            yield page.content if first or format != "csv" else without_header(page.content)
            first = False
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    def cancel(self, run_id: str) -> FormulaRun:
        """`POST /v1/formula-runs/{id}/cancel`: stop a run. No new work starts and calls in flight are asked to stop;
        rows already written stay, and what was done stays charged. The answer may still say `running`: follow it with
        `wait`. A run that has ended is returned unchanged."""
        return FormulaRun.from_dict(self._client._request("POST", f"/v1/formula-runs/{path_segment(run_id)}/cancel"))


class SavedFormulas:
    """Saved formulas: a formula with its parameters, kept under a name, to run again by hand or on a schedule. Its runs
    deliver only rows it has not delivered before, so its rows `since` a time are what is new."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def create(self, formula_id: str, params: Optional[Params] = None, *, name: Optional[str] = None,
               schedule: Optional[ScheduleSpec] = None, unit_cap: Optional[int] = None, row_cap: Optional[int] = None,
               monthly_unit_cap: Optional[int] = None, notify: Optional[str] = None) -> SavedFormula:
        """`POST /v1/saved-formulas`: save a formula with its parameters.

        `name` defaults to one made from its key parameters and its cadence. `schedule` runs it by itself:
        `{"cadence": "weekdays", "local_time": "07:30", "timezone": "Europe/London"}`; a schedule counts against the
        plan's (`PlanLimitReachedError`). `unit_cap` is the most one run may spend (above the formula's default: owners
        and admins only), `monthly_unit_cap` the most its runs may spend in a month. `notify` is `each_run` (the
        default), `digest` or `none`: mail when a scheduled run delivers new rows.

        Like adding a webhook endpoint, this request is not sent again after a timeout or a 5xx: the saved formula may
        exist. Look at `list()` before saving it again.
        """
        body: Dict[str, Any] = {"formula_id": formula_id, "params": _params(params)}
        extra = {"name": name, "unit_cap": _cap("unit_cap", unit_cap), "row_cap": _cap("row_cap", row_cap),
                 "monthly_unit_cap": _cap("monthly_unit_cap", monthly_unit_cap), "schedule": _schedule(schedule), "notify": notify}
        body.update({key: value for key, value in extra.items() if value is not None})
        return SavedFormula.from_dict(self._client._request("POST", "/v1/saved-formulas", json=body, idempotent=False))

    def list(self, *, formula_id: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> SyncPage[SavedFormula]:
        """`GET /v1/saved-formulas`: the account's saved formulas, newest first; archived ones only with
        `status="archived"`. Iterate it for every one. `limit` is the size of a page (1 to 100, default 50)."""
        def fetch(at: Optional[str]) -> SyncPage[SavedFormula]:
            payload = self._client._request("GET", "/v1/saved-formulas", params={
                "formula_id": formula_id, "status": status, "limit": limit, "cursor": at})
            return build_page(SyncPage, payload, "saved_formulas", SavedFormula.from_dict, fetch)

        return fetch(cursor)

    def get(self, saved_id: str) -> SavedFormula:
        """`GET /v1/saved-formulas/{id}`: one saved formula, with its schedule, its last run and what it spent in 30 days."""
        return SavedFormula.from_dict(self._client._request("GET", f"/v1/saved-formulas/{path_segment(saved_id)}"))

    def update(self, saved_id: str, *, name: Optional[str] = NOT_GIVEN, params: Optional[Params] = NOT_GIVEN,
               reset_seen: bool = False, unit_cap: Optional[int] = NOT_GIVEN, row_cap: Optional[int] = NOT_GIVEN,
               monthly_unit_cap: Optional[int] = NOT_GIVEN, schedule: Optional[ScheduleSpec] = NOT_GIVEN,
               notify: Optional[str] = NOT_GIVEN) -> SavedFormula:
        """`PATCH /v1/saved-formulas/{id}`: change a saved formula. Only what is given changes; give at least one.

        `None` means something for three of them: `schedule=None` removes the schedule, `monthly_unit_cap=None` the
        monthly cap, and `name=None` goes back to a name made from the parameters. New `params` are the whole set
        (what is left out takes the formula's default) and keep what was already delivered as delivered, unless
        `reset_seen=True` (owners and admins).
        """
        body = _given({}, name=name, unit_cap=unit_cap, row_cap=row_cap, monthly_unit_cap=monthly_unit_cap, notify=notify)
        if params is not NOT_GIVEN:
            body["params"] = None if params is None else _params(params)
        if schedule is not NOT_GIVEN:
            body["schedule"] = _schedule(schedule)
        if reset_seen:
            body["reset_seen"] = True
        if not body:
            raise ValueError("give at least one of name, params, reset_seen, unit_cap, row_cap, monthly_unit_cap, schedule, notify")
        return SavedFormula.from_dict(self._client._request("PATCH", f"/v1/saved-formulas/{path_segment(saved_id)}", json=body))

    def archive(self, saved_id: str) -> SavedFormula:
        """`DELETE /v1/saved-formulas/{id}`: archive it. Its schedule stops and it does not run again; its runs and rows
        are kept as long as they would be. An archived saved formula can be duplicated."""
        return SavedFormula.from_dict(self._client._request("DELETE", f"/v1/saved-formulas/{path_segment(saved_id)}"))

    def duplicate(self, saved_id: str, *, name: Optional[str] = None, copy_seen: bool = False,
                  schedule: Optional[ScheduleSpec] = None) -> SavedFormula:
        """`POST /v1/saved-formulas/{id}/duplicate`: a copy with the same formula, parameters, caps and notices. It
        starts with nothing delivered unless `copy_seen=True`, and with no schedule unless one is given. Not sent again
        after a timeout or a 5xx: the copy may exist."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if copy_seen:
            body["copy_seen"] = True
        if schedule is not None:
            body["schedule"] = _schedule(schedule)
        return SavedFormula.from_dict(self._client._request(
            "POST", f"/v1/saved-formulas/{path_segment(saved_id)}/duplicate", json=body, idempotent=False))

    def run(self, saved_id: str, *, preview: bool = False, include_seen: bool = False, wait: Optional[float] = None,
            idempotency_key: Optional[str] = None) -> FormulaRun:
        """`POST /v1/saved-formulas/{id}/runs`: run it now, with its saved parameters and caps (the monthly cap lowers
        the unit cap to what is left of it). It delivers only rows not delivered before, unless `include_seen=True`. A
        paused saved formula can still be run by hand. `wait` and the `Idempotency-Key` work as on `formulas.run`."""
        wait = validate_wait(wait)
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        body: Dict[str, Any] = {}
        if preview:
            body["mode"] = "preview"
        if include_seen:
            body["include_seen"] = True
        return FormulaRun.from_dict(self._client._request(
            "POST", f"/v1/saved-formulas/{path_segment(saved_id)}/runs", params={"wait": wait}, json=body,
            headers={"Idempotency-Key": key}, timeout=self._client._timeout_for(wait)))

    def pause(self, saved_id: str) -> SavedFormula:
        """`POST /v1/saved-formulas/{id}/pause`: no scheduled run starts until it is resumed. It can still be run by hand."""
        return SavedFormula.from_dict(self._client._request("POST", f"/v1/saved-formulas/{path_segment(saved_id)}/pause"))

    def resume(self, saved_id: str) -> SavedFormula:
        """`POST /v1/saved-formulas/{id}/resume`: its next run is the next slot of its schedule from now; slots missed while
        it was paused do not run. From now on its scheduled runs run as this client's API key, with that key's limits."""
        return SavedFormula.from_dict(self._client._request("POST", f"/v1/saved-formulas/{path_segment(saved_id)}/resume"))

    def reset_seen(self, saved_id: str) -> SeenReset:
        """`POST /v1/saved-formulas/{id}/seen/reset`: forget what it delivered, so its next run may deliver those rows
        again. Owners and admins; recorded in the account's activity."""
        return SeenReset.from_dict(self._client._request("POST", f"/v1/saved-formulas/{path_segment(saved_id)}/seen/reset"))

    def rows(self, saved_id: str, *, since: Optional[Moment] = None, order: Optional[str] = None, fields: Optional[Fields] = None,
             min_score: Optional[float] = None, limit: Optional[int] = None, cursor: Optional[str] = None) -> SyncPage[FormulaRow]:
        """`GET /v1/saved-formulas/{id}/rows`: its rows across its runs, in the order they were written (`order="desc"`:
        newest first). What a daily job polls: `since` keeps the rows written from that time on. Rows the suppression
        list now holds are left out. Iterate it for every row; `fields`, `min_score` and `limit` work as on a run's
        rows."""
        path = f"/v1/saved-formulas/{path_segment(saved_id)}/rows"
        query = _rows_query(fields=fields, min_score=min_score, limit=limit, cursor=None, since=since, order=order)

        def fetch(at: Optional[str]) -> SyncPage[FormulaRow]:
            payload = self._client._request("GET", path, params={**query, "cursor": at})
            return build_page(SyncPage, payload, "rows", FormulaRow.from_dict, fetch)

        return fetch(cursor)

    def export(self, saved_id: str, format: RowFormat, *, since: Optional[Moment] = None, order: Optional[str] = None,
               fields: Optional[Fields] = None, min_score: Optional[float] = None, limit: Optional[int] = None,
               cursor: Optional[str] = None) -> RowsExport:
        """`GET /v1/saved-formulas/{id}/rows?format=`: one page of its rows written by the API, as `csv` or `ndjson`."""
        query = {**_rows_query(fields=fields, min_score=min_score, limit=limit, cursor=cursor, since=since, order=order),
                 "format": _format(format)}
        response = self._client._request("GET", f"/v1/saved-formulas/{path_segment(saved_id)}/rows", params=query,
                                         headers={"Accept": _ACCEPT[format]}, raw=True)
        return _export(format, response)

    def export_all(self, saved_id: str, format: RowFormat, *, since: Optional[Moment] = None, order: Optional[str] = None,
                   fields: Optional[Fields] = None, min_score: Optional[float] = None, limit: int = ROWS_PAGE) -> Iterator[bytes]:
        """Every row of it (from `since`), as `csv` or `ndjson`, page by page: one file (a CSV has its header row once)."""
        cursor: Optional[str] = None
        first = True
        while True:
            page = self.export(saved_id, format, since=since, order=order, fields=fields, min_score=min_score, limit=limit, cursor=cursor)
            yield page.content if first or format != "csv" else without_header(page.content)
            first = False
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    def snapshots(self, saved_id: str, *, entity_key: Optional[str] = None, limit: Optional[int] = None) -> List[Snapshot]:
        """`GET /v1/saved-formulas/{id}/snapshots`: for a formula that watches things (prices, stock, sellers), one entry
        each time a thing's tracked values changed, newest first. `entity_key` keeps one: its history."""
        return _list(self._client._request("GET", f"/v1/saved-formulas/{path_segment(saved_id)}/snapshots",
                                           params={"entity_key": entity_key, "limit": limit}), "snapshots", Snapshot.from_dict)

    def limits(self) -> PlanLimits:
        """`GET /v1/saved-formulas/limits`: what the plan allows: schedules at once (and how many are active), the
        shortest interval between scheduled runs, how long rows are kept, destinations for each saved formula."""
        return PlanLimits.from_dict(self._client._request("GET", "/v1/saved-formulas/limits"))


class Suppressions:
    """The account's suppression list: companies (by domain or by name) and addresses that formula runs leave out
    before any paid step and never send anywhere."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self, *, kind: Optional[SuppressionKind] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> SyncPage[Suppression]:
        """`GET /v1/suppressions`: the list. Iterate it for every entry. `limit` is the size of a page (1 to 1000)."""
        def fetch(at: Optional[str]) -> SyncPage[Suppression]:
            payload = self._client._request("GET", "/v1/suppressions", params={"kind": kind, "limit": limit, "cursor": at})
            return build_page(SyncPage, payload, "suppressions", Suppression.from_dict, fetch)

        return fetch(cursor)

    def add(self, entries: Iterable[Union[Mapping[str, Any], Tuple[str, str]]], *, source: Optional[str] = None) -> int:
        """`POST /v1/suppressions`: add up to 10,000 entries, each `{"kind": ..., "value": ...}` or `(kind, value)`;
        kinds are `domain`, `email` and `company_name`. A domain is kept as its bare host, a company name in the form
        formulas match it. Returns how many were new to the list."""
        body: Dict[str, Any] = {"entries": _entries(entries)}
        if source is not None:
            body["source"] = source
        answer = self._client._request("POST", "/v1/suppressions", json=body)
        return int(answer.get("added", 0)) if isinstance(answer, Mapping) else 0

    def upload(self, file: CsvFile, *, kind: Optional[SuppressionKind] = None) -> SuppressionUpload:
        """`POST /v1/suppressions/upload`: add a CSV file to the list (at most 2 MB and 50,000 lines).

        `file` is the CSV's bytes or text, a `pathlib.Path`, or a file opened in binary mode. With a header row holding
        `kind` and `value`, each line says its kind; otherwise every value of the first column is `kind` or, without
        it, read as an address, a domain or a company name by its look. `invalid` gives each line that could not be
        read; the rest are added.
        """
        return SuppressionUpload.from_dict(self._client._request(
            "POST", "/v1/suppressions/upload", params={"kind": kind}, content=_csv_bytes(file), headers={"Content-Type": "text/csv"}))

    def delete(self, kind: SuppressionKind, value: str) -> None:
        """`DELETE /v1/suppressions/{kind}/{value}`: take an entry off the list."""
        self._client._request("DELETE", f"/v1/suppressions/{path_segment(kind)}/{path_segment(value)}")


class Attestations:
    """The terms some formulas need accepted before they run (a formula's `needs_attestation`). An owner or an admin
    accepts them in the console: a person accepts, not an API key."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self) -> List[Attestation]:
        """`GET /v1/attestations`: each kind of terms, its current text, and whether the account accepted that version."""
        return _list(self._client._request("GET", "/v1/attestations"), "attestations", Attestation.from_dict)


class FormulaRows:
    """What is wrong with a row of a formula run."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def feedback(self, row_id: str, verdict: Verdict, *, note: Optional[str] = None, correct_domain: Optional[str] = None) -> RowFeedback:
        """`POST /v1/formula-rows/{id}/feedback`: `good`, `wrong_company`, `wrong_contact` or `not_relevant`; a later
        answer replaces it. `wrong_company` also corrects the match for this account: its runs from now on match the
        company to `correct_domain`, or to no domain when none is given."""
        body: Dict[str, Any] = {"verdict": verdict}
        if note is not None:
            body["note"] = note
        if correct_domain is not None:
            body["correct_domain"] = correct_domain
        return RowFeedback.from_dict(self._client._request("POST", f"/v1/formula-rows/{path_segment(row_id)}/feedback", json=body))


# ======================================================================================================================
# async
# ======================================================================================================================


class AsyncFormulas:
    """The catalogue of formulas, what a run would cost, and starting one: see `Formulas`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def list(self, *, query: Optional[str] = None, category: Optional[str] = None, persona: Optional[str] = None,
                   status: Optional[str] = None) -> List[Formula]:
        """`GET /v1/formulas`: the catalogue."""
        return _formulas(await self._client._request("GET", "/v1/formulas", params={
            "query": query, "category": category, "persona": persona, "status": status}))

    async def get(self, formula_id: str) -> FormulaDetails:
        """`GET /v1/formulas/{id}`: one formula."""
        return FormulaDetails.from_dict(await self._client._request("GET", f"/v1/formulas/{path_segment(formula_id)}"))

    async def estimate(self, formula_id: str, params: Optional[Params] = None, *, unit_cap: Optional[int] = None,
                       row_cap: Optional[int] = None, preview: bool = False) -> FormulaEstimate:
        """`POST /v1/formulas/{id}/estimate`: what a run would cost; see `Formulas.estimate`."""
        return FormulaEstimate.from_dict(await self._client._request(
            "POST", f"/v1/formulas/{path_segment(formula_id)}/estimate",
            json=_run_body(params, preview=preview, unit_cap=unit_cap, row_cap=row_cap)))

    async def run(self, formula_id: str, params: Optional[Params] = None, *, preview: bool = False, unit_cap: Optional[int] = None,
                  row_cap: Optional[int] = None, wait: Optional[float] = None, idempotency_key: Optional[str] = None) -> FormulaRun:
        """`POST /v1/formulas/{id}/runs`: start a run; see `Formulas.run`."""
        wait = validate_wait(wait)
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        return FormulaRun.from_dict(await self._client._request(
            "POST", f"/v1/formulas/{path_segment(formula_id)}/runs", params={"wait": wait},
            json=_run_body(params, preview=preview, unit_cap=unit_cap, row_cap=row_cap), headers={"Idempotency-Key": key},
            timeout=self._client._timeout_for(wait)))


class AsyncFormulaRuns:
    """Formula runs: see `FormulaRuns`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    def list(self, *, formula_id: Optional[str] = None, saved_formula_id: Optional[str] = None, status: Optional[str] = None,
             limit: Optional[int] = None, cursor: Optional[str] = None) -> AsyncPaginator[FormulaRun, AsyncPage[FormulaRun]]:
        """`GET /v1/formula-runs`: await it for a page, or `async for` over every run."""
        async def fetch(at: Optional[str]) -> AsyncPage[FormulaRun]:
            payload = await self._client._request("GET", "/v1/formula-runs", params={
                "formula_id": formula_id, "saved_formula_id": saved_formula_id, "status": status, "limit": limit, "cursor": at})
            return build_page(AsyncPage, payload, "runs", FormulaRun.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def get(self, run_id: str, *, wait: Optional[float] = None) -> FormulaRun:
        """`GET /v1/formula-runs/{id}`: the run as it is now; `wait` holds the request until it has ended."""
        wait = validate_wait(wait)
        return FormulaRun.from_dict(await self._client._request("GET", f"/v1/formula-runs/{path_segment(run_id)}", params={"wait": wait},
                                                                timeout=self._client._timeout_for(wait)))

    async def wait(self, run_id: str, *, timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
                   poll_interval: float = DEFAULT_POLL_INTERVAL) -> FormulaRun:
        """Follow a run until it has ended; see `FormulaRuns.wait`."""
        poll_interval = _poll_interval(poll_interval)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            asked = time.monotonic()
            run = await self.get(run_id, wait=_hold(deadline))
            if run.is_terminal:
                return run
            pause = max(0.0, poll_interval - (time.monotonic() - asked))
            if deadline is not None and time.monotonic() + pause >= deadline:
                raise WaitTimeoutError(run, float(timeout or 0))
            if pause:
                await self._client._sleep(pause)

    def rows(self, run_id: str, *, fields: Optional[Fields] = None, min_score: Optional[float] = None, view: Optional[RowView] = None,
             limit: Optional[int] = None, cursor: Optional[str] = None) -> AsyncPaginator[FormulaRow, AsyncPage[FormulaRow]]:
        """`GET /v1/formula-runs/{id}/rows`: `async for` over every row, or await it for the first page; see
        `FormulaRuns.rows`."""
        path = f"/v1/formula-runs/{path_segment(run_id)}/rows"
        query = _rows_query(fields=fields, min_score=min_score, view=view, limit=limit, cursor=None)

        async def fetch(at: Optional[str]) -> AsyncPage[FormulaRow]:
            payload = await self._client._request("GET", path, params={**query, "cursor": at})
            return build_page(AsyncPage, payload, "rows", FormulaRow.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def export(self, run_id: str, format: RowFormat, *, fields: Optional[Fields] = None, min_score: Optional[float] = None,
                     view: Optional[RowView] = None, limit: Optional[int] = None, cursor: Optional[str] = None) -> RowsExport:
        """One page of a run's rows written by the API; see `FormulaRuns.export`."""
        query = {**_rows_query(fields=fields, min_score=min_score, view=view, limit=limit, cursor=cursor), "format": _format(format)}
        response = await self._client._request("GET", f"/v1/formula-runs/{path_segment(run_id)}/rows", params=query,
                                               headers={"Accept": _ACCEPT[format]}, raw=True)
        return _export(format, response)

    async def export_all(self, run_id: str, format: RowFormat, *, fields: Optional[Fields] = None, min_score: Optional[float] = None,
                         view: Optional[RowView] = None, limit: int = ROWS_PAGE) -> AsyncIterator[bytes]:
        """Every row of a run, as `csv` or `ndjson`, page by page (`async for`); a CSV has its header row once."""
        cursor: Optional[str] = None
        first = True
        while True:
            page = await self.export(run_id, format, fields=fields, min_score=min_score, view=view, limit=limit, cursor=cursor)
            yield page.content if first or format != "csv" else without_header(page.content)
            first = False
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    async def cancel(self, run_id: str) -> FormulaRun:
        """`POST /v1/formula-runs/{id}/cancel`: stop a run; see `FormulaRuns.cancel`."""
        return FormulaRun.from_dict(await self._client._request("POST", f"/v1/formula-runs/{path_segment(run_id)}/cancel"))


class AsyncSavedFormulas:
    """Saved formulas: see `SavedFormulas`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def create(self, formula_id: str, params: Optional[Params] = None, *, name: Optional[str] = None,
                     schedule: Optional[ScheduleSpec] = None, unit_cap: Optional[int] = None, row_cap: Optional[int] = None,
                     monthly_unit_cap: Optional[int] = None, notify: Optional[str] = None) -> SavedFormula:
        """`POST /v1/saved-formulas`: save a formula with its parameters; see `SavedFormulas.create`."""
        body: Dict[str, Any] = {"formula_id": formula_id, "params": _params(params)}
        extra = {"name": name, "unit_cap": _cap("unit_cap", unit_cap), "row_cap": _cap("row_cap", row_cap),
                 "monthly_unit_cap": _cap("monthly_unit_cap", monthly_unit_cap), "schedule": _schedule(schedule), "notify": notify}
        body.update({key: value for key, value in extra.items() if value is not None})
        return SavedFormula.from_dict(await self._client._request("POST", "/v1/saved-formulas", json=body, idempotent=False))

    def list(self, *, formula_id: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> AsyncPaginator[SavedFormula, AsyncPage[SavedFormula]]:
        """`GET /v1/saved-formulas`: await it for a page, or `async for` over every saved formula."""
        async def fetch(at: Optional[str]) -> AsyncPage[SavedFormula]:
            payload = await self._client._request("GET", "/v1/saved-formulas", params={
                "formula_id": formula_id, "status": status, "limit": limit, "cursor": at})
            return build_page(AsyncPage, payload, "saved_formulas", SavedFormula.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def get(self, saved_id: str) -> SavedFormula:
        """`GET /v1/saved-formulas/{id}`: one saved formula."""
        return SavedFormula.from_dict(await self._client._request("GET", f"/v1/saved-formulas/{path_segment(saved_id)}"))

    async def update(self, saved_id: str, *, name: Optional[str] = NOT_GIVEN, params: Optional[Params] = NOT_GIVEN,
                     reset_seen: bool = False, unit_cap: Optional[int] = NOT_GIVEN, row_cap: Optional[int] = NOT_GIVEN,
                     monthly_unit_cap: Optional[int] = NOT_GIVEN, schedule: Optional[ScheduleSpec] = NOT_GIVEN,
                     notify: Optional[str] = NOT_GIVEN) -> SavedFormula:
        """`PATCH /v1/saved-formulas/{id}`: change a saved formula; see `SavedFormulas.update`."""
        body = _given({}, name=name, unit_cap=unit_cap, row_cap=row_cap, monthly_unit_cap=monthly_unit_cap, notify=notify)
        if params is not NOT_GIVEN:
            body["params"] = None if params is None else _params(params)
        if schedule is not NOT_GIVEN:
            body["schedule"] = _schedule(schedule)
        if reset_seen:
            body["reset_seen"] = True
        if not body:
            raise ValueError("give at least one of name, params, reset_seen, unit_cap, row_cap, monthly_unit_cap, schedule, notify")
        return SavedFormula.from_dict(await self._client._request("PATCH", f"/v1/saved-formulas/{path_segment(saved_id)}", json=body))

    async def archive(self, saved_id: str) -> SavedFormula:
        """`DELETE /v1/saved-formulas/{id}`: archive it; see `SavedFormulas.archive`."""
        return SavedFormula.from_dict(await self._client._request("DELETE", f"/v1/saved-formulas/{path_segment(saved_id)}"))

    async def duplicate(self, saved_id: str, *, name: Optional[str] = None, copy_seen: bool = False,
                        schedule: Optional[ScheduleSpec] = None) -> SavedFormula:
        """`POST /v1/saved-formulas/{id}/duplicate`: a copy; see `SavedFormulas.duplicate`."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if copy_seen:
            body["copy_seen"] = True
        if schedule is not None:
            body["schedule"] = _schedule(schedule)
        return SavedFormula.from_dict(await self._client._request(
            "POST", f"/v1/saved-formulas/{path_segment(saved_id)}/duplicate", json=body, idempotent=False))

    async def run(self, saved_id: str, *, preview: bool = False, include_seen: bool = False, wait: Optional[float] = None,
                  idempotency_key: Optional[str] = None) -> FormulaRun:
        """`POST /v1/saved-formulas/{id}/runs`: run it now; see `SavedFormulas.run`."""
        wait = validate_wait(wait)
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        body: Dict[str, Any] = {}
        if preview:
            body["mode"] = "preview"
        if include_seen:
            body["include_seen"] = True
        return FormulaRun.from_dict(await self._client._request(
            "POST", f"/v1/saved-formulas/{path_segment(saved_id)}/runs", params={"wait": wait}, json=body,
            headers={"Idempotency-Key": key}, timeout=self._client._timeout_for(wait)))

    async def pause(self, saved_id: str) -> SavedFormula:
        """`POST /v1/saved-formulas/{id}/pause`: no scheduled run starts until it is resumed."""
        return SavedFormula.from_dict(await self._client._request("POST", f"/v1/saved-formulas/{path_segment(saved_id)}/pause"))

    async def resume(self, saved_id: str) -> SavedFormula:
        """`POST /v1/saved-formulas/{id}/resume`: its schedule runs again, from the next slot."""
        return SavedFormula.from_dict(await self._client._request("POST", f"/v1/saved-formulas/{path_segment(saved_id)}/resume"))

    async def reset_seen(self, saved_id: str) -> SeenReset:
        """`POST /v1/saved-formulas/{id}/seen/reset`: forget what it delivered (owners and admins)."""
        return SeenReset.from_dict(await self._client._request("POST", f"/v1/saved-formulas/{path_segment(saved_id)}/seen/reset"))

    def rows(self, saved_id: str, *, since: Optional[Moment] = None, order: Optional[str] = None, fields: Optional[Fields] = None,
             min_score: Optional[float] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> AsyncPaginator[FormulaRow, AsyncPage[FormulaRow]]:
        """`GET /v1/saved-formulas/{id}/rows`: `async for` over its rows across its runs; see `SavedFormulas.rows`."""
        path = f"/v1/saved-formulas/{path_segment(saved_id)}/rows"
        query = _rows_query(fields=fields, min_score=min_score, limit=limit, cursor=None, since=since, order=order)

        async def fetch(at: Optional[str]) -> AsyncPage[FormulaRow]:
            payload = await self._client._request("GET", path, params={**query, "cursor": at})
            return build_page(AsyncPage, payload, "rows", FormulaRow.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def export(self, saved_id: str, format: RowFormat, *, since: Optional[Moment] = None, order: Optional[str] = None,
                     fields: Optional[Fields] = None, min_score: Optional[float] = None, limit: Optional[int] = None,
                     cursor: Optional[str] = None) -> RowsExport:
        """One page of its rows written by the API, as `csv` or `ndjson`."""
        query = {**_rows_query(fields=fields, min_score=min_score, limit=limit, cursor=cursor, since=since, order=order),
                 "format": _format(format)}
        response = await self._client._request("GET", f"/v1/saved-formulas/{path_segment(saved_id)}/rows", params=query,
                                               headers={"Accept": _ACCEPT[format]}, raw=True)
        return _export(format, response)

    async def export_all(self, saved_id: str, format: RowFormat, *, since: Optional[Moment] = None, order: Optional[str] = None,
                         fields: Optional[Fields] = None, min_score: Optional[float] = None,
                         limit: int = ROWS_PAGE) -> AsyncIterator[bytes]:
        """Every row of it (from `since`), as one file, page by page (`async for`)."""
        cursor: Optional[str] = None
        first = True
        while True:
            page = await self.export(saved_id, format, since=since, order=order, fields=fields, min_score=min_score, limit=limit,
                                     cursor=cursor)
            yield page.content if first or format != "csv" else without_header(page.content)
            first = False
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    async def snapshots(self, saved_id: str, *, entity_key: Optional[str] = None, limit: Optional[int] = None) -> List[Snapshot]:
        """`GET /v1/saved-formulas/{id}/snapshots`: what a watch formula observed, each time it changed."""
        return _list(await self._client._request("GET", f"/v1/saved-formulas/{path_segment(saved_id)}/snapshots",
                                                 params={"entity_key": entity_key, "limit": limit}), "snapshots", Snapshot.from_dict)

    async def limits(self) -> PlanLimits:
        """`GET /v1/saved-formulas/limits`: what the plan allows of saved formulas."""
        return PlanLimits.from_dict(await self._client._request("GET", "/v1/saved-formulas/limits"))


class AsyncSuppressions:
    """The account's suppression list: see `Suppressions`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    def list(self, *, kind: Optional[SuppressionKind] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> AsyncPaginator[Suppression, AsyncPage[Suppression]]:
        """`GET /v1/suppressions`: await it for a page, or `async for` over every entry."""
        async def fetch(at: Optional[str]) -> AsyncPage[Suppression]:
            payload = await self._client._request("GET", "/v1/suppressions", params={"kind": kind, "limit": limit, "cursor": at})
            return build_page(AsyncPage, payload, "suppressions", Suppression.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def add(self, entries: Iterable[Union[Mapping[str, Any], Tuple[str, str]]], *, source: Optional[str] = None) -> int:
        """`POST /v1/suppressions`: add entries; returns how many were new. See `Suppressions.add`."""
        body: Dict[str, Any] = {"entries": _entries(entries)}
        if source is not None:
            body["source"] = source
        answer = await self._client._request("POST", "/v1/suppressions", json=body)
        return int(answer.get("added", 0)) if isinstance(answer, Mapping) else 0

    async def upload(self, file: CsvFile, *, kind: Optional[SuppressionKind] = None) -> SuppressionUpload:
        """`POST /v1/suppressions/upload`: add a CSV file to the list; see `Suppressions.upload`."""
        return SuppressionUpload.from_dict(await self._client._request(
            "POST", "/v1/suppressions/upload", params={"kind": kind}, content=_csv_bytes(file), headers={"Content-Type": "text/csv"}))

    async def delete(self, kind: SuppressionKind, value: str) -> None:
        """`DELETE /v1/suppressions/{kind}/{value}`: take an entry off the list."""
        await self._client._request("DELETE", f"/v1/suppressions/{path_segment(kind)}/{path_segment(value)}")


class AsyncAttestations:
    """The terms some formulas need: see `Attestations`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def list(self) -> List[Attestation]:
        """`GET /v1/attestations`: each kind of terms and whether the account accepted it."""
        return _list(await self._client._request("GET", "/v1/attestations"), "attestations", Attestation.from_dict)


class AsyncFormulaRows:
    """What is wrong with a row: see `FormulaRows`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def feedback(self, row_id: str, verdict: Verdict, *, note: Optional[str] = None,
                       correct_domain: Optional[str] = None) -> RowFeedback:
        """`POST /v1/formula-rows/{id}/feedback`; see `FormulaRows.feedback`."""
        body: Dict[str, Any] = {"verdict": verdict}
        if note is not None:
            body["note"] = note
        if correct_domain is not None:
            body["correct_domain"] = correct_domain
        return RowFeedback.from_dict(await self._client._request("POST", f"/v1/formula-rows/{path_segment(row_id)}/feedback", json=body))
