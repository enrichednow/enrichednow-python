"""The resources of the API: scrapers, runs, usage, webhooks and the datasets reads. Each exists twice, sync and async."""
from __future__ import annotations

import time
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Mapping, Optional, Union

from ._base import (
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RUN_TIMEOUT,
    build_page,
    path_segment,
    posting_params,
    validate_wait,
)
from ._exceptions import WaitTimeoutError
from ._models import (
    Company,
    Posting,
    PostingDetail,
    Run,
    Scraper,
    ScraperDetails,
    Usage,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointList,
    WebhookEndpointWithSecret,
    WebhookSecret,
)
from ._pagination import AsyncPage, AsyncPaginator, AsyncRecordsPage, SyncPage, SyncRecordsPage

if TYPE_CHECKING:
    from ._client import AsyncEnrichedNow, EnrichedNow

__all__ = [
    "Scrapers", "AsyncScrapers", "Runs", "AsyncRuns", "UsageResource", "AsyncUsageResource",
    "Data", "AsyncData", "Postings", "AsyncPostings", "Companies", "AsyncCompanies",
    "Webhooks", "AsyncWebhooks", "WebhookDeliveries", "AsyncWebhookDeliveries",
]

Day = Union[date, str]
"""A day: a `date` or `YYYY-MM-DD`."""
Moment = Union[datetime, date, str]
"""A time: a `datetime`, a `date` (its start, UTC) or an ISO 8601 string."""
Provenance = Union[str, Iterable[str]]
"""`feed`, `page`, `board`, several of them, or `all`."""
Events = Union[str, Iterable[str]]
"""The run endings a webhook endpoint is told about: one or several of `enrichednow.WEBHOOK_EVENTS`."""


