"""Verifying a webhook request. Nothing here needs a client or the network.

    from enrichednow import verify_webhook

    ok = verify_webhook(secret, request.headers["X-Webhook-Timestamp"], raw_body, request.headers["X-Webhook-Signature"])

The signature is `v1=` and the HMAC-SHA256, in hex, of the timestamp, a dot, and the body exactly as it arrived,
under the endpoint's signing secret.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Mapping, Optional, Union

from ._exceptions import WebhookVerificationError
from ._models import WebhookEvent

__all__ = ["verify_webhook", "parse_webhook", "DEFAULT_WEBHOOK_TOLERANCE"]

DEFAULT_WEBHOOK_TOLERANCE = 300
"""Seconds a request's timestamp may be from now."""

Body = Union[bytes, bytearray, memoryview, str]


def _body_bytes(body: Any) -> Optional[bytes]:
    if isinstance(body, str):
        return body.encode("utf-8")
    if isinstance(body, (bytes, bytearray, memoryview)):
        return bytes(body)
    return None


def _timestamp(timestamp: Any) -> Optional[str]:
    """The timestamp as the header carries it, when it is whole seconds in ASCII digits (or an `int`); otherwise `None`."""
    if isinstance(timestamp, int) and not isinstance(timestamp, bool):
        timestamp = str(timestamp)
    if isinstance(timestamp, str) and timestamp.isascii() and timestamp.isdigit() and len(timestamp) <= 20:
        return timestamp
    return None


def verify_webhook(
    secret: str,
    timestamp: Union[str, int],
    body: Body,
    signature: Optional[str],
    *,
    tolerance_s: float = DEFAULT_WEBHOOK_TOLERANCE,
    now: Optional[float] = None,
) -> bool:
    """Whether a webhook request is one this API signed with `secret`, recently.

    `secret` is the endpoint's signing secret (for a run's own `webhook_url`, the account's run secret).
    `timestamp` and `signature` are the `X-Webhook-Timestamp` and `X-Webhook-Signature` headers. `body` is the
    request body as the raw bytes that arrived, before any JSON parsing; a `str` is encoded as UTF-8.

    False when the signature does not match (compared in constant time), when anything is missing or malformed, and
    when the timestamp is more than `tolerance_s` seconds from now (default 300), so a recorded request cannot be
    played back later. `now` is the time to compare with, in seconds since the epoch; default: the clock.

    Never raises for what a request can carry: a request that is not right is `False`.
    """
    sent = _timestamp(timestamp)
    raw = _body_bytes(body)
    if sent is None or raw is None or not isinstance(secret, str) or not secret or not isinstance(signature, str):
        return False
    if not abs((time.time() if now is None else now) - int(sent)) <= tolerance_s:
        return False
    digest = hmac.new(secret.encode("utf-8"), sent.encode("ascii") + b"." + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(("v1=" + digest).encode("ascii"), signature.encode("utf-8"))


def parse_webhook(
    secret: str,
    timestamp: Union[str, int],
    body: Body,
    signature: Optional[str],
    *,
    tolerance_s: float = DEFAULT_WEBHOOK_TOLERANCE,
    now: Optional[float] = None,
) -> WebhookEvent:
    """Verify a webhook request as `verify_webhook` does, and return the event it carries.

    Raises `WebhookVerificationError` when the request does not verify, or when what was signed is not an event:
    answer `400` and do nothing with it.

        event = parse_webhook(secret, headers["X-Webhook-Timestamp"], raw_body, headers["X-Webhook-Signature"])
        if event.type == "run.succeeded":
            for record in client.runs.records(event.run.id): ...
    """
    if not verify_webhook(secret, timestamp, body, signature, tolerance_s=tolerance_s, now=now):
        raise WebhookVerificationError(
            "The webhook request did not verify: the signature does not match this secret, timestamp and body, "
            "or the timestamp is too far from now.")
    try:
        payload = json.loads(_body_bytes(body) or b"")
    except ValueError:                              # not JSON, or not UTF-8
        payload = None
    if not isinstance(payload, Mapping):
        raise WebhookVerificationError("The webhook request verified, but its body is not an event.")
    return WebhookEvent.from_dict(payload)
