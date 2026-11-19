"""What the API has beyond the first release: record formats, the account's standing on every answer, `unmetered`, a
wait of up to 300 seconds, the filters of the run list, and the files a run produced."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from typing import Any, Dict, List

import httpx
import pytest

from conftest import FakeAPI, error_json, ok, run_json
from enrichednow import QuotaExceededError, RecordsExport, Standing

STANDING = {
    "X-Units-Limit": "1000", "X-Units-Used": "120", "X-Units-Remaining": "880", "X-Units-Topup": "50",
    "X-Units-Reset": "2026-12-01T00:00:00Z", "X-RateLimit-Limit": "2", "X-RateLimit-Remaining": "1",
}


def page(body: bytes, *, cursor: str = "", expired: bool = False, media: str = "text/csv; charset=utf-8") -> httpx.Response:
    headers = {"Content-Type": media}
    if cursor:
        headers["X-Next-Cursor"] = cursor
    if expired:
        headers["X-Records-Expired"] = "true"
    return httpx.Response(200, content=body, headers=headers)


# --- the standing --------------------------------------------------------------------------------------------------------


def test_the_standing_of_the_last_answer_that_carried_it_is_kept(api: FakeAPI) -> None:
    api.reply(ok({"scrapers": []}), ok(run_json("ok"), headers=STANDING))
    client = api.client()
    client.scrapers.list()
    assert client.standing is None                      # the catalogue says nothing of an account
    client.runs.get("run_1")
    standing = client.standing
    assert standing == Standing(units_limit=1000, units_used=120, units_remaining=880, units_topup=50,
                                units_reset=datetime(2026, 12, 1, tzinfo=timezone.utc), runs_limit=2, runs_remaining=1,
                                unmetered=False)
    assert standing.units_available == 930


def test_an_error_carries_the_standing_too(api: FakeAPI) -> None:
    spent = {**STANDING, "X-Units-Used": "1000", "X-Units-Remaining": "0", "X-Units-Topup": "0"}
    api.reply(httpx.Response(402, json=error_json("quota_exceeded"), headers=spent))
    client = api.client()
    with pytest.raises(QuotaExceededError):
        client.scrapers.run("ats.board", {})
    assert client.standing is not None and client.standing.units_available == 0


def test_usage_standing_asks_for_it(api: FakeAPI) -> None:
    unmetered = {**STANDING, "X-Units-Limit": "2147483647", "X-Units-Remaining": "2147483527", "X-Units-Unmetered": "true"}
    api.reply(ok({"runs": [], "next_cursor": None}, headers=unmetered))
    standing = api.client().usage.standing()
    assert api.sent()["path"] == "/v1/runs" and api.sent()["params"] == {"limit": "1"}
    assert standing.unmetered is True and standing.units_limit == 2147483647


def test_usage_says_unmetered(api: FakeAPI) -> None:
    api.reply(ok({"period": {"from": "2026-11-01", "to": "2026-11-19"}, "total_units": 9, "allowance_units": 1000, "unmetered": True, "rows": []}))
    assert api.client().usage.get().unmetered is True


# --- waiting -------------------------------------------------------------------------------------------------------------


def test_a_wait_of_up_to_300_seconds_holds_the_request_that_long(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok")))
    client = api.client(timeout=10)
    client.scrapers.run("ats.board", {}, wait=300)
    assert api.sent()["params"] == {"wait": "300"} and api.last.extensions["timeout"]["read"] == 330
    client.runs.get("run_1", wait=120)
    assert api.sent()["params"] == {"wait": "120"} and api.last.extensions["timeout"]["read"] == 150
    with pytest.raises(ValueError):
        client.scrapers.run("ats.board", {}, wait=301)
    with pytest.raises(ValueError):
        client.runs.get("run_1", wait=-1)


def test_runs_list_takes_every_filter(api: FakeAPI) -> None:
    api.reply(ok({"runs": [run_json("ok")], "next_cursor": None}))
    api.client().runs.list(scraper_id="ats.board", status="ok", api_key_id="key_1",
                           from_=datetime(2026, 11, 1, tzinfo=timezone.utc), to=date(2026, 11, 19), limit=5)
    assert api.sent()["params"] == {"scraper_id": "ats.board", "status": "ok", "api_key_id": "key_1",
                                    "from": "2026-11-01T00:00:00+00:00", "to": "2026-11-19", "limit": "5"}


# --- formats -------------------------------------------------------------------------------------------------------------


def test_export_is_one_page_as_the_api_writes_it(api: FakeAPI) -> None:
    api.reply(page(b"a,b\r\n1,2\r\n", cursor="c2"))
    got = api.client().runs.export("run_1", "csv", limit=1)
    assert api.sent()["params"] == {"format": "csv", "limit": "1"} and api.sent()["path"] == "/v1/runs/run_1/records"
    assert api.last.headers["accept"] == "text/csv"
    assert isinstance(got, RecordsExport) and got.content == b"a,b\r\n1,2\r\n" and got.next_cursor == "c2" and not got.expired
    assert got.text == "a,b\r\n1,2\r\n"
    with pytest.raises(ValueError):
        api.client().runs.export("run_1", "xml")  # type: ignore[arg-type]


def test_export_all_follows_the_cursor_and_writes_the_csv_header_once(api: FakeAPI) -> None:
    api.reply(page(b"a,b\r\n1,2\r\n", cursor="c2"), page(b"a,b\r\n3,4\r\n", cursor="c3"), page(b"a,b\r\n5,6\r\n"))
    chunks = list(api.client().runs.export_all("run_1", "csv"))
    assert b"".join(chunks) == b"a,b\r\n1,2\r\n3,4\r\n5,6\r\n"
    assert [r.url.params.get("cursor") for r in api.requests] == [None, "c2", "c3"]
    assert {r.url.params["limit"] for r in api.requests} == {"1000"}


def test_export_all_ndjson_and_expired(api: FakeAPI) -> None:
    api.reply(page(b'{"a":1}\n', cursor="c2", media="application/x-ndjson"), page(b'{"a":2}\n', media="application/x-ndjson"))
    assert b"".join(api.client().runs.export_all("run_1", "ndjson")) == b'{"a":1}\n{"a":2}\n'
    fresh = FakeAPI().reply(page(b"", expired=True))
    gone = fresh.client().runs.export("run_1", "ndjson")
    assert gone.expired and gone.content == b"" and gone.next_cursor is None


def test_a_file_a_run_produced(api: FakeAPI) -> None:
    api.reply(httpx.Response(200, content=b"\x89PNG", headers={"Content-Type": "image/png"}))
    assert api.client().runs.file("run_1", "screenshot.png") == b"\x89PNG"
    assert api.sent()["path"] == "/v1/runs/run_1/files/screenshot.png"


# --- the async client -----------------------------------------------------------------------------------------------------


def test_the_async_client_has_the_same(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok"), headers=STANDING), page(b"a\r\n1\r\n", cursor="c2"), page(b"a\r\n2\r\n"),
              page(b"a\r\n9\r\n"), ok({"runs": [], "next_cursor": None}, headers=STANDING),
              httpx.Response(200, content=b"img"))

    async def main() -> Dict[str, Any]:
        async with api.async_client() as client:
            await client.runs.get("run_1", wait=200)
            seen = client.standing
            chunks: List[bytes] = [chunk async for chunk in client.runs.export_all("run_1", "csv")]
            one = await client.runs.export("run_1", "csv", cursor="c9")
            return {"seen": seen, "all": b"".join(chunks), "one": one, "standing": await client.usage.standing(),
                    "file": await client.runs.file("run_1", "a.png")}

    got = asyncio.run(main())
    assert got["seen"].units_remaining == 880 and got["all"] == b"a\r\n1\r\n2\r\n" and got["one"].content == b"a\r\n9\r\n"
    assert got["standing"].runs_remaining == 1 and got["file"] == b"img"
