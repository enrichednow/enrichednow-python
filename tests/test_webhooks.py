"""Webhooks: the `webhook_url` of a run, the `webhooks` resource (sync and async), and verifying what arrives."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

import httpx
import pytest

import enrichednow
from conftest import FakeAPI, error_json, ok, run_json
from enrichednow import (
    AsyncEnrichedNow,
    EnrichedNowError,
    NotFoundError,
    ServerError,
    ValidationError,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointWithSecret,
    WebhookEvent,
    WebhookVerificationError,
    parse_webhook,
    verify_webhook,
)

HOOK = "https://example.com/hooks/enrichednow"


def endpoint_json(**over: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "id": "whk_1",
        "url": HOOK,
        "description": "production",
        "events": ["run.succeeded", "run.failed"],
        "enabled": True,
        "disabled_reason": None,
        "disabled_at": None,
        "last_success_at": "2026-11-18T10:00:02Z",
        "last_failure_at": None,
        "created_at": "2026-11-18T09:00:00Z",
    }
    body.update(over)
    return body


def delivery_json(**over: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "id": "whd_1",
        "endpoint_id": "whk_1",
        "run_id": "run_1",
        "event_id": "evt_1",
        "event": "run.succeeded",
        "url": HOOK,
        "status": "failed",
        "attempts": 10,
        "max_attempts": 10,
        "next_attempt_at": None,
        "response_status": 500,
        "error": "http_error",
        "duration_ms": 120,
        "last_attempt_at": "2026-11-18T10:00:02Z",
        "created_at": "2026-11-17T10:00:00Z",
        "finished_at": "2026-11-18T10:00:02Z",
        "resend_of": None,
    }
    body.update(over)
    return body


def no_content() -> httpx.Response:
    return httpx.Response(204)


# --- webhook_url on a run ---------------------------------------------------------------------------------------------


def test_scrapers_run_sends_webhook_url_only_when_given(api: FakeAPI) -> None:
    api.reply(ok(run_json("queued"), status=202))
    client = api.client()
    client.scrapers.run("ats.board", {"board_url": "x"})
    assert api.sent()["json"] == {"input": {"board_url": "x"}}
    client.scrapers.run("ats.board", {"board_url": "x"}, webhook_url=HOOK)
    assert api.sent()["json"] == {"input": {"board_url": "x"}, "webhook_url": HOOK}
    assert api.sent()["params"] == {}


def test_scrape_passes_webhook_url_to_the_run_it_starts(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok")))
    client = api.client()
    client.scrape("ats.board", {"board_url": "x"}, webhook_url=HOOK)
    assert api.sent(0)["json"] == {"input": {"board_url": "x"}, "webhook_url": HOOK}
    client.scrape("ats.board", {"board_url": "x"})
    assert api.sent()["json"] == {"input": {"board_url": "x"}}


def test_webhook_url_must_be_a_string(api: FakeAPI) -> None:
    with pytest.raises(TypeError):
        api.client().scrapers.run("ats.board", {}, webhook_url=5)  # type: ignore[arg-type]
    assert api.requests == []


def test_async_run_and_scrape_send_webhook_url(api: FakeAPI) -> None:
    api.reply(ok(run_json("ok")))

    async def main() -> None:
        async with api.async_client() as client:
            await client.scrapers.run("ats.board", {"board_url": "x"}, webhook_url=HOOK)
            await client.scrape("ats.board", {"board_url": "x"}, webhook_url=HOOK)
            await client.scrape("ats.board", {"board_url": "x"})

    asyncio.run(main())
    assert api.sent(0)["json"] == api.sent(1)["json"] == {"input": {"board_url": "x"}, "webhook_url": HOOK}
    assert api.sent(2)["json"] == {"input": {"board_url": "x"}}


# --- endpoints --------------------------------------------------------------------------------------------------------


def test_webhooks_list(api: FakeAPI) -> None:
    api.reply(ok({"endpoints": [endpoint_json(), endpoint_json(id="whk_2", enabled=False, disabled_reason="deliveries_failed",
                                                               disabled_at="2026-11-18T11:00:00Z", something_new=1)],
                  "run_secret_set": True}))
    listed = api.client().webhooks.list()
    assert api.sent() == {"method": "GET", "path": "/v1/webhooks", "raw_path": "/v1/webhooks", "params": {}, "json": None}
    assert listed.run_secret_set is True and len(listed) == 2
    assert [e.id for e in listed] == [e.id for e in listed.endpoints] == ["whk_1", "whk_2"]
    first, second = listed.endpoints
    assert isinstance(first, WebhookEndpoint) and first.url == HOOK and first.description == "production"
    assert first.events == ["run.succeeded", "run.failed"] and first.enabled is True and first.disabled_reason is None
    assert first.last_success_at == datetime(2026, 11, 18, 10, 0, 2, tzinfo=timezone.utc) and first.last_failure_at is None
    assert first.created_at == datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)
    assert second.enabled is False and second.disabled_reason == "deliveries_failed"
    assert second.disabled_at == datetime(2026, 11, 18, 11, 0, tzinfo=timezone.utc) and second.raw["something_new"] == 1


def test_webhooks_list_of_nothing(api: FakeAPI) -> None:
    api.reply(ok({"endpoints": [], "run_secret_set": False}))
    listed = api.client().webhooks.list()
    assert listed.endpoints == [] and listed.run_secret_set is False and list(listed) == []


def test_webhooks_create_returns_the_secret(api: FakeAPI) -> None:
    api.reply(ok(endpoint_json(secret="whsec_abc"), status=201))
    client = api.client()
    made = client.webhooks.create(HOOK, ["run.succeeded", "run.failed"], description="production")
    sent = api.sent()
    assert (sent["method"], sent["path"]) == ("POST", "/v1/webhooks")
    assert sent["json"] == {"url": HOOK, "events": ["run.succeeded", "run.failed"], "description": "production"}
    assert isinstance(made, WebhookEndpointWithSecret) and isinstance(made, WebhookEndpoint)
    assert made.secret == "whsec_abc" and made.id == "whk_1"
    assert "whsec_abc" not in repr(made)                    # a secret is not printed with the endpoint

    client.webhooks.create(HOOK, ("run.partial",))
    assert api.sent()["json"] == {"url": HOOK, "events": ["run.partial"]}      # no description unless one is given
    client.webhooks.create(HOOK, "run.cancelled")
    assert api.sent()["json"] == {"url": HOOK, "events": ["run.cancelled"]}    # one event name is a list of one


def test_webhooks_create_is_not_sent_twice_after_a_5xx(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=500))
    with pytest.raises(ServerError):
        api.client().webhooks.create(HOOK, ["run.failed"])
    assert len(api.requests) == 1 and api.slept == []       # the endpoint may exist: it is not made a second time


def test_webhooks_create_refused_is_a_validation_error(api: FakeAPI) -> None:
    api.reply(ok(error_json("invalid_input", "The request is not valid.", {"fields": [{"field": "url", "message": "https only"}]}), status=422))
    with pytest.raises(ValidationError) as caught:
        api.client().webhooks.create("http://example.com/hook", ["run.failed"])
    assert caught.value.code == "invalid_input"


def test_webhooks_get_update_delete_and_rotate(api: FakeAPI) -> None:
    api.reply(ok(endpoint_json()), ok(endpoint_json(enabled=False, description="")), no_content(),
              ok(endpoint_json(secret="whsec_new")))
    client = api.client()

    assert client.webhooks.get("whk_1").id == "whk_1"
    assert (api.sent()["method"], api.sent()["path"], api.sent()["json"]) == ("GET", "/v1/webhooks/whk_1", None)

    changed = client.webhooks.update("whk_1", enabled=False, description="")
    assert (api.sent()["method"], api.sent()["path"]) == ("PATCH", "/v1/webhooks/whk_1")
    assert api.sent()["json"] == {"description": "", "enabled": False}        # only what was given, an empty note included
    assert changed.enabled is False and changed.description == ""

    assert client.webhooks.delete("whk_1") is None
    assert (api.sent()["method"], api.sent()["path"], api.sent()["json"]) == ("DELETE", "/v1/webhooks/whk_1", None)

    rotated = client.webhooks.rotate_secret("whk_1")
    assert (api.sent()["method"], api.sent()["path"], api.sent()["json"]) == ("POST", "/v1/webhooks/whk_1/rotate-secret", None)
    assert isinstance(rotated, WebhookEndpointWithSecret) and rotated.secret == "whsec_new"


def test_webhooks_update_sends_every_field_given(api: FakeAPI) -> None:
    api.reply(ok(endpoint_json()))
    client = api.client()
    client.webhooks.update("whk_1", url=HOOK + "/2", events=["run.partial"], description="new", enabled=True)
    assert api.sent()["json"] == {"url": HOOK + "/2", "events": ["run.partial"], "description": "new", "enabled": True}
    with pytest.raises(ValueError):
        client.webhooks.update("whk_1")                     # nothing to change: the API would refuse it
    assert len(api.requests) == 1


def test_webhook_ids_are_one_path_segment(api: FakeAPI) -> None:
    api.reply(ok(endpoint_json()))
    client = api.client()
    client.webhooks.get("../keys?x=1")
    assert api.sent()["raw_path"] == "/v1/webhooks/..%2Fkeys%3Fx%3D1"
    for call in (client.webhooks.get, client.webhooks.delete, client.webhooks.rotate_secret, client.webhooks.deliveries.resend):
        with pytest.raises(ValueError):
            call("")
    assert len(api.requests) == 1


def test_a_missing_endpoint_is_not_found(api: FakeAPI) -> None:
    api.reply(ok(error_json("not_found", "There is no webhook endpoint 'whk_9'."), status=404))
    with pytest.raises(NotFoundError):
        api.client().webhooks.delete("whk_9")


def test_webhooks_create_run_secret(api: FakeAPI) -> None:
    api.reply(ok({"secret": "whsec_run"}))
    made = api.client().webhooks.create_run_secret()
    assert (api.sent()["method"], api.sent()["path"], api.sent()["json"]) == ("POST", "/v1/webhooks/run-secret", None)
    assert made.secret == "whsec_run" and "whsec_run" not in repr(made)


# --- deliveries -------------------------------------------------------------------------------------------------------


def test_deliveries_list_pages(api: FakeAPI) -> None:
    api.reply(ok({"deliveries": [delivery_json(id="whd_3"), delivery_json(id="whd_2", endpoint_id=None)], "next_cursor": "abc"}),
              ok({"deliveries": [delivery_json(id="whd_1", status="pending", next_attempt_at="2026-11-18T10:05:00Z")], "next_cursor": None}))
    page = api.client().webhooks.deliveries.list(endpoint_id="whk_1", run_id="run_1", status="failed", limit=2)
    assert api.sent()["path"] == "/v1/webhooks/deliveries"
    assert api.sent()["params"] == {"endpoint_id": "whk_1", "run_id": "run_1", "status": "failed", "limit": "2"}
    assert [d.id for d in page.items] == ["whd_3", "whd_2"] and page.has_next_page() and page.next_cursor == "abc"
    first = page.items[0]
    assert isinstance(first, WebhookDelivery)
    assert (first.endpoint_id, first.run_id, first.event_id, first.event, first.url) == ("whk_1", "run_1", "evt_1", "run.succeeded", HOOK)
    assert (first.status, first.attempts, first.max_attempts, first.response_status, first.error, first.duration_ms) == (
        "failed", 10, 10, 500, "http_error", 120)
    assert first.next_attempt_at is None and first.resend_of is None
    assert first.last_attempt_at == first.finished_at == datetime(2026, 11, 18, 10, 0, 2, tzinfo=timezone.utc)
    assert first.created_at == datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    assert page.items[1].endpoint_id is None                # a delivery to a run's own webhook_url

    everything = list(page)
    assert [d.id for d in everything] == ["whd_3", "whd_2", "whd_1"]
    assert api.sent()["params"] == {"endpoint_id": "whk_1", "run_id": "run_1", "status": "failed", "limit": "2", "cursor": "abc"}
    assert everything[2].next_attempt_at == datetime(2026, 11, 18, 10, 5, tzinfo=timezone.utc)


def test_deliveries_list_from_a_cursor(api: FakeAPI) -> None:
    api.reply(ok({"deliveries": [], "next_cursor": None}))
    page = api.client().webhooks.deliveries.list(cursor="abc")
    assert api.sent()["params"] == {"cursor": "abc"} and page.items == [] and page.next_page() is None


def test_deliveries_resend(api: FakeAPI) -> None:
    api.reply(ok(delivery_json(id="whd_9", status="pending", attempts=0, resend_of="whd_1"), status=201))
    again = api.client().webhooks.deliveries.resend("whd_1")
    assert (api.sent()["method"], api.sent()["path"], api.sent()["json"]) == ("POST", "/v1/webhooks/deliveries/whd_1/resend", None)
    assert again.id == "whd_9" and again.resend_of == "whd_1" and again.status == "pending"


def test_deliveries_resend_is_not_sent_twice_after_a_5xx(api: FakeAPI) -> None:
    api.reply(ok(error_json("internal"), status=503))
    with pytest.raises(ServerError):
        api.client().webhooks.deliveries.resend("whd_1")
    assert len(api.requests) == 1


# --- async ------------------------------------------------------------------------------------------------------------


def test_async_webhooks(api: FakeAPI) -> None:
    api.reply(ok({"endpoints": [endpoint_json()], "run_secret_set": False}), ok(endpoint_json(secret="whsec_abc"), status=201),
              ok(endpoint_json()), ok(endpoint_json(enabled=False)), no_content(), ok(endpoint_json(secret="whsec_new")),
              ok({"secret": "whsec_run"}), ok(delivery_json(id="whd_9", resend_of="whd_1"), status=201),
              ok({"deliveries": [delivery_json(id="whd_2")], "next_cursor": "abc"}),
              ok({"deliveries": [delivery_json(id="whd_2")], "next_cursor": "abc"}),
              ok({"deliveries": [delivery_json(id="whd_1")], "next_cursor": None}))

    async def scenario(client: AsyncEnrichedNow) -> None:
        listed = await client.webhooks.list()
        assert [e.id for e in listed] == ["whk_1"] and listed.run_secret_set is False
        assert (await client.webhooks.create(HOOK, ["run.failed"], description="x")).secret == "whsec_abc"
        assert (await client.webhooks.get("whk_1")).id == "whk_1"
        assert (await client.webhooks.update("whk_1", enabled=False)).enabled is False
        assert await client.webhooks.delete("whk_1") is None
        assert (await client.webhooks.rotate_secret("whk_1")).secret == "whsec_new"
        assert (await client.webhooks.create_run_secret()).secret == "whsec_run"
        assert (await client.webhooks.deliveries.resend("whd_1")).resend_of == "whd_1"
        page = await client.webhooks.deliveries.list(status="failed")
        assert [d.id for d in page.items] == ["whd_2"] and page.has_next_page()
        assert [d.id async for d in client.webhooks.deliveries.list(status="failed", limit=1)] == ["whd_2", "whd_1"]
        with pytest.raises(ValueError):
            await client.webhooks.update("whk_1")

    async def main() -> None:
        async with api.async_client() as client:
            await scenario(client)

    asyncio.run(main())
    assert [(api.sent(i)["method"], api.sent(i)["path"]) for i in range(11)] == [
        ("GET", "/v1/webhooks"), ("POST", "/v1/webhooks"), ("GET", "/v1/webhooks/whk_1"), ("PATCH", "/v1/webhooks/whk_1"),
        ("DELETE", "/v1/webhooks/whk_1"), ("POST", "/v1/webhooks/whk_1/rotate-secret"), ("POST", "/v1/webhooks/run-secret"),
        ("POST", "/v1/webhooks/deliveries/whd_1/resend"), ("GET", "/v1/webhooks/deliveries"), ("GET", "/v1/webhooks/deliveries"),
        ("GET", "/v1/webhooks/deliveries")]
    assert api.sent(1)["json"] == {"url": HOOK, "events": ["run.failed"], "description": "x"}
    assert api.sent(3)["json"] == {"enabled": False}
    assert api.sent(8)["params"] == {"status": "failed"}
    assert api.sent(10)["params"] == {"status": "failed", "limit": "1", "cursor": "abc"}


def test_the_async_surface_matches_the_sync_one(api: FakeAPI) -> None:
    def names(resource: Any) -> set:  # type: ignore[type-arg]
        return {name for name in dir(resource) if not name.startswith("_")}

    sync, later = api.client(), api.async_client()
    assert names(sync.webhooks) == names(later.webhooks) >= {
        "list", "create", "get", "update", "delete", "rotate_secret", "create_run_secret", "deliveries"}
    assert names(sync.webhooks.deliveries) == names(later.webhooks.deliveries) == {"list", "resend"}


# --- verifying what arrives -------------------------------------------------------------------------------------------

SECRET = "whsec_test_4f1c2d3e"
EVENT = {"id": "evt_1", "type": "run.succeeded", "created_at": "2026-11-18T10:00:02Z", "data": {"run": run_json("ok")}}
BODY = json.dumps(EVENT, separators=(",", ":")).encode("utf-8")


def sign(secret: str, timestamp: Union[int, str], body: bytes) -> str:
    """The signature, made here with nothing of the library's: HMAC-SHA256 of `<timestamp>.<body>`, in hex, after `v1=`."""
    return "v1=" + hmac.new(secret.encode("utf-8"), str(timestamp).encode("ascii") + b"." + body, hashlib.sha256).hexdigest()


