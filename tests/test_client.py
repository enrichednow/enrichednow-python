from __future__ import annotations

from datetime import date, datetime, timezone

import httpx
import pytest

import enrichednow
from conftest import KEY, FakeAPI, error_json, ok, run_json
from enrichednow import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    EnrichedNow,
    EnrichedNowError,
    MissingAPIKeyError,
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    QuotaExceededError,
    RateLimitError,
    RunFailedError,
    ServerError,
    ValidationError,
    WaitTimeoutError,
)

# --- configuration ----------------------------------------------------------------------------------------------------


def test_the_key_is_sent_as_a_bearer_token_with_the_user_agent(api: FakeAPI) -> None:
    api.reply(ok({"status": "ok"}))
    assert api.client().health().status == "ok"
    assert api.last.headers["authorization"] == f"Bearer {KEY}"
    assert api.last.headers["user-agent"] == f"enrichednow-python/{enrichednow.__version__}"
    assert str(api.last.url) == "https://api.enrichednow.com/v1/health"


def test_the_key_falls_back_to_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENRICHEDNOW_API_KEY", "en_live_from_env")
    assert EnrichedNow().api_key == "en_live_from_env"
    assert EnrichedNow("en_live_given").api_key == "en_live_given"


def test_no_key_is_a_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENRICHEDNOW_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError, match="ENRICHEDNOW_API_KEY"):
        EnrichedNow()
    with pytest.raises(EnrichedNowError):
        enrichednow.AsyncEnrichedNow(api_key="  ")


def test_base_url_is_configurable_and_the_key_is_not_in_the_repr(api: FakeAPI) -> None:
    api.reply(ok({"status": "ok"}))
    client = api.client(base_url="http://localhost:8080/")
    client.health()
    assert str(api.last.url) == "http://localhost:8080/v1/health"
    assert KEY not in repr(client)


def test_version() -> None:
    assert enrichednow.__version__ == "0.3.0"


# --- scrapers ---------------------------------------------------------------------------------------------------------

CARD = {"id": "ats.board", "version": 3, "title": "ATS board", "summary": "Reads a board.", "mode": "job",
        "billing_unit": "record", "units_per_request": None, "units_per_record": 4, "data_class": "public", "availability": "public"}


def test_scrapers_list(api: FakeAPI) -> None:
    api.reply(ok({"scrapers": [CARD, {**CARD, "id": "web.fetch", "something_new": 1}]}))
    scrapers = api.client().scrapers.list()
    assert api.sent() == {"method": "GET", "path": "/v1/scrapers", "raw_path": "/v1/scrapers", "params": {}, "json": None}
    assert [s.id for s in scrapers] == ["ats.board", "web.fetch"]
    assert scrapers[0].billing_unit == "record" and scrapers[0].version == 3
    assert (scrapers[0].units_per_record, scrapers[0].units_per_request, scrapers[0].unit_cost) == (4, None, 4)
    old = {k: v for k, v in CARD.items() if not k.startswith("units_per")}          # an API from before costs differed
    api.answers.clear()
    api.reply(ok({"scrapers": [old]}))
    assert api.client().scrapers.list()[0].unit_cost == 1
    assert scrapers[1].raw["something_new"] == 1          # a field this version does not know is kept, not a failure


def test_scrapers_get(api: FakeAPI) -> None:
    api.reply(ok({**CARD, "input_schema": {"type": "object"}, "record_schema": {"title": "Job"}}))
    scraper = api.client().scrapers.get("ats.board")
    assert api.sent()["path"] == "/v1/scrapers/ats.board"
    assert scraper.input_schema == {"type": "object"} and scraper.record_schema == {"title": "Job"}


def test_an_id_is_one_path_segment(api: FakeAPI) -> None:
    api.reply(ok(run_json()))
    api.client().runs.get("../keys?x=1")
    assert api.sent()["raw_path"] == "/v1/runs/..%2Fkeys%3Fx%3D1"
    with pytest.raises(ValueError):
        api.client().runs.get("")


