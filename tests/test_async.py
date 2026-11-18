"""The async client has the same surface as the sync one; these tests run it with asyncio.run, so no plugin is needed."""
from __future__ import annotations

import asyncio
import inspect
from typing import Any, Awaitable, Callable

import httpx
import pytest

import enrichednow
from conftest import KEY, FakeAPI, error_json, ok, run_json
from enrichednow import AsyncEnrichedNow, EnrichedNow, NotFoundError, RunFailedError, ServerError, WaitTimeoutError


def run(scenario: Callable[[AsyncEnrichedNow], Awaitable[Any]], api: FakeAPI, **options: Any) -> Any:
    async def main() -> Any:
        async with api.async_client(**options) as client:
            return await scenario(client)

    return asyncio.run(main())


def test_headers_and_health(api: FakeAPI) -> None:
    api.reply(ok({"status": "ok"}))
    assert run(lambda c: c.health(), api).status == "ok"
    assert api.last.headers["authorization"] == f"Bearer {KEY}"
    assert api.last.headers["user-agent"] == f"enrichednow-python/{enrichednow.__version__}"


def test_scrapers_and_runs(api: FakeAPI) -> None:
    api.reply(ok({"scrapers": [{"id": "ats.board"}]}), ok({"id": "ats.board", "input_schema": {"type": "object"}}),
              ok(run_json("queued"), status=202), ok(run_json("ok")), ok(run_json("cancelled")),
              ok({"period": {"from": "2026-11-01", "to": "2026-11-18"}, "total_units": 1, "allowance_units": 1000, "rows": []}))

    async def scenario(client: AsyncEnrichedNow) -> None:
        assert [s.id for s in await client.scrapers.list()] == ["ats.board"]
        assert (await client.scrapers.get("ats.board")).input_schema == {"type": "object"}
        assert (await client.scrapers.run("ats.board", {"board_url": "x"}, wait=30)).status == "queued"
        assert (await client.runs.get("run_1")).status == "ok"
        assert (await client.runs.cancel("run_1")).status == "cancelled"
        assert (await client.usage.get(group_by="product")).total_units == 1

    run(scenario, api)
    assert [(api.sent(i)["method"], api.sent(i)["path"]) for i in range(6)] == [
        ("GET", "/v1/scrapers"), ("GET", "/v1/scrapers/ats.board"), ("POST", "/v1/scrapers/ats.board/runs"),
        ("GET", "/v1/runs/run_1"), ("POST", "/v1/runs/run_1/cancel"), ("GET", "/v1/usage")]
    assert api.sent(2)["params"] == {"wait": "30"} and api.sent(2)["json"] == {"input": {"board_url": "x"}}
    assert api.requests[2].extensions["timeout"]["read"] == 60
    assert api.sent(5)["params"] == {"group_by": "product"}


def test_records_async_for_walks_every_page(api: FakeAPI) -> None:
    api.reply(ok({"records": [{"n": 1}, {"n": 2}], "next_cursor": "Mg"}), ok({"records": [{"n": 3}], "next_cursor": None}))

    async def scenario(client: AsyncEnrichedNow) -> Any:
        return [record async for record in client.runs.records("run_1", limit=2)]

    assert run(scenario, api) == [{"n": 1}, {"n": 2}, {"n": 3}]
    assert api.sent(0)["params"] == {"limit": "2"} and api.sent(1)["params"] == {"limit": "2", "cursor": "Mg"}


def test_records_awaited_is_one_page(api: FakeAPI) -> None:
    api.reply(ok({"records": [{"n": 1}], "next_cursor": "MQ"}), ok({"records": [], "next_cursor": None, "expired": True}))

    async def scenario(client: AsyncEnrichedNow) -> None:
        page = await client.runs.records("run_1")
        assert page.items == [{"n": 1}] and page.has_next_page() and len(api.requests) == 1
        following = await page.next_page()
        assert following is not None and following.items == [] and following.expired is True
        assert await following.next_page() is None

    run(scenario, api)