def _run_body(input: Mapping[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(input, Mapping):
        raise TypeError("input must be a mapping: the scraper's input, as its input_schema describes it")
    body: Dict[str, Any] = {"input": dict(input)}
    if webhook_url is not None:
        if not isinstance(webhook_url, str):
            raise TypeError("webhook_url must be a string: the https URL to tell when the run ends")
        body["webhook_url"] = webhook_url
    return body


def _events(events: Events) -> List[str]:
    if isinstance(events, str):
        return [events]
    if isinstance(events, (bytes, Mapping)) or not isinstance(events, Iterable):
        raise TypeError("events must be event names: one or several of enrichednow.WEBHOOK_EVENTS")
    return [str(name) for name in events]


def _endpoint_body(*, url: Optional[str], events: Optional[Events], description: Optional[str]) -> Dict[str, Any]:
    """What is given of an endpoint's url, events and description, as the API takes it."""
    body: Dict[str, Any] = {}
    if url is not None:
        if not isinstance(url, str):
            raise TypeError("url must be a string: the https URL of the endpoint")
        body["url"] = url
    if events is not None:
        body["events"] = _events(events)
    if description is not None:
        body["description"] = description
    return body


def _endpoint_change(*, url: Optional[str], events: Optional[Events], description: Optional[str], enabled: Optional[bool]) -> Dict[str, Any]:
    body = _endpoint_body(url=url, events=events, description=description)
    if enabled is not None:
        body["enabled"] = bool(enabled)
    if not body:
        raise ValueError("give at least one of url, events, description, enabled")
    return body


def _scrapers(payload: Any) -> List[Scraper]:
    rows = payload.get("scrapers") if isinstance(payload, Mapping) else None
    return [Scraper.from_dict(row) for row in rows] if isinstance(rows, list) else []


def _poll_interval(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError("poll_interval must be a number of seconds, 0 or more")
    return float(value)


# ======================================================================================================================
# sync
# ======================================================================================================================


class Scrapers:
    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self) -> List[Scraper]:
        """`GET /v1/scrapers`: the catalogue."""
        return _scrapers(self._client._request("GET", "/v1/scrapers"))

    def get(self, scraper_id: str) -> ScraperDetails:
        """`GET /v1/scrapers/{id}`: one scraper, with the JSON Schema of its input and of one record."""
        return ScraperDetails.from_dict(self._client._request("GET", f"/v1/scrapers/{path_segment(scraper_id)}"))

    def run(self, scraper_id: str, input: Mapping[str, Any], *, wait: Optional[float] = None,
            webhook_url: Optional[str] = None, idempotency_key: Optional[str] = None) -> Run:
        """`POST /v1/scrapers/{id}/runs`: start a run.

        `wait` (0 to 60 seconds) asks the API to hold the request until the run ends or the time is up. The run that
        comes back may still be `queued` or `running`: follow it with `client.runs.wait(run.id)`, or use
        `client.scrape()` to do both.

        `webhook_url` is an `https` URL that is sent a signed `POST` when this run ends, whichever way it ends,
        beside the account's webhook endpoints. The account needs a signing secret for these first:
        `client.webhooks.create_run_secret()`.

        The request carries an `Idempotency-Key`, so it is safe to send again: after a timeout or a 5xx it is
        retried with the same key, and the API answers with the run the first attempt started, never a second one.
        A key is made for each call; pass `idempotency_key` (your own text, up to 255 characters, no spaces) to make
        a call of yours repeatable across processes: for 24 hours the same key and the same request give the same run.
        """
        wait = validate_wait(wait)
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        return Run.from_dict(self._client._request(
            "POST", f"/v1/scrapers/{path_segment(scraper_id)}/runs", params={"wait": wait},
            json=_run_body(input, webhook_url), headers={"Idempotency-Key": key},
            timeout=self._client._timeout_for(wait),
        ))


class Runs:
    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def get(self, run_id: str) -> Run:
        """`GET /v1/runs/{id}`: the run as it is now."""
        return Run.from_dict(self._client._request("GET", f"/v1/runs/{path_segment(run_id)}"))

    def list(self, *, scraper_id: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> SyncPage[Run]:
        """`GET /v1/runs`: the account's runs, newest first. `limit` is the size of a page (1 to 100, default 20)."""
        def fetch(at: Optional[str]) -> SyncPage[Run]:
            payload = self._client._request("GET", "/v1/runs", params={"scraper_id": scraper_id, "status": status, "limit": limit, "cursor": at})
            return build_page(SyncPage, payload, "runs", Run.from_dict, fetch)

        return fetch(cursor)

    def cancel(self, run_id: str) -> Run:
        """`POST /v1/runs/{id}/cancel`: ask a run to stop. The answer is the run as it is at that moment; a running
        one usually still says `running`. A run that has ended is returned unchanged."""
        return Run.from_dict(self._client._request("POST", f"/v1/runs/{path_segment(run_id)}/cancel"))

    def wait(self, run_id: str, *, timeout: Optional[float] = DEFAULT_RUN_TIMEOUT, poll_interval: float = DEFAULT_POLL_INTERVAL) -> Run:
        """Poll a run until it has ended, and return it, however it ended.

        Raises `WaitTimeoutError` when the run is still going after `timeout` seconds (`None`: no limit). The run
        itself carries on.
        """
        poll_interval = _poll_interval(poll_interval)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            run = self.get(run_id)
            if run.is_terminal:
                return run
            if deadline is not None and time.monotonic() + poll_interval > deadline:
                raise WaitTimeoutError(run, float(timeout or 0))
            self._client._sleep(poll_interval)

    def records(self, run_id: str, *, limit: Optional[int] = None, cursor: Optional[str] = None) -> SyncRecordsPage:
        """`GET /v1/runs/{id}/records`: a run's records, in the order the run stored them.

        Iterate the result for every record; pages are fetched as they are reached. `limit` is the size of a page
        (1 to 1000, default 100). Records are kept 7 days after the run ended; after that the page is empty and its
        `expired` is true.
        """
        path = f"/v1/runs/{path_segment(run_id)}/records"

        def fetch(at: Optional[str]) -> SyncRecordsPage:
            payload = self._client._request("GET", path, params={"limit": limit, "cursor": at})
            return build_page(SyncRecordsPage, payload, "records", None, fetch)

        return fetch(cursor)


class UsageResource:
    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def get(self, *, from_: Optional[Day] = None, to: Optional[Day] = None, group_by: Optional[str] = None,
            product: Optional[str] = None) -> Usage:
        """`GET /v1/usage`: units used over a period.

        `from_` and `to` are days (UTC), both included; without them, the current calendar month up to today.
        `group_by` is `day` (the default), `scraper` or `product`. `product` keeps one of `scrapers` and `data`.
        """
        return Usage.from_dict(self._client._request(
            "GET", "/v1/usage", params={"from": from_, "to": to, "group_by": group_by, "product": product}))


class Postings:
    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(
        self,
        *,
        company_domain: Optional[str] = None,
        title: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        remote: Optional[bool] = None,
        employment_type: Optional[str] = None,
        seniority: Optional[str] = None,
        function: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        provenance: Optional[Provenance] = None,
        unmatched: Optional[bool] = None,
        posted_from: Optional[Day] = None,
        posted_to: Optional[Day] = None,
        first_seen_from: Optional[Moment] = None,
        first_seen_to: Optional[Moment] = None,
        last_seen_from: Optional[Moment] = None,
        last_seen_to: Optional[Moment] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> SyncPage[Posting]:
        """`GET /v1/data/postings`: search job postings, newest first. Every filter given must hold.

        `limit` is the size of a page (1 to 200, default 50). Each posting returned costs one data unit, so stop
        iterating when you have what you need.
        """
        params = posting_params(
            company_domain=company_domain, title=title, location=location, country=country, remote=remote,
            employment_type=employment_type, seniority=seniority, function=function, status=status, source=source,
            provenance=provenance, unmatched=unmatched, posted_from=posted_from, posted_to=posted_to,
            first_seen_from=first_seen_from, first_seen_to=first_seen_to, last_seen_from=last_seen_from,
            last_seen_to=last_seen_to, sort=sort, limit=limit, cursor=None)

        def fetch(at: Optional[str]) -> SyncPage[Posting]:
            payload = self._client._request("GET", "/v1/data/postings", params={**params, "cursor": at})
            return build_page(SyncPage, payload, "postings", Posting.from_dict, fetch)

        return fetch(cursor)

    def get(self, posting_id: str) -> PostingDetail:
        """`GET /v1/data/postings/{id}`: one posting, with its description and its history."""
        return PostingDetail.from_dict(self._client._request("GET", f"/v1/data/postings/{path_segment(posting_id)}"))


class Companies:
    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self, *, q: Optional[str] = None, ats: Optional[str] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> SyncPage[Company]:
        """`GET /v1/data/companies`: the companies held, by domain. `q` is text that must appear in the domain or in a
        name; `ats` is the applicant tracking system detected."""
        def fetch(at: Optional[str]) -> SyncPage[Company]:
            payload = self._client._request("GET", "/v1/data/companies", params={"q": q, "ats": ats, "limit": limit, "cursor": at})
            return build_page(SyncPage, payload, "companies", Company.from_dict, fetch)

        return fetch(cursor)

    def get(self, domain: str) -> Company:
        """`GET /v1/data/companies/{domain}`: one company. Any host of the company's domain will do."""
        return Company.from_dict(self._client._request("GET", f"/v1/data/companies/{path_segment(domain)}"))

    def postings(
        self,
        domain: str,
        *,
        title: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        remote: Optional[bool] = None,
        employment_type: Optional[str] = None,
        seniority: Optional[str] = None,
        function: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        provenance: Optional[Provenance] = None,
        unmatched: Optional[bool] = None,
        posted_from: Optional[Day] = None,
        posted_to: Optional[Day] = None,
        first_seen_from: Optional[Moment] = None,
        first_seen_to: Optional[Moment] = None,
        last_seen_from: Optional[Moment] = None,
        last_seen_to: Optional[Moment] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> SyncPage[Posting]:
        """`GET /v1/data/companies/{domain}/postings`: a company's postings, with the filters of the postings search."""
        path = f"/v1/data/companies/{path_segment(domain)}/postings"
        params = posting_params(
            title=title, location=location, country=country, remote=remote, employment_type=employment_type,
            seniority=seniority, function=function, status=status, source=source, provenance=provenance,
            unmatched=unmatched, posted_from=posted_from, posted_to=posted_to, first_seen_from=first_seen_from,
            first_seen_to=first_seen_to, last_seen_from=last_seen_from, last_seen_to=last_seen_to, sort=sort,
            limit=limit, cursor=None)

        def fetch(at: Optional[str]) -> SyncPage[Posting]:
            payload = self._client._request("GET", path, params={**params, "cursor": at})
            return build_page(SyncPage, payload, "postings", Posting.from_dict, fetch)

        return fetch(cursor)


class WebhookDeliveries:
    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client

    def list(self, *, endpoint_id: Optional[str] = None, run_id: Optional[str] = None, status: Optional[str] = None,
             limit: Optional[int] = None, cursor: Optional[str] = None) -> SyncPage[WebhookDelivery]:
        """`GET /v1/webhooks/deliveries`: the delivery log, newest first: one row for each event sent to each target,
        with how its last attempt went. A delivery stays 30 days after it ended.

        `endpoint_id`, `run_id` and `status` (`pending`, `succeeded`, `failed` or `cancelled`) narrow it. `limit` is
        the size of a page (1 to 100, default 20).
        """
        def fetch(at: Optional[str]) -> SyncPage[WebhookDelivery]:
            payload = self._client._request("GET", "/v1/webhooks/deliveries", params={
                "endpoint_id": endpoint_id, "run_id": run_id, "status": status, "limit": limit, "cursor": at})
            return build_page(SyncPage, payload, "deliveries", WebhookDelivery.from_dict, fetch)

        return fetch(cursor)

    def resend(self, delivery_id: str) -> WebhookDelivery:
        """`POST /v1/webhooks/deliveries/{id}/resend`: send a delivery again. The answer is a new delivery of the same
        event (the same `event_id` and body) to where the endpoint is now, with the full set of attempts.

        Not for a delivery that is still `pending`, nor for an endpoint that is switched off or deleted. Like
        starting a run, this request is not sent again after a timeout or a 5xx: the delivery may be queued.
        """
        return WebhookDelivery.from_dict(self._client._request(
            "POST", f"/v1/webhooks/deliveries/{path_segment(delivery_id)}/resend", idempotent=False))


class Webhooks:
    """Webhooks: the endpoints that are told when a run ends, their signing secrets, and the delivery log."""

    def __init__(self, client: "EnrichedNow") -> None:
        self._client = client
        self.deliveries = WebhookDeliveries(client)

    def list(self) -> WebhookEndpointList:
        """`GET /v1/webhooks`: the account's endpoints, and whether it has a secret for a run's own `webhook_url`.
        A signing secret is never listed."""
        return WebhookEndpointList.from_dict(self._client._request("GET", "/v1/webhooks"))

    def create(self, url: str, events: Events, *, description: Optional[str] = None) -> WebhookEndpointWithSecret:
        """`POST /v1/webhooks`: add an endpoint. Its signing secret is on the answer, and only there: store it.

        `url` must be `https`. `events` are the run endings to be told about (`enrichednow.WEBHOOK_EVENTS`):
        `run.succeeded`, `run.partial`, `run.failed`, `run.unsupported`, `run.cancelled`. `description` is a note
        for yourself.

        Like starting a run, this request is not sent again after a timeout or a 5xx: the endpoint may exist. Look
        at `client.webhooks.list()` before adding it again.
        """
        return WebhookEndpointWithSecret.from_dict(self._client._request(
            "POST", "/v1/webhooks", json=_endpoint_body(url=url, events=events, description=description), idempotent=False))

    def get(self, endpoint_id: str) -> WebhookEndpoint:
        """`GET /v1/webhooks/{id}`: one endpoint."""
        return WebhookEndpoint.from_dict(self._client._request("GET", f"/v1/webhooks/{path_segment(endpoint_id)}"))

    def update(self, endpoint_id: str, *, url: Optional[str] = None, events: Optional[Events] = None,
               description: Optional[str] = None, enabled: Optional[bool] = None) -> WebhookEndpoint:
        """`PATCH /v1/webhooks/{id}`: change an endpoint. Only what is given changes; give at least one.

        `enabled=False` switches it off: nothing more is queued for it, and what was waiting is cancelled.
        `enabled=True` switches it on again, also after it was switched off for failing.
        """
        body = _endpoint_change(url=url, events=events, description=description, enabled=enabled)
        return WebhookEndpoint.from_dict(self._client._request("PATCH", f"/v1/webhooks/{path_segment(endpoint_id)}", json=body))

    def delete(self, endpoint_id: str) -> None:
        """`DELETE /v1/webhooks/{id}`: delete an endpoint. Nothing more is sent to it; what was waiting is cancelled.
        Its past deliveries stay in the log."""
        self._client._request("DELETE", f"/v1/webhooks/{path_segment(endpoint_id)}")

    def rotate_secret(self, endpoint_id: str) -> WebhookEndpointWithSecret:
        """`POST /v1/webhooks/{id}/rotate-secret`: replace an endpoint's signing secret. The new one is on the answer,
        and only there: store it. The old one stops being used at once, for deliveries already queued too.

        After a timeout or a 5xx this request is sent again like any other: the secret that comes back is the one
        in use, whichever attempt made it.
        """
        return WebhookEndpointWithSecret.from_dict(self._client._request("POST", f"/v1/webhooks/{path_segment(endpoint_id)}/rotate-secret"))

    def create_run_secret(self) -> WebhookSecret:
        """`POST /v1/webhooks/run-secret`: make, or replace, the secret that signs what is sent to a run's own
        `webhook_url`. It is the account's, and it is on the answer only: store it. An account needs one before a
        run can name a `webhook_url`. Asking again replaces it."""
        return WebhookSecret.from_dict(self._client._request("POST", "/v1/webhooks/run-secret"))


class Data:
    """The datasets reads, under `/v1/data`."""

    def __init__(self, client: "EnrichedNow") -> None:
        self.postings = Postings(client)
        self.companies = Companies(client)


# ======================================================================================================================
# async
# ======================================================================================================================


class AsyncScrapers:
    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def list(self) -> List[Scraper]:
        """`GET /v1/scrapers`: the catalogue."""
        return _scrapers(await self._client._request("GET", "/v1/scrapers"))

    async def get(self, scraper_id: str) -> ScraperDetails:
        """`GET /v1/scrapers/{id}`: one scraper, with the JSON Schema of its input and of one record."""
        return ScraperDetails.from_dict(await self._client._request("GET", f"/v1/scrapers/{path_segment(scraper_id)}"))

    async def run(self, scraper_id: str, input: Mapping[str, Any], *, wait: Optional[float] = None,
                  webhook_url: Optional[str] = None, idempotency_key: Optional[str] = None) -> Run:
        """`POST /v1/scrapers/{id}/runs`: start a run.

        `wait` (0 to 60 seconds) asks the API to hold the request until the run ends or the time is up. The run that
        comes back may still be `queued` or `running`: follow it with `client.runs.wait(run.id)`, or use
        `client.scrape()` to do both.

        `webhook_url` is an `https` URL that is sent a signed `POST` when this run ends, whichever way it ends,
        beside the account's webhook endpoints. The account needs a signing secret for these first:
        `client.webhooks.create_run_secret()`.

        The request carries an `Idempotency-Key`, so it is safe to send again: after a timeout or a 5xx it is
        retried with the same key, and the API answers with the run the first attempt started, never a second one.
        A key is made for each call; pass `idempotency_key` (your own text, up to 255 characters, no spaces) to make
        a call of yours repeatable across processes: for 24 hours the same key and the same request give the same run.
        """
        wait = validate_wait(wait)
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        return Run.from_dict(await self._client._request(
            "POST", f"/v1/scrapers/{path_segment(scraper_id)}/runs", params={"wait": wait},
            json=_run_body(input, webhook_url), headers={"Idempotency-Key": key},
            timeout=self._client._timeout_for(wait),
        ))


class AsyncRuns:
    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def get(self, run_id: str) -> Run:
        """`GET /v1/runs/{id}`: the run as it is now."""
        return Run.from_dict(await self._client._request("GET", f"/v1/runs/{path_segment(run_id)}"))

    def list(self, *, scraper_id: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> AsyncPaginator[Run, AsyncPage[Run]]:
        """`GET /v1/runs`: the account's runs, newest first. Await it for a page, or `async for` over every run."""
        async def fetch(at: Optional[str]) -> AsyncPage[Run]:
            payload = await self._client._request("GET", "/v1/runs", params={"scraper_id": scraper_id, "status": status, "limit": limit, "cursor": at})
            return build_page(AsyncPage, payload, "runs", Run.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def cancel(self, run_id: str) -> Run:
        """`POST /v1/runs/{id}/cancel`: ask a run to stop. The answer is the run as it is at that moment; a running
        one usually still says `running`. A run that has ended is returned unchanged."""
        return Run.from_dict(await self._client._request("POST", f"/v1/runs/{path_segment(run_id)}/cancel"))

    async def wait(self, run_id: str, *, timeout: Optional[float] = DEFAULT_RUN_TIMEOUT, poll_interval: float = DEFAULT_POLL_INTERVAL) -> Run:
        """Poll a run until it has ended, and return it, however it ended.

        Raises `WaitTimeoutError` when the run is still going after `timeout` seconds (`None`: no limit). The run
        itself carries on.
        """
        poll_interval = _poll_interval(poll_interval)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            run = await self.get(run_id)
            if run.is_terminal:
                return run
            if deadline is not None and time.monotonic() + poll_interval > deadline:
                raise WaitTimeoutError(run, float(timeout or 0))
            await self._client._sleep(poll_interval)

    def records(self, run_id: str, *, limit: Optional[int] = None, cursor: Optional[str] = None) -> AsyncPaginator[Dict[str, Any], AsyncRecordsPage]:
        """`GET /v1/runs/{id}/records`: a run's records, in the order the run stored them.

        `async for` over the result for every record, or await it for the first page. `limit` is the size of a page
        (1 to 1000, default 100). Records are kept 7 days after the run ended; after that the page is empty and its
        `expired` is true.
        """
        path = f"/v1/runs/{path_segment(run_id)}/records"

        async def fetch(at: Optional[str]) -> AsyncRecordsPage:
            payload = await self._client._request("GET", path, params={"limit": limit, "cursor": at})
            return build_page(AsyncRecordsPage, payload, "records", None, fetch)

        return AsyncPaginator(fetch, cursor)


class AsyncUsageResource:
    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    async def get(self, *, from_: Optional[Day] = None, to: Optional[Day] = None, group_by: Optional[str] = None,
                  product: Optional[str] = None) -> Usage:
        """`GET /v1/usage`: units used over a period.

        `from_` and `to` are days (UTC), both included; without them, the current calendar month up to today.
        `group_by` is `day` (the default), `scraper` or `product`. `product` keeps one of `scrapers` and `data`.
        """
        return Usage.from_dict(await self._client._request(
            "GET", "/v1/usage", params={"from": from_, "to": to, "group_by": group_by, "product": product}))


class AsyncPostings:
    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    def list(
        self,
        *,
        company_domain: Optional[str] = None,
        title: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        remote: Optional[bool] = None,
        employment_type: Optional[str] = None,
        seniority: Optional[str] = None,
        function: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        provenance: Optional[Provenance] = None,
        unmatched: Optional[bool] = None,
        posted_from: Optional[Day] = None,
        posted_to: Optional[Day] = None,
        first_seen_from: Optional[Moment] = None,
        first_seen_to: Optional[Moment] = None,
        last_seen_from: Optional[Moment] = None,
        last_seen_to: Optional[Moment] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncPaginator[Posting, AsyncPage[Posting]]:
        """`GET /v1/data/postings`: search job postings, newest first. Every filter given must hold.

        `limit` is the size of a page (1 to 200, default 50). Each posting returned costs one data unit, so stop
        iterating when you have what you need.
        """
        params = posting_params(
            company_domain=company_domain, title=title, location=location, country=country, remote=remote,
            employment_type=employment_type, seniority=seniority, function=function, status=status, source=source,
            provenance=provenance, unmatched=unmatched, posted_from=posted_from, posted_to=posted_to,
            first_seen_from=first_seen_from, first_seen_to=first_seen_to, last_seen_from=last_seen_from,
            last_seen_to=last_seen_to, sort=sort, limit=limit, cursor=None)

        async def fetch(at: Optional[str]) -> AsyncPage[Posting]:
            payload = await self._client._request("GET", "/v1/data/postings", params={**params, "cursor": at})
            return build_page(AsyncPage, payload, "postings", Posting.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def get(self, posting_id: str) -> PostingDetail:
        """`GET /v1/data/postings/{id}`: one posting, with its description and its history."""
        return PostingDetail.from_dict(await self._client._request("GET", f"/v1/data/postings/{path_segment(posting_id)}"))


class AsyncCompanies:
    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    def list(self, *, q: Optional[str] = None, ats: Optional[str] = None, limit: Optional[int] = None,
             cursor: Optional[str] = None) -> AsyncPaginator[Company, AsyncPage[Company]]:
        """`GET /v1/data/companies`: the companies held, by domain. `q` is text that must appear in the domain or in a
        name; `ats` is the applicant tracking system detected."""
        async def fetch(at: Optional[str]) -> AsyncPage[Company]:
            payload = await self._client._request("GET", "/v1/data/companies", params={"q": q, "ats": ats, "limit": limit, "cursor": at})
            return build_page(AsyncPage, payload, "companies", Company.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def get(self, domain: str) -> Company:
        """`GET /v1/data/companies/{domain}`: one company. Any host of the company's domain will do."""
        return Company.from_dict(await self._client._request("GET", f"/v1/data/companies/{path_segment(domain)}"))

    def postings(
        self,
        domain: str,
        *,
        title: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        remote: Optional[bool] = None,
        employment_type: Optional[str] = None,
        seniority: Optional[str] = None,
        function: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        provenance: Optional[Provenance] = None,
        unmatched: Optional[bool] = None,
        posted_from: Optional[Day] = None,
        posted_to: Optional[Day] = None,
        first_seen_from: Optional[Moment] = None,
        first_seen_to: Optional[Moment] = None,
        last_seen_from: Optional[Moment] = None,
        last_seen_to: Optional[Moment] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncPaginator[Posting, AsyncPage[Posting]]:
        """`GET /v1/data/companies/{domain}/postings`: a company's postings, with the filters of the postings search."""
        path = f"/v1/data/companies/{path_segment(domain)}/postings"
        params = posting_params(
            title=title, location=location, country=country, remote=remote, employment_type=employment_type,
            seniority=seniority, function=function, status=status, source=source, provenance=provenance,
            unmatched=unmatched, posted_from=posted_from, posted_to=posted_to, first_seen_from=first_seen_from,
            first_seen_to=first_seen_to, last_seen_from=last_seen_from, last_seen_to=last_seen_to, sort=sort,
            limit=limit, cursor=None)

        async def fetch(at: Optional[str]) -> AsyncPage[Posting]:
            payload = await self._client._request("GET", path, params={**params, "cursor": at})
            return build_page(AsyncPage, payload, "postings", Posting.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)


class AsyncWebhookDeliveries:
    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client

    def list(self, *, endpoint_id: Optional[str] = None, run_id: Optional[str] = None, status: Optional[str] = None,
             limit: Optional[int] = None, cursor: Optional[str] = None) -> AsyncPaginator[WebhookDelivery, AsyncPage[WebhookDelivery]]:
        """`GET /v1/webhooks/deliveries`: the delivery log, newest first: one row for each event sent to each target,
        with how its last attempt went. A delivery stays 30 days after it ended.

        `endpoint_id`, `run_id` and `status` (`pending`, `succeeded`, `failed` or `cancelled`) narrow it. `limit` is
        the size of a page (1 to 100, default 20). Await it for a page, or `async for` over every delivery.
        """
        async def fetch(at: Optional[str]) -> AsyncPage[WebhookDelivery]:
            payload = await self._client._request("GET", "/v1/webhooks/deliveries", params={
                "endpoint_id": endpoint_id, "run_id": run_id, "status": status, "limit": limit, "cursor": at})
            return build_page(AsyncPage, payload, "deliveries", WebhookDelivery.from_dict, fetch)

        return AsyncPaginator(fetch, cursor)

    async def resend(self, delivery_id: str) -> WebhookDelivery:
        """`POST /v1/webhooks/deliveries/{id}/resend`: send a delivery again. The answer is a new delivery of the same
        event (the same `event_id` and body) to where the endpoint is now, with the full set of attempts.

        Not for a delivery that is still `pending`, nor for an endpoint that is switched off or deleted. Like
        starting a run, this request is not sent again after a timeout or a 5xx: the delivery may be queued.
        """
        return WebhookDelivery.from_dict(await self._client._request(
            "POST", f"/v1/webhooks/deliveries/{path_segment(delivery_id)}/resend", idempotent=False))


class AsyncWebhooks:
    """Webhooks: the endpoints that are told when a run ends, their signing secrets, and the delivery log."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self._client = client
        self.deliveries = AsyncWebhookDeliveries(client)

    async def list(self) -> WebhookEndpointList:
        """`GET /v1/webhooks`: the account's endpoints, and whether it has a secret for a run's own `webhook_url`.
        A signing secret is never listed."""
        return WebhookEndpointList.from_dict(await self._client._request("GET", "/v1/webhooks"))

    async def create(self, url: str, events: Events, *, description: Optional[str] = None) -> WebhookEndpointWithSecret:
        """`POST /v1/webhooks`: add an endpoint. Its signing secret is on the answer, and only there: store it.

        `url` must be `https`. `events` are the run endings to be told about (`enrichednow.WEBHOOK_EVENTS`):
        `run.succeeded`, `run.partial`, `run.failed`, `run.unsupported`, `run.cancelled`. `description` is a note
        for yourself.

        Like starting a run, this request is not sent again after a timeout or a 5xx: the endpoint may exist. Look
        at `client.webhooks.list()` before adding it again.
        """
        return WebhookEndpointWithSecret.from_dict(await self._client._request(
            "POST", "/v1/webhooks", json=_endpoint_body(url=url, events=events, description=description), idempotent=False))

    async def get(self, endpoint_id: str) -> WebhookEndpoint:
        """`GET /v1/webhooks/{id}`: one endpoint."""
        return WebhookEndpoint.from_dict(await self._client._request("GET", f"/v1/webhooks/{path_segment(endpoint_id)}"))

    async def update(self, endpoint_id: str, *, url: Optional[str] = None, events: Optional[Events] = None,
               description: Optional[str] = None, enabled: Optional[bool] = None) -> WebhookEndpoint:
        """`PATCH /v1/webhooks/{id}`: change an endpoint. Only what is given changes; give at least one.

        `enabled=False` switches it off: nothing more is queued for it, and what was waiting is cancelled.
        `enabled=True` switches it on again, also after it was switched off for failing.
        """
        body = _endpoint_change(url=url, events=events, description=description, enabled=enabled)
        return WebhookEndpoint.from_dict(await self._client._request("PATCH", f"/v1/webhooks/{path_segment(endpoint_id)}", json=body))

    async def delete(self, endpoint_id: str) -> None:
        """`DELETE /v1/webhooks/{id}`: delete an endpoint. Nothing more is sent to it; what was waiting is cancelled.
        Its past deliveries stay in the log."""
        await self._client._request("DELETE", f"/v1/webhooks/{path_segment(endpoint_id)}")

    async def rotate_secret(self, endpoint_id: str) -> WebhookEndpointWithSecret:
        """`POST /v1/webhooks/{id}/rotate-secret`: replace an endpoint's signing secret. The new one is on the answer,
        and only there: store it. The old one stops being used at once, for deliveries already queued too.

        After a timeout or a 5xx this request is sent again like any other: the secret that comes back is the one
        in use, whichever attempt made it.
        """
        return WebhookEndpointWithSecret.from_dict(await self._client._request("POST", f"/v1/webhooks/{path_segment(endpoint_id)}/rotate-secret"))

    async def create_run_secret(self) -> WebhookSecret:
        """`POST /v1/webhooks/run-secret`: make, or replace, the secret that signs what is sent to a run's own
        `webhook_url`. It is the account's, and it is on the answer only: store it. An account needs one before a
        run can name a `webhook_url`. Asking again replaces it."""
        return WebhookSecret.from_dict(await self._client._request("POST", "/v1/webhooks/run-secret"))


class AsyncData:
    """The datasets reads, under `/v1/data`."""

    def __init__(self, client: "AsyncEnrichedNow") -> None:
        self.postings = AsyncPostings(client)
        self.companies = AsyncCompanies(client)

