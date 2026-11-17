from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict

import pytest

from conftest import FakeAPI, error_json, ok
from enrichednow import PermissionDeniedError, QuotaExceededError, ServerError, ValidationError


def posting_json(**over: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "id": "pst_1",
        "title": "Senior Software Engineer (m/f/d)",
        "title_clean": "Senior Software Engineer",
        "company": {"domain": "acme.com", "name": "Acme"},
        "location": {"raw": "Berlin, Germany", "city": "Berlin", "region": None, "country": "Germany", "country_code": "DE", "remote": False},
        "employment_type": "full_time",
        "salary": {"raw": "€80k–€100k", "min": 80000, "max": 100000, "currency": "EUR", "period": "year"},
        "posted_at": "2026-11-10",
        "valid_through": None,
        "seniority": "senior",
        "function": "engineering",
        "url": "https://boards.greenhouse.io/acme/jobs/1",
        "apply_url": None,
        "source": {"name": "greenhouse", "provenance": "feed", "trusted": True, "external_id": "1"},
        "status": "open",
        "first_seen_at": "2026-11-10T08:00:00Z",
        "last_seen_at": "2026-11-18T08:00:00Z",
        "closed_at": None,
    }
    body.update(over)
    return body


COMPANY = {
    "domain": "acme.com", "name": "Acme", "names": [{"name": "Acme", "first_seen_at": "2026-10-01T00:00:00Z", "last_seen_at": "2026-11-18T00:00:00Z"}],
    "careers_url": "https://acme.com/careers", "ats": "greenhouse", "first_seen_at": "2026-10-01T00:00:00Z", "last_seen_at": "2026-11-18T00:00:00Z",
    "last_read": {"at": "2026-11-18T00:00:00Z", "status": "complete", "last_complete_at": "2026-11-18T00:00:00Z"},
    "postings": {"open": 12, "closed": 3},
}


def test_postings_list_sends_every_filter_as_the_api_reads_it(api: FakeAPI) -> None:
    api.reply(ok({"postings": [posting_json()], "next_cursor": None}))
    page = api.client().data.postings.list(
        company_domain="acme.com", title="software engineer", location="Berlin", country="DE", remote=False,
        employment_type="full_time", seniority="senior", function="engineering", status="open", source="greenhouse",
        provenance=["feed", "page"], unmatched=True, posted_from=date(2026, 11, 1), posted_to="2026-11-18",
        first_seen_from=datetime(2026, 11, 1, tzinfo=timezone.utc), first_seen_to="2026-11-18", last_seen_from=date(2026, 11, 16),
        last_seen_to="2026-11-19T00:00:00Z", sort="last_seen_at", limit=200)
    sent = api.sent()
    assert (sent["method"], sent["path"]) == ("GET", "/v1/data/postings")
    assert sent["params"] == {
        "company_domain": "acme.com", "title": "software engineer", "location": "Berlin", "country": "DE", "remote": "false",
        "employment_type": "full_time", "seniority": "senior", "function": "engineering", "status": "open", "source": "greenhouse",
        "provenance": "feed,page", "unmatched": "true", "posted_from": "2026-11-01", "posted_to": "2026-11-18",
        "first_seen_from": "2026-11-01T00:00:00+00:00", "first_seen_to": "2026-11-18", "last_seen_from": "2026-11-16",
        "last_seen_to": "2026-11-19T00:00:00Z", "sort": "last_seen_at", "limit": "200",
    }
    posting = page.items[0]
    assert posting.title_clean == "Senior Software Engineer" and posting.company.domain == "acme.com"
    assert posting.location.raw_text == "Berlin, Germany" and posting.location.country_code == "DE" and posting.location.remote is False
    assert posting.salary is not None and (posting.salary.min, posting.salary.currency, posting.salary.raw_text) == (80000, "EUR", "€80k–€100k")
    assert posting.posted_at == date(2026, 11, 10) and posting.valid_through is None and posting.closed_at is None
    assert posting.source.provenance == "feed" and posting.source.trusted is True
    assert posting.first_seen_at == datetime(2026, 11, 10, 8, tzinfo=timezone.utc)