def now() -> str:
    return str(int(time.time()))


def test_a_signature_made_independently_verifies() -> None:
    timestamp = now()
    assert verify_webhook(SECRET, timestamp, BODY, sign(SECRET, timestamp, BODY)) is True
    assert enrichednow.verify_webhook is verify_webhook


def test_a_known_signature_verifies() -> None:
    # Worked out once outside Python, so a mistake shared by `sign` and the library would show:
    #   printf '1700000000.{"id":"evt_1"}' | openssl dgst -sha256 -hmac whsec_known
    signature = "v1=68a37d422c7a8b96c533eaf81281025cd110ae84fcf96e4f0307b1bad5f2a1cd"
    assert verify_webhook("whsec_known", "1700000000", b'{"id":"evt_1"}', signature, now=1700000000) is True
    assert verify_webhook("whsec_known", "1700000000", b'{"id":"evt_2"}', signature, now=1700000000) is False


def test_the_body_may_be_text_or_any_bytes() -> None:
    timestamp = now()
    body = '{"note":"café ☕"}'
    signature = sign(SECRET, timestamp, body.encode("utf-8"))
    assert verify_webhook(SECRET, timestamp, body, signature)                           # text is taken as UTF-8
    assert verify_webhook(SECRET, timestamp, body.encode("utf-8"), signature)
    assert verify_webhook(SECRET, timestamp, bytearray(body.encode("utf-8")), signature)
    assert verify_webhook(SECRET, timestamp, memoryview(body.encode("utf-8")), signature)
    assert verify_webhook(SECRET, int(timestamp), body, signature)                      # the timestamp as a number too