def test_scrapers_run(api: FakeAPI) -> None:
    api.reply(ok(run_json("queued"), status=202))
    run = api.client().scrapers.run("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})
    sent = api.sent()
    assert (sent["method"], sent["path"], sent["params"]) == ("POST", "/v1/scrapers/ats.board/runs", {})
    assert sent["json"] == {"input": {"board_url": "https://boards.greenhouse.io/acme"}}
    assert run.status == "queued" and run.is_active and not run.is_terminal
    assert run.diagnostics is None and run.finished_at is None


def test_scrapers_run_with_wait_holds_the_request_longer_than_the_wait(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok")))
    run = api.client(timeout=10).scrapers.run("ats.board", {"board_url": "x"}, wait=60)
    assert api.sent()["params"] == {"wait": "60"}
    assert api.last.extensions["timeout"]["read"] == 90
    assert run.succeeded and run.record_count == 2 and run.units == 2
    assert run.diagnostics is not None and run.diagnostics.facts == {"ats": "greenhouse"} and run.diagnostics.requests == 4
    assert run.created_at == datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc)
    assert run.started_at == datetime(2026, 11, 18, 10, 0, 1, 123456, tzinfo=timezone.utc)
    assert run.finished_at == datetime(2026, 11, 18, 10, 0, 2, 500000, tzinfo=timezone.utc)


def test_scrapers_run_refuses_a_wait_the_api_would_refuse(api: FakeAPI) -> None:
    with pytest.raises(ValueError):
        api.client().scrapers.run("ats.board", {}, wait=301)
    with pytest.raises(TypeError):
        api.client().scrapers.run("ats.board", "not a mapping")  # type: ignore[arg-type]
    assert api.requests == []


# --- runs -------------------------------------------------------------------------------------------------------------


def test_runs_get_and_cancel(api: FakeAPI) -> None:
    api.reply(ok(run_json("running")), ok(run_json("cancelled", reason="cancelled")))
    client = api.client()
    assert client.runs.get("run_1").status == "running"
    assert api.sent() == {"method": "GET", "path": "/v1/runs/run_1", "raw_path": "/v1/runs/run_1", "params": {}, "json": None}
    cancelled = client.runs.cancel("run_1")
    assert (api.sent()["method"], api.sent()["path"]) == ("POST", "/v1/runs/run_1/cancel")
    assert cancelled.status == "cancelled" and cancelled.reason == "cancelled" and cancelled.failed


def test_runs_list_pages(api: FakeAPI) -> None:
    api.reply(ok({"runs": [run_json(id="run_3"), run_json(id="run_2")], "next_cursor": "abc"}),
              ok({"runs": [run_json(id="run_1")], "next_cursor": None}))
    page = api.client().runs.list(scraper_id="ats.board", status="ok", limit=2)
    assert api.sent()["params"] == {"scraper_id": "ats.board", "status": "ok", "limit": "2"}
    assert [r.id for r in page.items] == ["run_3", "run_2"] and page.has_next_page() and page.next_cursor == "abc"
    assert [r.id for r in page] == ["run_3", "run_2", "run_1"]
    assert api.sent()["params"] == {"scraper_id": "ats.board", "status": "ok", "limit": "2", "cursor": "abc"}


def test_runs_records_auto_paginates(api: FakeAPI) -> None:
    api.reply(ok({"records": [{"n": 1}, {"n": 2}], "next_cursor": "Mg"}),
              ok({"records": [{"n": 3}, {"n": 4}], "next_cursor": "NA"}),
              ok({"records": [{"n": 5}], "next_cursor": None}))
    records = list(api.client().runs.records("run_1", limit=2))
    assert records == [{"n": 1}, {"n": 2}, {"n": 3}, {"n": 4}, {"n": 5}]
    assert [api.sent(i)["params"] for i in range(3)] == [{"limit": "2"}, {"limit": "2", "cursor": "Mg"}, {"limit": "2", "cursor": "NA"}]
    assert all(api.sent(i)["path"] == "/v1/runs/run_1/records" for i in range(3))


def test_runs_records_page_by_page(api: FakeAPI) -> None:
    api.reply(ok({"records": [{"n": 1}], "next_cursor": "MQ"}), ok({"records": [{"n": 2}], "next_cursor": None}))
    first = api.client().runs.records("run_1", cursor=None)
    assert first.items == [{"n": 1}] and len(first) == 1 and first.expired is False
    assert len(api.requests) == 1                          # the next page is not fetched until it is asked for
    second = first.next_page()
    assert second is not None and second.items == [{"n": 2}] and not second.has_next_page()
    assert second.next_page() is None


def test_runs_records_start_from_a_cursor_and_iter_pages(api: FakeAPI) -> None:
    api.reply(ok({"records": [{"n": 3}], "next_cursor": "NA"}), ok({"records": [], "next_cursor": None}))
    pages = list(api.client().runs.records("run_1", cursor="Mg").iter_pages())
    assert api.sent(0)["params"] == {"cursor": "Mg"} and api.sent(1)["params"] == {"cursor": "NA"}
    assert [p.items for p in pages] == [[{"n": 3}], []]


def test_expired_records(api: FakeAPI) -> None:
    api.reply(ok({"records": [], "next_cursor": None, "expired": True}))
    page = api.client().runs.records("run_1")
    assert page.expired is True and page.to_list() == []


def test_runs_wait_polls_until_the_run_ends(api: FakeAPI) -> None:
    api.reply(ok(run_json("queued")), ok(run_json("running")), ok(run_json("partial", reason="deadline_exceeded")))
    run = api.client().runs.wait("run_1", poll_interval=3)
    assert run.status == "partial" and run.reason == "deadline_exceeded"
    assert len(api.requests) == 3 and api.slept == [3.0, 3.0]


def test_runs_wait_returns_a_failed_run_without_raising(api: FakeAPI) -> None:
    api.reply(ok(run_json("failed")))
    run = api.client().runs.wait("run_1")
    assert run.status == "failed"
    with pytest.raises(RunFailedError):
        run.raise_for_status()


def test_runs_wait_gives_up_after_the_timeout(api: FakeAPI) -> None:
    api.reply(ok(run_json("running")))
    with pytest.raises(WaitTimeoutError) as caught:
        api.client().runs.wait("run_1", timeout=0)
    assert caught.value.run.status == "running" and caught.value.run_id == "run_1" and caught.value.timeout == 0
    assert len(api.requests) == 1 and api.slept == []


# --- usage ------------------------------------------------------------------------------------------------------------


def test_usage(api: FakeAPI) -> None:
    api.reply(ok({"period": {"from": "2026-11-01", "to": "2026-11-18"}, "total_units": 12, "allowance_units": 1000,
                  "rows": [{"key": "ats.board", "units": 12, "runs": 3}]}))
    usage = api.client().usage.get(from_=date(2026, 11, 1), to="2026-11-18", group_by="scraper", product="scrapers")
    sent = api.sent()
    assert sent["path"] == "/v1/usage"
    assert sent["params"] == {"from": "2026-11-01", "to": "2026-11-18", "group_by": "scraper", "product": "scrapers"}
    assert usage.period.from_ == date(2026, 11, 1) and usage.period.to == date(2026, 11, 18)
    assert usage.total_units == 12 and usage.allowance_units == 1000
    assert (usage.rows[0].key, usage.rows[0].units, usage.rows[0].runs) == ("ats.board", 12, 3)


def test_usage_defaults_send_nothing(api: FakeAPI) -> None:
    api.reply(ok({"period": {"from": "2026-11-01", "to": "2026-11-18"}, "total_units": 0, "allowance_units": 1000, "rows": []}))
    assert api.client().usage.get().rows == []
    assert api.sent()["params"] == {}


# --- the one-liner ----------------------------------------------------------------------------------------------------


def test_scrape_returns_the_run_and_its_records(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok")), ok({"records": [{"title": "Engineer"}], "next_cursor": "MQ"}),
              ok({"records": [{"title": "Designer"}], "next_cursor": None}))
    result = api.client().scrape("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})
    assert api.sent(0)["params"] == {"wait": "60"} and api.sent(0)["method"] == "POST"
    assert result.run.status == "ok" and len(api.requests) == 1          # records are fetched when they are read
    assert [r["title"] for r in result.records] == ["Engineer", "Designer"]
    assert api.sent(1)["path"] == "/v1/runs/run_1/records" and api.sent(1)["params"] == {"limit": "1000"}


def test_scrape_polls_when_the_wait_runs_out(api: FakeAPI) -> None:
    api.reply(ok(run_json("running"), status=202), ok(run_json("running")), ok(run_json("ok")), ok({"records": [{"n": 1}], "next_cursor": None}))
    result = api.client().scrape("ats.board", {"board_url": "x"}, poll_interval=1)
    assert [api.sent(i)["path"] for i in range(3)] == ["/v1/scrapers/ats.board/runs", "/v1/runs/run_1", "/v1/runs/run_1"]
    assert api.slept == [1.0]
    assert list(result) == [{"n": 1}]


@pytest.mark.parametrize("status, reason", [("failed", "fetch_failed"), ("unsupported", "render_required"), ("cancelled", "cancelled")])
def test_scrape_raises_when_the_run_did_not_succeed(api: FakeAPI, status: str, reason: str) -> None:
    api.reply(ok(run_json(status, reason=reason)))
    with pytest.raises(RunFailedError) as caught:
        api.client().scrape("ats.board", {"board_url": "x"})
    error = caught.value
    assert (error.status, error.reason, error.run_id, error.run.scraper_id) == (status, reason, "run_1", "ats.board")
    assert status in str(error) and reason in str(error)
    assert isinstance(error, EnrichedNowError)


def test_scrape_can_return_a_failed_run_instead(api: FakeAPI) -> None:
    api.reply(ok(run_json("failed")))
    result = api.client().scrape("ats.board", {"board_url": "x"}, raise_on_failure=False)
    assert result.run.status == "failed" and result.run.reason == "fetch_failed"


def test_scrape_returns_a_partial_run(api: FakeAPI) -> None:
    api.reply(ok(run_json("partial", reason="deadline_exceeded")))
    assert api.client().scrape("ats.board", {"board_url": "x"}).run.status == "partial"


def test_scrape_gives_up_after_the_timeout(api: FakeAPI) -> None:
    api.reply(ok(run_json("running"), status=202))
    with pytest.raises(WaitTimeoutError):
        api.client().scrape("ats.board", {"board_url": "x"}, timeout=5)
    assert api.sent(0)["params"] == {"wait": "5"}


# --- errors -----------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("status, code, kind", [
    (401, "unauthorized", AuthenticationError),
    (403, "forbidden", PermissionDeniedError),
    (404, "not_found", NotFoundError),
    (402, "quota_exceeded", QuotaExceededError),
    (422, "invalid_input", ValidationError),
    (400, "invalid_input", ValidationError),
    (429, "too_many_runs", RateLimitError),
    (500, "internal", ServerError),
    (503, "data_unavailable", ServerError),
])
def test_each_status_has_its_error(api: FakeAPI, status: int, code: str, kind: type) -> None:
    api.reply(ok(error_json(code, "A sentence."), status=status))
    with pytest.raises(enrichednow.APIError) as caught:
        api.client(max_retries=0).runs.get("run_1")
    error = caught.value
    assert type(error) is kind
    assert (error.status_code, error.code, error.message, error.details) == (status, code, "A sentence.", {})
    assert error.request_id is None and error.body == error_json(code, "A sentence.")
    assert str(error) == f"{status} {code}: A sentence."