def test_postings_list_keeps_the_filters_on_the_next_page(api: FakeAPI) -> None:
    api.reply(ok({"postings": [posting_json(id="pst_2")], "next_cursor": "WyJ4Il0"}), ok({"postings": [posting_json(id="pst_1")], "next_cursor": None}))
    ids = [p.id for p in api.client().data.postings.list(status="open", limit=1)]
    assert ids == ["pst_2", "pst_1"]
    assert api.sent(0)["params"] == {"status": "open", "limit": "1"}
    assert api.sent(1)["params"] == {"status": "open", "limit": "1", "cursor": "WyJ4Il0"}


def test_postings_get(api: FakeAPI) -> None:
    api.reply(ok(posting_json(
        description="We build things.", classification={"seniority_rule": "title:senior", "function_rule": None},
        history={"events": [{"kind": "first_seen", "at": "2026-11-10T08:00:00Z"}],
                 "changes": [{"field": "title", "old": "Engineer", "new": "Senior Engineer", "at": "2026-11-12T08:00:00Z"}],
                 "sightings": {"count": 2, "recent": ["2026-11-18T08:00:00Z", "2026-11-17T08:00:00Z"]}, "reopened_count": 0})))
    posting = api.client().data.postings.get("pst_1")
    assert api.sent()["path"] == "/v1/data/postings/pst_1"
    assert posting.description == "We build things." and posting.classification.seniority_rule == "title:senior"
    assert posting.history.events[0].kind == "first_seen" and posting.history.reopened_count == 0
    assert (posting.history.changes[0].field, posting.history.changes[0].old, posting.history.changes[0].new) == ("title", "Engineer", "Senior Engineer")
    assert posting.history.sightings.count == 2 and posting.history.sightings.recent[0] == datetime(2026, 11, 18, 8, tzinfo=timezone.utc)
    assert posting.id == "pst_1" and posting.status == "open"


def test_companies_list_and_get(api: FakeAPI) -> None:
    api.reply(ok({"companies": [COMPANY], "next_cursor": None}), ok(COMPANY))
    client = api.client()
    page = client.data.companies.list(q="acme", ats="greenhouse", limit=10)
    assert api.sent()["path"] == "/v1/data/companies" and api.sent()["params"] == {"q": "acme", "ats": "greenhouse", "limit": "10"}
    assert page.items[0].domain == "acme.com" and page.items[0].postings.open == 12 and page.items[0].postings.closed == 3
    company = client.data.companies.get("www.acme.com")
    assert api.sent()["path"] == "/v1/data/companies/www.acme.com"
    assert company.names[0].name == "Acme" and company.last_read.status == "complete" and company.ats == "greenhouse"
    assert company.last_read.last_complete_at == datetime(2026, 11, 18, tzinfo=timezone.utc)


def test_company_postings(api: FakeAPI) -> None:
    api.reply(ok({"postings": [posting_json()], "next_cursor": "bmV4dA"}), ok({"postings": [], "next_cursor": None}))
    postings = api.client().data.companies.postings("acme.com", title="engineer", remote=True, status="open").to_list()
    assert len(postings) == 1
    assert api.sent(0)["path"] == "/v1/data/companies/acme.com/postings"
    assert api.sent(0)["params"] == {"title": "engineer", "remote": "true", "status": "open"}
    assert api.sent(1)["params"] == {"title": "engineer", "remote": "true", "status": "open", "cursor": "bmV4dA"}


@pytest.mark.parametrize("status, code, kind", [(403, "forbidden", PermissionDeniedError), (402, "quota_exceeded", QuotaExceededError),
                                                (422, "invalid_input", ValidationError), (503, "data_unavailable", ServerError)])
def test_the_errors_of_a_data_request(api: FakeAPI, status: int, code: str, kind: type) -> None:
    api.reply(ok(error_json(code), status=status))
    with pytest.raises(kind) as caught:
        api.client(max_retries=0).data.postings.list()
    assert caught.value.code == code  # type: ignore[attr-defined]


def test_a_sparse_answer_does_not_break_parsing(api: FakeAPI) -> None:
    api.reply(ok({"postings": [{"id": "pst_1", "brand_new_field": {"a": 1}}], "next_cursor": None}))
    posting = api.client().data.postings.list().items[0]
    assert posting.id == "pst_1" and posting.salary is None and posting.company.domain is None and posting.location.city is None
    assert posting.raw["brand_new_field"] == {"a": 1} and posting.to_dict() == {"id": "pst_1", "brand_new_field": {"a": 1}}