def test_a_different_secret_is_refused() -> None:
    timestamp = now()
    assert verify_webhook("whsec_other", timestamp, BODY, sign(SECRET, timestamp, BODY)) is False
    assert verify_webhook("", timestamp, BODY, sign("", timestamp, BODY)) is False      # no secret verifies nothing


def test_a_changed_body_is_refused() -> None:
    timestamp = now()
    signature = sign(SECRET, timestamp, BODY)
    assert verify_webhook(SECRET, timestamp, BODY + b" ", signature) is False
    assert verify_webhook(SECRET, timestamp, BODY.replace(b"run.succeeded", b"run.failed!!!"), signature) is False
    assert verify_webhook(SECRET, timestamp, json.dumps(json.loads(BODY)).encode(), signature) is False     # parsed and written again


def test_a_changed_timestamp_is_refused() -> None:
    timestamp = int(time.time())
    assert verify_webhook(SECRET, str(timestamp + 1), BODY, sign(SECRET, timestamp, BODY)) is False


def test_a_signature_without_the_prefix_is_refused() -> None:
    timestamp = now()
    signature = sign(SECRET, timestamp, BODY)
    assert verify_webhook(SECRET, timestamp, BODY, signature[len("v1="):]) is False
    assert verify_webhook(SECRET, timestamp, BODY, "v2=" + signature[3:]) is False
    assert verify_webhook(SECRET, timestamp, BODY, signature.upper()) is False