def test_403_is_also_an_authentication_error_and_carries_the_reason(api: FakeAPI) -> None:
    api.reply(ok(error_json("forbidden", "Confirm your email address first.", {"reason": "email_not_verified"}), status=403))
    with pytest.raises(AuthenticationError) as caught:
        api.client().scrapers.run("ats.board", {})
    assert caught.value.reason == "email_not_verified"


def test_invalid_input_lists_the_fields(api: FakeAPI) -> None:
    fields = [{"path": "input.board_url", "message": "Field required"}, {"path": "wait", "message": "too big"}]
    api.reply(ok(error_json("invalid_input", "The input is not valid.", {"fields": fields}), status=422))
    with pytest.raises(ValidationError) as caught:
        api.client().scrapers.run("ats.board", {})
    assert caught.value.fields == fields and len(api.requests) == 1


def test_quota_exceeded_says_where_the_account_stands(api: FakeAPI) -> None:
    api.reply(ok(error_json("quota_exceeded", "Used up.", {"used_units": 1000, "allowance_units": 1000}), status=402))
    with pytest.raises(QuotaExceededError) as caught:
        api.client().scrapers.run("ats.board", {})
    assert (caught.value.used_units, caught.value.allowance_units) == (1000, 1000) and len(api.requests) == 1