def test_lists_page_and_collect(api: FakeAPI) -> None:
    api.reply(ok({"runs": [run_json(id="run_2")], "next_cursor": "abc"}), ok({"runs": [run_json(id="run_1")], "next_cursor": None}),
              ok({"postings": [{"id": "pst_1"}], "next_cursor": None}), ok({"companies": [{"domain": "acme.com"}], "next_cursor": None}),
              ok({"postings": [{"id": "pst_2"}], "next_cursor": None}), ok({"id": "pst_1", "description": "x"}), ok({"domain": "acme.com"}))

    async def scenario(client: AsyncEnrichedNow) -> None:
        pages = [page async for page in client.runs.list(status="ok", limit=1).iter_pages()]
        assert [[r.id for r in page.items] for page in pages] == [["run_2"], ["run_1"]]
        assert [p.id for p in await client.data.postings.list(remote=True).to_list()] == ["pst_1"]
        assert [c.domain async for c in client.data.companies.list(q="acme")] == ["acme.com"]
        assert [p.id async for p in client.data.companies.postings("acme.com", status="open")] == ["pst_2"]
        assert (await client.data.postings.get("pst_1")).description == "x"
        assert (await client.data.companies.get("acme.com")).domain == "acme.com"

    run(scenario, api)
    assert api.sent(1)["params"] == {"status": "ok", "limit": "1", "cursor": "abc"}
    assert api.sent(2)["params"] == {"remote": "true"}
    assert [api.sent(i)["path"] for i in range(2, 7)] == ["/v1/data/postings", "/v1/data/companies", "/v1/data/companies/acme.com/postings",
                                                         "/v1/data/postings/pst_1", "/v1/data/companies/acme.com"]


def test_wait_polls(api: FakeAPI) -> None:
    api.reply(ok(run_json("running")), ok(run_json("ok")))
    assert run(lambda c: c.runs.wait("run_1", poll_interval=4), api).status == "ok"
    assert api.slept == [4.0]
    api.answers[:] = [ok(run_json("queued"))]
    with pytest.raises(WaitTimeoutError):
        run(lambda c: c.runs.wait("run_1", timeout=0), api)


def test_scrape(api: FakeAPI) -> None:
    api.reply(ok(run_json("running"), status=202), ok(run_json("ok")), ok({"records": [{"n": 1}], "next_cursor": "MQ"}),
              ok({"records": [{"n": 2}], "next_cursor": None}))

    async def scenario(client: AsyncEnrichedNow) -> Any:
        result = await client.scrape("ats.board", {"board_url": "x"})
        assert result.run.status == "ok"
        return [record async for record in result.records]

    assert run(scenario, api) == [{"n": 1}, {"n": 2}]
    assert api.sent(0)["params"] == {"wait": "60"} and api.sent(2)["params"] == {"limit": "1000"}


def test_scrape_raises_for_a_failed_run(api: FakeAPI) -> None:
    api.reply(ok(run_json("unsupported", reason="render_required")))
    with pytest.raises(RunFailedError) as caught:
        run(lambda c: c.scrape("ats.board", {"board_url": "x"}), api)
    assert (caught.value.status, caught.value.reason) == ("unsupported", "render_required")
    assert run(lambda c: c.scrape("ats.board", {"board_url": "x"}, raise_on_failure=False), api).run.status == "unsupported"


def test_errors_and_retries(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=500), httpx.ConnectError("refused"), ok(run_json()))
    assert run(lambda c: c.runs.get("run_1"), api).id == "run_1"
    assert len(api.requests) == 3 and len(api.slept) == 2

    api.answers[:] = [ok(error_json("not_found", "There is no run 'x'."), status=404)]
    with pytest.raises(NotFoundError, match="There is no run"):
        run(lambda c: c.runs.get("x"), api)

    api.requests.clear()
    api.answers[:] = [ok(error_json("internal"), status=500)]
    with pytest.raises(ServerError):
        run(lambda c: c.webhooks.create("https://example.com/hook", events=["run.succeeded"]), api)
    assert len(api.requests) == 1                          # adding an endpoint is not sent again after a 5xx

    api.requests.clear()
    api.answers[:] = [ok(error_json("rate_limited"), status=429, headers={"Retry-After": "2"}), ok(run_json())]
    api.slept.clear()
    run(lambda c: c.runs.get("run_1"), api)
    assert api.slept == [2.0]


def _surface(obj: Any) -> Any:
    return {name for name, value in inspect.getmembers(obj) if not name.startswith("_") and callable(value)}


def test_the_two_clients_have_the_same_surface() -> None:
    sync, async_ = EnrichedNow(KEY), AsyncEnrichedNow(KEY)
    assert _surface(sync) == _surface(async_)
    for name in ("scrapers", "runs", "usage"):
        assert _surface(getattr(sync, name)) == _surface(getattr(async_, name)), name
    for name in ("postings", "companies"):
        sync_resource, async_resource = getattr(sync.data, name), getattr(async_.data, name)
        assert _surface(sync_resource) == _surface(async_resource), name
        for method in _surface(sync_resource):
            assert inspect.signature(getattr(sync_resource, method)).parameters.keys() == inspect.signature(getattr(async_resource, method)).parameters.keys()
    for resource in ("scrapers", "runs", "usage"):
        for method in _surface(getattr(sync, resource)):
            assert (inspect.signature(getattr(getattr(sync, resource), method)).parameters.keys()
                    == inspect.signature(getattr(getattr(async_, resource), method)).parameters.keys()), (resource, method)