@pytest.mark.parametrize("signature", ["", None, "v1=", "v1=zz", "é", b"v1=00", 5])
def test_an_empty_or_malformed_signature_is_refused(signature: Any) -> None:
    assert verify_webhook(SECRET, now(), BODY, signature) is False


@pytest.mark.parametrize("timestamp", ["", "abc", "12.5", "1e9", None, 1.5, True, "0x10", b"1700000000", float("nan")])
def test_a_timestamp_that_is_not_a_whole_number_is_refused(timestamp: Any) -> None:
    assert verify_webhook(SECRET, timestamp, BODY, sign(SECRET, str(timestamp), BODY), now=1700000000) is False


def test_a_timestamp_outside_the_tolerance_is_refused() -> None:
    at = 1_700_000_000
    signature = sign(SECRET, at, BODY)
    assert verify_webhook(SECRET, str(at), BODY, signature, now=at + 300) is True
    assert verify_webhook(SECRET, str(at), BODY, signature, now=at + 301) is False      # older than five minutes
    assert verify_webhook(SECRET, str(at), BODY, signature, now=at - 300) is True
    assert verify_webhook(SECRET, str(at), BODY, signature, now=at - 301) is False      # from too far ahead
    assert verify_webhook(SECRET, str(at), BODY, signature, now=at + 301, tolerance_s=600) is True
    assert verify_webhook(SECRET, str(at), BODY, signature, now=at + 2, tolerance_s=1) is False

    old = int(time.time()) - 301
    assert verify_webhook(SECRET, str(old), BODY, sign(SECRET, old, BODY)) is False     # against the real clock
    assert verify_webhook(SECRET, str(old), BODY, sign(SECRET, old, BODY), tolerance_s=900) is True