def test_quota_exceeded_says_what_the_run_needed(api: FakeAPI) -> None:
    details = {"used_units": 998, "allowance_units": 1000, "topup_units": 0, "units_needed": 5}
    api.reply(ok(error_json("quota_exceeded", "Used up.", details), status=402))
    with pytest.raises(QuotaExceededError) as caught:
        api.client().scrapers.run("ats.board", {})
    assert (caught.value.units_needed, caught.value.topup_units) == (5, 0)
    api.answers.clear()
    api.reply(ok(error_json("quota_exceeded", "Used up.", {"used_units": 1}), status=402))
    with pytest.raises(QuotaExceededError) as caught:
        api.client().scrapers.run("ats.board", {})
    assert (caught.value.units_needed, caught.value.topup_units) == (None, None)    # an API from before costs differed


def test_a_run_carries_its_rate(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok", units_per_request=5, units_per_record=None)))
    run = api.client().runs.get("run_1")
    assert (run.units_per_request, run.units_per_record) == (5, None)
    api.answers.clear()
    api.reply(ok(run_json("ok")))
    run = api.client().runs.get("run_1")
    assert (run.units_per_request, run.units_per_record) == (None, None)


def test_a_request_id_is_kept_when_the_api_sends_one(api: FakeAPI) -> None:
    api.reply(ok(error_json("not_found"), status=404, headers={"X-Request-Id": "req_9"}))
    with pytest.raises(NotFoundError) as caught:
        api.client().runs.get("nope")
    assert caught.value.request_id == "req_9" and "req_9" in str(caught.value)


def test_an_error_that_is_not_the_api_s_json_is_still_typed(api: FakeAPI) -> None:
    api.reply(httpx.Response(502, text="<html>Bad Gateway</html>"))
    with pytest.raises(ServerError) as caught:
        api.client(max_retries=0).health()
    assert caught.value.status_code == 502 and caught.value.code is None and "502" in caught.value.message


def test_a_success_that_is_not_json_is_an_api_error(api: FakeAPI) -> None:
    api.reply(httpx.Response(200, text="hello"))
    with pytest.raises(enrichednow.APIError):
        api.client().health()


# --- retries ----------------------------------------------------------------------------------------------------------


def test_a_get_is_retried_on_5xx_with_growing_jittered_pauses(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=500), ok(error_json("data_unavailable"), status=503), ok(run_json()))
    assert api.client().runs.get("run_1").id == "run_1"
    assert len(api.requests) == 3 and len(api.slept) == 2
    assert 0.25 <= api.slept[0] <= 0.5 and 0.5 <= api.slept[1] <= 1.0


