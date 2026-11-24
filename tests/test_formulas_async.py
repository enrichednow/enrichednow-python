"""The async client's formula calls send and read the same as the sync client's (tests/test_formulas.py)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Coroutine, Dict, TypeVar

import pytest

from conftest import FakeAPI, assert_sent, exchange, recorded
from enrichednow import AttestationRequiredError, FormulaRunFailedError, PlanLimitReachedError, WaitTimeoutError

T = TypeVar("T")
RUN_ID = "frun_000000000000000000000002"
SAVED_ID = "sf_000000000000000000000002"
PARAMS: Dict[str, Any] = dict(exchange("formulas_run")["request"]["body"]["params"])


def run(coroutine: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coroutine)


def test_run_formula_waits_and_iterates_every_row(api: FakeAPI) -> None:
    api.reply(recorded("formulas_run_queued"), recorded("formula_runs_get_running"), recorded("formula_runs_get"),
              recorded("formula_runs_rows"), recorded("formula_runs_rows_page2"))

    async def go() -> int:
        async with api.async_client() as client:
            result = await client.run_formula("job-order-hunter", PARAMS, unit_cap=2000, poll_interval=1)
            assert result.run.status == "partial"
            return len([row async for row in result])

    assert run(go()) == 4
    assert json.loads(api.requests[0].content) == exchange("formulas_run_queued")["request"]["body"]
    assert dict(api.requests[0].url.params) == {"wait": "60"}
    assert api.slept and api.slept[0] <= 1


def test_the_catalogue_and_a_run_with_its_rows_by_company(api: FakeAPI) -> None:
    api.reply(recorded("formulas_list"), recorded("formulas_get"), recorded("formulas_estimate"), recorded("formula_runs_rows_company"))

    async def go() -> None:
        client = api.async_client()
        assert "job-order-hunter" in [f.id for f in await client.formulas.list()]
        assert (await client.formulas.get("job-order-hunter")).company_view is not None
        assert (await client.formulas.estimate("job-order-hunter", PARAMS, unit_cap=2000)).valid
        assert_sent(api.last, "formulas_estimate")
        page = await client.formula_runs.rows(RUN_ID, view="company")
        assert_sent(api.last, "formula_runs_rows_company")
        assert page.items and isinstance(page.items[0].data["job_title"], list)
        await client.close()

    run(go())


def test_export_all_and_download(api: FakeAPI, tmp_path: Path) -> None:
    api.reply(recorded("formulas_run"), recorded("formula_runs_rows_csv"), recorded("formula_runs_rows_csv_page2"))

    async def go() -> Path:
        client = api.async_client()
        result = await client.run_formula("job-order-hunter", PARAMS, preview=True)
        return await result.download(tmp_path / "rows.csv")

    lines = run(go()).read_text().splitlines()
    assert sum(line.startswith("company_name,") for line in lines) == 1 and len([line for line in lines if line]) == 5


def test_saved_formulas_and_their_new_rows(api: FakeAPI) -> None:
    api.reply(recorded("saved_create"), recorded("saved_update"), recorded("saved_run"), recorded("saved_rows"), recorded("saved_pause"),
              recorded("saved_resume"), recorded("saved_archive"))

    async def go() -> None:
        client = api.async_client()
        saved = await client.saved_formulas.create("job-order-hunter", PARAMS, notify="digest",
                                                   schedule={"cadence": "weekdays", "local_time": "07:30", "timezone": "Europe/London"})
        assert saved.schedule is not None
        await client.saved_formulas.update(saved.id, name="Java in London, weekdays", monthly_unit_cap=20000)
        assert_sent(api.last, "saved_update")
        ran = await client.saved_formulas.run(saved.id, wait=60)
        assert ran.saved_formula_id == SAVED_ID
        page = await client.saved_formulas.rows(saved.id, since="2026-11-25T09:02:55.250000+00:00", limit=2)
        assert len(page.items) == 2 and page.next_cursor
        assert (await client.saved_formulas.pause(saved.id)).status == "paused"
        assert (await client.saved_formulas.resume(saved.id)).status == "active"
        assert (await client.saved_formulas.archive(saved.id)).status == "archived"

    run(go())
    assert_sent(api.requests[3], "saved_rows")


def test_suppressions_terms_and_feedback(api: FakeAPI) -> None:
    api.reply(recorded("suppressions_upload"), recorded("attestations_list"), recorded("formula_rows_feedback"))

    async def go() -> None:
        client = api.async_client()
        upload = await client.suppressions.upload(exchange("suppressions_upload")["request"]["text"])
        assert_sent(api.last, "suppressions_upload")
        assert upload.added == 3
        assert (await client.attestations.list())[0].accepted
        feedback = await client.formula_rows.feedback("frow_000000000000000000000001", "wrong_company",
                                                      note="This is the agency, not the employer.", correct_domain="corvid.example")
        assert_sent(api.last, "formula_rows_feedback")
        assert feedback.status == "flagged"

    run(go())


def test_errors_and_waiting(api: FakeAPI) -> None:
    async def go() -> None:
        client = api.async_client()
        api.reply(recorded("error_attestation_required"))
        with pytest.raises(AttestationRequiredError):
            await client.formulas.run("job-order-hunter", PARAMS)
        api.answers.clear()
        api.reply(recorded("error_plan_limit_reached"))
        with pytest.raises(PlanLimitReachedError):
            await client.saved_formulas.create("posting-watch", {"terms": ["java"]}, schedule={"cadence": "hourly", "local_time": "07:30",
                                                                                            "timezone": "Europe/London"})
        api.answers.clear()
        api.reply(recorded("formulas_run", status="cancelled", reason="cancelled"))
        with pytest.raises(FormulaRunFailedError):
            await client.run_formula("job-order-hunter", PARAMS)
        api.answers.clear()
        api.reply(recorded("formula_runs_get_running"))
        with pytest.raises(WaitTimeoutError):
            await client.formula_runs.wait(RUN_ID, timeout=1, poll_interval=5)

    run(go())
    assert json.loads(api.requests[1].content)["schedule"]["cadence"] == "hourly"
