"""A fake API on httpx.MockTransport: tests script the answers and read back what was sent."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Union

import httpx
import pytest

from enrichednow import AsyncEnrichedNow, EnrichedNow

KEY = "en_live_test0000000000000000000000000000"
Answer = Union[httpx.Response, Exception, Callable[[httpx.Request], httpx.Response]]


def run_json(status: str = "ok", **over: Any) -> Dict[str, Any]:
    ended = status not in ("queued", "running")
    body: Dict[str, Any] = {
        "id": "run_1",
        "scraper_id": "ats.board",
        "scraper_version": 3,
        "status": status,
        "reason": None if status in ("ok", "queued", "running") else "fetch_failed",
        "input": {"board_url": "https://boards.greenhouse.io/acme"},
        "record_count": 2 if status in ("ok", "partial") else 0,
        "units": 2 if status in ("ok", "partial") else 0,
        "diagnostics": {"requests": 4, "bytes": 1234, "wall_ms": 900, "facts": {"ats": "greenhouse"}} if ended else None,
        "created_at": "2026-11-18T10:00:00Z",
        "started_at": "2026-11-18T10:00:01.123456789+00:00" if status != "queued" else None,
        "finished_at": "2026-11-18T10:00:02.5Z" if ended else None,
    }
    body.update(over)
    return body


def error_json(code: str, message: str = "No.", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def ok(body: Any, status: int = 200, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
    return httpx.Response(status, json=body, headers=headers)


class FakeAPI:
    """Answers in the order given; the last answer repeats. `requests` is everything that was sent."""

    def __init__(self) -> None:
        self.answers: List[Answer] = []
        self.requests: List[httpx.Request] = []
        self.slept: List[float] = []

    def reply(self, *answers: Answer) -> "FakeAPI":
        self.answers.extend(answers)
        return self

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        assert self.answers, f"no answer scripted for {request.method} {request.url}"
        answer = self.answers[0] if len(self.answers) == 1 else self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        if callable(answer):
            return answer(request)
        return answer

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def sent(self, index: int = -1) -> Dict[str, Any]:
        request = self.requests[index]
        return {
            "method": request.method,
            "path": request.url.path,
            "raw_path": request.url.raw_path.decode().split("?")[0],
            "params": dict(request.url.params),
            "json": json.loads(request.content) if request.content else None,
        }

    def client(self, **options: Any) -> EnrichedNow:
        client = EnrichedNow(options.pop("api_key", KEY), http_client=httpx.Client(transport=httpx.MockTransport(self.handle)), **options)
        client._sleep = self.slept.append
        return client

    def async_client(self, **options: Any) -> AsyncEnrichedNow:
        async def handle(request: httpx.Request) -> httpx.Response:
            return self.handle(request)

        async def sleep(seconds: float) -> None:
            self.slept.append(seconds)

        client = AsyncEnrichedNow(options.pop("api_key", KEY), http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)), **options)
        client._sleep = sleep
        return client


@pytest.fixture
def api() -> FakeAPI:
    return FakeAPI()