def test_retries_stop_at_max_retries(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=500))
    with pytest.raises(ServerError):
        api.client(max_retries=3).runs.get("run_1")
    assert len(api.requests) == 4 and len(api.slept) == 3
    assert api.slept[2] <= 2.0


def test_max_retries_zero_never_retries(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=500))
    with pytest.raises(ServerError):
        api.client(max_retries=0).runs.get("run_1")
    assert len(api.requests) == 1 and api.slept == []


def test_429_honours_retry_after(api: FakeAPI) -> None:
    api.reply(ok(error_json("rate_limited"), status=429, headers={"Retry-After": "7"}), ok(run_json()))
    assert api.client().runs.get("run_1").id == "run_1"
    assert api.slept == [7.0]


def test_a_retry_after_too_long_to_wait_is_raised(api: FakeAPI) -> None:
    api.reply(ok(error_json("rate_limited"), status=429, headers={"Retry-After": "3600"}))
    with pytest.raises(RateLimitError) as caught:
        api.client().runs.get("run_1")
    assert caught.value.retry_after == 3600 and len(api.requests) == 1 and api.slept == []


def test_connection_errors_and_timeouts_are_retried_for_a_get(api: FakeAPI) -> None:
    api.reply(httpx.ConnectError("refused"), httpx.ReadTimeout("slow"), ok(run_json()))
    assert api.client().runs.get("run_1").id == "run_1"
    assert len(api.requests) == 3


def test_connection_errors_are_typed_when_retries_run_out(api: FakeAPI) -> None:
    api.reply(httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError) as caught:
        api.client(max_retries=1).runs.get("run_1")
    assert isinstance(caught.value, APIConnectionError) and isinstance(caught.value.__cause__, httpx.ReadTimeout)
    assert len(api.requests) == 2
    api.answers[:] = [httpx.ConnectError("refused")]
    with pytest.raises(APIConnectionError) as refused:
        api.client(max_retries=0).runs.get("run_1")
    assert not isinstance(refused.value, APITimeoutError)