def test_verify_matches_what_the_gateway_signs() -> None:
    # gateway/webhook_delivery.py: "v1=" + HMAC-SHA256(secret, f"{timestamp}." + body).hexdigest()
    timestamp = now()
    gateway = "v1=" + hmac.new(SECRET.encode("utf-8"), f"{timestamp}.".encode("ascii") + BODY, hashlib.sha256).hexdigest()
    assert verify_webhook(SECRET, timestamp, BODY, gateway)


def test_parse_webhook_returns_the_event() -> None:
    timestamp = now()
    event = parse_webhook(SECRET, timestamp, BODY, sign(SECRET, timestamp, BODY))
    assert isinstance(event, WebhookEvent)
    assert (event.id, event.type) == ("evt_1", "run.succeeded")
    assert event.created_at == datetime(2026, 11, 18, 10, 0, 2, tzinfo=timezone.utc)
    assert event.run is not None and event.run.id == "run_1" and event.run.succeeded and event.run.record_count == 2
    assert event.raw == EVENT and event.data == {"run": run_json("ok")}
    assert enrichednow.parse_webhook is parse_webhook


def test_a_webhook_events_run_carries_its_rate() -> None:
    body = json.dumps({"id": "evt_2", "type": "run.succeeded", "created_at": "2026-11-18T10:00:02Z",
                       "data": {"run": run_json("ok", units_per_request=None, units_per_record=3)}}).encode()
    timestamp = now()
    event = parse_webhook(SECRET, timestamp, body, sign(SECRET, timestamp, body))
    assert event.run is not None and (event.run.units_per_request, event.run.units_per_record) == (None, 3)


def test_parse_webhook_raises_the_librarys_error_on_a_bad_signature() -> None:
    timestamp = now()
    with pytest.raises(WebhookVerificationError) as caught:
        parse_webhook("whsec_other", timestamp, BODY, sign(SECRET, timestamp, BODY))
    assert isinstance(caught.value, EnrichedNowError)
    assert SECRET not in str(caught.value) and "whsec_other" not in str(caught.value)
    with pytest.raises(WebhookVerificationError):
        parse_webhook(SECRET, str(int(timestamp) - 301), BODY, sign(SECRET, int(timestamp) - 301, BODY))
    with pytest.raises(WebhookVerificationError):
        parse_webhook(SECRET, timestamp, BODY, None)  # type: ignore[arg-type]


@pytest.mark.parametrize("body", [b"not json", b"[1, 2]", b'"text"', b"\xff\xfe"])
def test_parse_webhook_refuses_a_signed_body_that_is_not_an_event(body: bytes) -> None:
    timestamp = now()
    with pytest.raises(WebhookVerificationError):
        parse_webhook(SECRET, timestamp, body, sign(SECRET, timestamp, body))


def test_webhook_events_are_named() -> None:
    assert enrichednow.WEBHOOK_EVENTS == ("run.succeeded", "run.partial", "run.failed", "run.unsupported", "run.cancelled")


def test_parse_webhook_accepts_a_tolerance(monkeypatch: pytest.MonkeyPatch) -> None:
    at: Optional[int] = int(time.time()) - 400
    signature = sign(SECRET, str(at), BODY)
    with pytest.raises(WebhookVerificationError):
        parse_webhook(SECRET, str(at), BODY, signature)
    assert parse_webhook(SECRET, str(at), BODY, signature, tolerance_s=600).id == "evt_1"