@pytest.mark.parametrize("failure", [ok(error_json("internal"), status=500), httpx.ReadTimeout("slow"), httpx.ReadError("cut"), httpx.RemoteProtocolError("cut")])
def test_starting_a_run_is_sent_again_with_the_same_idempotency_key(api: FakeAPI, failure: object) -> None:
    api.reply(failure, ok(run_json("queued"), status=202))  # type: ignore[arg-type]
    assert api.client().scrapers.run("ats.board", {"board_url": "x"}).status == "queued"
    keys = [request.headers["Idempotency-Key"] for request in api.requests]
    assert len(keys) == 2 and keys[0] == keys[1] and len(keys[0]) == 36           # one key for the call, a UUID


def test_each_call_has_its_own_key_unless_one_is_given(api: FakeAPI) -> None:
    api.reply(ok(run_json("queued"), status=202), ok(run_json("queued"), status=202), ok(run_json()))
    client = api.client()
    client.scrapers.run("ats.board", {"board_url": "x"})
    client.scrapers.run("ats.board", {"board_url": "x"})
    client.scrape("ats.board", {"board_url": "x"}, idempotency_key="import-acme")
    keys = [request.headers["Idempotency-Key"] for request in api.requests]
    assert keys[0] != keys[1] and keys[2] == "import-acme"


def test_a_key_used_for_another_request_is_a_conflict(api: FakeAPI) -> None:
    api.reply(ok(error_json("idempotency_conflict", "Used.", {"run_id": "run_1"}), status=409))
    with pytest.raises(ConflictError) as caught:
        api.client().scrapers.run("ats.board", {"board_url": "y"}, idempotency_key="import-acme")
    assert caught.value.details == {"run_id": "run_1"} and len(api.requests) == 1


@pytest.mark.parametrize("failure", [ok(error_json("internal"), status=500), httpx.ReadTimeout("slow")])
def test_adding_an_endpoint_is_not_sent_again_when_it_may_have_been_made(api: FakeAPI, failure: object) -> None:
    api.reply(failure)  # type: ignore[arg-type]
    with pytest.raises((ServerError, APIConnectionError)):
        api.client().webhooks.create("https://example.com/hook", events=["run.succeeded"])
    assert len(api.requests) == 1 and api.slept == []


def test_starting_a_run_is_sent_again_when_no_run_can_exist(api: FakeAPI) -> None:
    # The connection was never made, and then a 429 (the docs: "No run was created").
    api.reply(httpx.ConnectError("refused"), ok(error_json("too_many_runs", "Busy.", {"active_runs": 2, "max_concurrent_runs": 2}), status=429),
              ok(run_json("queued"), status=202))
    assert api.client().scrapers.run("ats.board", {"board_url": "x"}).status == "queued"
    assert len(api.requests) == 3


def test_too_many_runs_says_where_the_account_stands(api: FakeAPI) -> None:
    api.reply(ok(error_json("too_many_runs", "Busy.", {"active_runs": 2, "max_concurrent_runs": 2}), status=429))
    with pytest.raises(RateLimitError) as caught:
        api.client(max_retries=0).scrapers.run("ats.board", {"board_url": "x"})
    assert (caught.value.code, caught.value.active_runs, caught.value.max_concurrent_runs, caught.value.retry_after) == ("too_many_runs", 2, 2, None)


def test_cancel_is_retried_like_a_read(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=500), ok(run_json("cancelled")))
    assert api.client().runs.cancel("run_1").status == "cancelled"
    assert len(api.requests) == 2


def test_4xx_is_never_retried(api: FakeAPI) -> None:
    api.reply(ok(error_json("not_found"), status=404))
    with pytest.raises(NotFoundError):
        api.client().runs.get("run_1")
    assert len(api.requests) == 1


def test_the_client_closes_only_what_it_made() -> None:
    mine = httpx.Client()
    with EnrichedNow(KEY, http_client=mine):
        pass
    assert not mine.is_closed
    mine.close()
    with EnrichedNow(KEY) as client:
        own = client._http
    assert own.is_closed
