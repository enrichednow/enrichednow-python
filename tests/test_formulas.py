"""Formulas, saved formulas, the suppression list, the terms and row feedback, against answers recorded from the API
(tests/fixtures/formulas): each call sends what the API was sent, and reads what it answered."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import httpx
import pytest

from conftest import FakeAPI, assert_sent, exchange, recorded
from enrichednow import (
    NOT_GIVEN,
    AttestationRequiredError,
    ConflictError,
    FormulaDetails,
    FormulaRunFailedError,
    FormulaUnavailableError,
    LimitReachedError,
    NotFoundError,
    PermissionDeniedError,
    PlanLimitReachedError,
    QuotaExceededError,
    RequirementMissingError,
    RunFailedError,
    SavedFormulaArchivedError,
    ServerError,
    ValidationError,
    WaitTimeoutError,
)
from enrichednow.formula_params import FORMULA_IDS, JobOrderHunterParams

RUN_ID = "frun_000000000000000000000002"
SAVED_ID = "sf_000000000000000000000002"


def params_of(name: str) -> Dict[str, Any]:
    body: Dict[str, Any] = exchange(name)["request"]["body"]
    return dict(body["params"])


PARAMS = params_of("formulas_run")


# --- the catalogue ------------------------------------------------------------------------------------------------------


def test_list_reads_the_catalogue(api: FakeAPI) -> None:
    api.reply(recorded("formulas_list"))
    formulas = api.client().formulas.list()
    assert_sent(api.last, "formulas_list")
    by_id = {f.id: f for f in formulas}
    hunter = by_id["job-order-hunter"]
    assert hunter.status == "beta" and hunter.available is True and hunter.needs_provider is True
    assert hunter.needs_attestation is True and hunter.schedules == ["daily", "weekdays", "weekly"]
    assert hunter.health is not None and hunter.health.status == "ok" and hunter.health.success_rate_7d is None
    assert by_id["data-formula"].available is False
    assert [(b.name, b.required) for b in hunter.basics] == [("job_titles", True), ("locations", True), ("posted_within_days", False)]
    assert hunter.basics[0].type == "list of strings" and hunter.basics[0].help


def test_list_narrows_by_query_and_category(api: FakeAPI) -> None:
    api.reply(recorded("formulas_list_filtered"))
    formulas = api.client().formulas.list(query="hiring", category="recruiting")
    assert_sent(api.last, "formulas_list_filtered")
    assert [f.id for f in formulas] == ["job-order-hunter"]


def test_get_has_the_parameters_columns_and_requirements(api: FakeAPI) -> None:
    api.reply(recorded("formulas_get"))
    detail = api.client().formulas.get("job-order-hunter")
    assert_sent(api.last, "formulas_get")
    assert isinstance(detail, FormulaDetails) and detail.title == "Job Order Hunter"
    assert detail.parameters["required"] == ["job_titles", "locations"]
    assert "company_name" in [c.key for c in detail.columns] and detail.presets and detail.steps
    assert detail.company_view is not None and detail.company_view.key == "company_domain" and "job_title" in detail.company_view.lists
    assert "linkedin.jobs_search" in detail.requirements.scrapers and detail.requirements.capabilities
    assert detail.limits["default_unit_cap"] > 0 and detail.sample_rows and detail.changelog


def test_estimate_sends_only_what_is_given(api: FakeAPI) -> None:
    api.reply(recorded("formulas_estimate"))
    answer = api.client().formulas.estimate("job-order-hunter", PARAMS, unit_cap=2000)
    assert_sent(api.last, "formulas_estimate")
    assert answer.valid is True and answer.estimate is not None
    assert 0 < answer.estimate.min_units <= answer.estimate.expected_units <= answer.estimate.max_units <= 2000
    assert answer.estimate.basis and answer.errors == []


def test_parameters_that_cannot_run_are_an_answer_not_an_error(api: FakeAPI) -> None:
    api.reply(recorded("formulas_estimate_invalid"))
    answer = api.client().formulas.estimate("job-order-hunter", {"locations": ["London"]})
    assert_sent(api.last, "formulas_estimate_invalid")
    assert answer.valid is False and answer.estimate is None
    assert [problem.path for problem in answer.errors] == ["params.job_titles"]


def test_typed_parameters_are_the_formulas_own(api: FakeAPI) -> None:
    typed: JobOrderHunterParams = {"job_titles": ["Java Developer"], "locations": ["London"], "company_size": {"min": 11, "max": 5000}}
    api.reply(recorded("formulas_estimate"))
    api.client().formulas.estimate("job-order-hunter", typed)
    assert json.loads(api.last.content) == {"params": typed}
    assert "job-order-hunter" in FORMULA_IDS


# --- a run --------------------------------------------------------------------------------------------------------------


def test_run_sends_its_parameters_mode_wait_and_an_idempotency_key(api: FakeAPI) -> None:
    api.reply(recorded("formulas_run"))
    run = api.client().formulas.run("job-order-hunter", PARAMS, preview=True, wait=60)
    assert_sent(api.last, "formulas_run")
    assert api.last.extensions["timeout"]["read"] == 90
    assert run.status == "partial" and run.reason == "contacts_not_connected" and run.mode == "preview"
    assert run.succeeded and run.is_terminal and not run.failed
    assert {"code": "source_not_offered", "step": "search_google_jobs", "scraper": "google.jobs"} in run.reasons
    assert run.steps and run.steps[0].id == "search_ats" and sum(step.units for step in run.steps) == run.units_spent
    assert run.estimate is not None and run.rows_total == 4 and run.finished_at is not None


def test_a_queued_run_and_a_key_of_your_own(api: FakeAPI) -> None:
    api.reply(recorded("formulas_run_queued"))
    client = api.client()
    run = client.formulas.run("job-order-hunter", PARAMS, unit_cap=2000, idempotency_key="order-42")
    assert_sent(api.last, "formulas_run_queued")
    assert api.last.headers["idempotency-key"] == "order-42"
    assert run.status == "queued" and run.is_active and run.started_at is None
    assert client.standing is not None and client.standing.units_limit == 1000


def test_a_run_is_retried_with_the_same_key_after_a_server_error(api: FakeAPI) -> None:
    api.reply(httpx.Response(502), recorded("formulas_run_queued"))
    api.client().formulas.run("job-order-hunter", PARAMS)
    first, second = api.requests
    assert first.headers["idempotency-key"] == second.headers["idempotency-key"]


def test_caps_and_wait_are_checked_before_sending(api: FakeAPI) -> None:
    client = api.client()
    with pytest.raises(ValueError):
        client.formulas.run("job-order-hunter", PARAMS, unit_cap=0)
    with pytest.raises(ValueError):
        client.formulas.run("job-order-hunter", PARAMS, wait=301)
    with pytest.raises(TypeError):
        client.formulas.run("job-order-hunter", ["not", "a", "mapping"])  # type: ignore[arg-type]
    assert api.requests == []


def test_get_and_list_runs(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_get_running"), recorded("formula_runs_list"))
    client = api.client()
    run = client.formula_runs.get(RUN_ID)
    assert_sent(api.last, "formula_runs_get_running")
    assert run.status == "running" and run.is_active
    page = client.formula_runs.list(limit=1)
    assert_sent(api.last, "formula_runs_list")
    assert len(page.items) == 1 and page.next_cursor and page.items[0].steps is None


def test_wait_holds_each_look_and_pauses_when_the_api_answers_at_once(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_get_running"), recorded("formula_runs_get"))
    run = api.client().formula_runs.wait(RUN_ID, timeout=120, poll_interval=2)
    assert run.status == "partial"
    assert [dict(r.url.params) for r in api.requests] == [{"wait": "60"}, {"wait": "60"}]
    assert len(api.slept) == 1 and 0 < api.slept[0] <= 2


def test_wait_gives_up_after_its_timeout_and_the_run_carries_on(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_get_running"))
    with pytest.raises(WaitTimeoutError) as caught:
        api.client().formula_runs.wait(RUN_ID, timeout=1, poll_interval=5)
    assert caught.value.run.status == "running" and caught.value.run_id == RUN_ID


def test_cancel_asks_the_run_to_stop(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_cancel"))
    run = api.client().formula_runs.cancel("frun_000000000000000000000001")
    assert_sent(api.last, "formula_runs_cancel")
    assert run.status == "running"


# --- rows -------------------------------------------------------------------------------------------------------------


def test_rows_are_read_across_pages(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_rows"), recorded("formula_runs_rows_page2"))
    rows = api.client().formula_runs.rows(RUN_ID, limit=2).to_list()
    assert_sent(api.requests[0], "formula_runs_rows")
    assert_sent(api.requests[1], "formula_runs_rows_page2")
    assert len(rows) == 4 and rows[0].data["company_name"] == "Corvid" and rows[0].run_id == RUN_ID
    assert rows[0].score is not None and rows[0].evidence["sources"] and rows[0].status == "new" and rows[0].first_seen_at


def test_rows_keep_fields_and_a_least_score(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_rows_fields"))
    rows = list(api.client().formula_runs.rows(RUN_ID, fields=["company_name", "job_title", "contact_email"], min_score=10))
    assert_sent(api.last, "formula_runs_rows_fields")
    assert rows and all(set(row.data) <= {"company_name", "job_title", "contact_email"} for row in rows)


def test_one_row_per_company(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_rows_company"))
    rows = list(api.client().formula_runs.rows(RUN_ID, view="company"))
    assert_sent(api.last, "formula_runs_rows_company")
    corvid = next(row for row in rows if row.data["company_name"] == "Corvid")
    assert isinstance(corvid.data["job_title"], list) and len(corvid.data["job_title"]) == 2
    with pytest.raises(ValueError):
        api.client().formula_runs.rows(RUN_ID, view="people")  # type: ignore[arg-type]


def test_export_a_page_of_csv(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_rows_csv"))
    page = api.client().formula_runs.export(RUN_ID, "csv", limit=2)
    assert_sent(api.last, "formula_runs_rows_csv")
    assert api.last.headers["accept"] == "text/csv"
    assert page.next_cursor == "Mg" and page.text.startswith("company_name,company_domain,")


def test_export_all_writes_one_csv_with_one_header(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_rows_csv"), recorded("formula_runs_rows_csv_page2"))
    text = b"".join(api.client().formula_runs.export_all(RUN_ID, "csv", limit=2)).decode()
    lines = [line for line in text.splitlines() if line]
    assert_sent(api.requests[1], "formula_runs_rows_csv_page2")
    assert lines[0].startswith("company_name,") and sum(line.startswith("company_name,") for line in lines) == 1
    assert len(lines) == 5


def test_export_ndjson(api: FakeAPI) -> None:
    api.reply(recorded("formula_runs_rows_ndjson"))
    page = api.client().formula_runs.export(RUN_ID, "ndjson")
    assert_sent(api.last, "formula_runs_rows_ndjson")
    assert api.last.headers["accept"] == "application/x-ndjson" and page.next_cursor is None
    assert [json.loads(line)["company_name"] for line in page.text.splitlines()][0] == "Corvid"
    with pytest.raises(ValueError):
        api.client().formula_runs.export(RUN_ID, "json")  # type: ignore[arg-type]


def test_row_feedback(api: FakeAPI) -> None:
    api.reply(recorded("formula_rows_feedback"))
    answer = api.client().formula_rows.feedback("frow_000000000000000000000001", "wrong_company",
                                                note="This is the agency, not the employer.", correct_domain="corvid.example")
    assert_sent(api.last, "formula_rows_feedback")
    assert answer.status == "flagged" and answer.correction is not None and answer.correction.domain == "corvid.example"


# --- the helper ---------------------------------------------------------------------------------------------------------


def test_run_formula_waits_for_the_end_and_iterates_every_row(api: FakeAPI) -> None:
    api.reply(recorded("formulas_run_queued"), recorded("formula_runs_get"), recorded("formula_runs_rows"), recorded("formula_runs_rows_page2"))
    result = api.client().run_formula("job-order-hunter", PARAMS)
    assert dict(api.requests[0].url.params) == {"wait": "60"} and api.requests[0].headers["idempotency-key"]
    assert result.run.status == "partial"
    rows = list(result)
    assert len(rows) == 4
    assert dict(api.requests[2].url.params) == {"limit": "1000"}


def test_run_formula_raises_when_the_run_failed(api: FakeAPI) -> None:
    api.reply(recorded("formulas_run", status="failed", reason="source_failed:linkedin.jobs_search"))
    with pytest.raises(FormulaRunFailedError) as caught:
        api.client().run_formula("job-order-hunter", PARAMS)
    assert isinstance(caught.value, RunFailedError) and caught.value.run.formula_id == "job-order-hunter"
    assert "source_failed:linkedin.jobs_search" in str(caught.value)
    result = api.client().run_formula("job-order-hunter", PARAMS, raise_on_failure=False)
    assert result.run.failed


def test_run_formula_downloads_the_whole_run(api: FakeAPI, tmp_path: Path) -> None:
    api.reply(recorded("formulas_run"), recorded("formula_runs_rows_csv"), recorded("formula_runs_rows_csv_page2"))
    result = api.client().run_formula("job-order-hunter", PARAMS, preview=True)
    written = result.download(tmp_path / "rows.csv")
    lines = written.read_text().splitlines()
    assert lines[0].startswith("company_name,") and sum(line.startswith("company_name,") for line in lines) == 1
    assert dict(api.requests[1].url.params) == {"format": "csv", "limit": "1000"}
    with pytest.raises(ValueError):
        result.download(tmp_path / "rows.txt")


# --- saved formulas -------------------------------------------------------------------------------------------------------


def test_save_a_formula_on_a_schedule(api: FakeAPI) -> None:
    api.reply(recorded("saved_create"))
    saved = api.client().saved_formulas.create(
        "job-order-hunter", params_of("saved_create"), schedule={"cadence": "weekdays", "local_time": "07:30", "timezone": "Europe/London"},
        notify="digest")
    assert_sent(api.last, "saved_create")
    assert saved.id == SAVED_ID and saved.name == "Java Developer, London, on weekdays" and saved.name_auto
    assert saved.schedule is not None and saved.schedule.cadence == "weekdays" and saved.schedule.next_fire_at is not None
    assert saved.status == "active" and saved.notify == "digest" and saved.last_run is None and saved.estimate is not None


def test_saving_is_not_sent_again_after_a_server_error(api: FakeAPI) -> None:
    api.reply(httpx.Response(503), recorded("saved_create"))
    with pytest.raises(ServerError):
        api.client().saved_formulas.create("job-order-hunter", PARAMS)
    assert len(api.requests) == 1


def test_list_get_and_limits(api: FakeAPI) -> None:
    api.reply(recorded("saved_list"), recorded("saved_get"), recorded("saved_limits"))
    client = api.client()
    page = client.saved_formulas.list(limit=10)
    assert_sent(api.last, "saved_list")
    assert SAVED_ID in [s.id for s in page.items]
    assert client.saved_formulas.get(SAVED_ID).formula_id == "job-order-hunter"
    assert_sent(api.last, "saved_get")
    limits = client.saved_formulas.limits()
    assert_sent(api.last, "saved_limits")
    assert limits.schedules == 3 and limits.min_interval_minutes == 1440


def test_update_sends_only_what_is_given_and_none_removes(api: FakeAPI) -> None:
    api.reply(recorded("saved_update"))
    client = api.client()
    saved = client.saved_formulas.update(SAVED_ID, name="Java in London, weekdays", monthly_unit_cap=20000)
    assert_sent(api.last, "saved_update")
    assert saved.name == "Java in London, weekdays" and saved.name_auto is False and saved.monthly_unit_cap == 20000
    client.saved_formulas.update(SAVED_ID, schedule=None, monthly_unit_cap=None, name=None)
    assert json.loads(api.last.content) == {"name": None, "monthly_unit_cap": None, "schedule": None}
    client.saved_formulas.update(SAVED_ID, params={"job_titles": ["Kotlin Developer"], "locations": ["Leeds"]}, reset_seen=True)
    assert json.loads(api.last.content) == {"params": {"job_titles": ["Kotlin Developer"], "locations": ["Leeds"]}, "reset_seen": True}
    with pytest.raises(ValueError):
        client.saved_formulas.update(SAVED_ID, name=NOT_GIVEN)


def test_run_a_saved_formula_and_read_what_is_new(api: FakeAPI) -> None:
    api.reply(recorded("saved_run"), recorded("saved_rows"))
    client = api.client()
    run = client.saved_formulas.run(SAVED_ID, wait=60)
    assert_sent(api.requests[0], "saved_run")
    assert run.saved_formula_id == SAVED_ID and run.status == "partial"
    since = datetime(2026, 11, 25, 9, 2, 55, 250000, tzinfo=timezone.utc)
    page = client.saved_formulas.rows(SAVED_ID, since=since, limit=2)
    assert_sent(api.last, "saved_rows")
    assert len(page.items) == 2 and page.next_cursor
    client.saved_formulas.run(SAVED_ID, preview=True, include_seen=True)
    assert json.loads(api.last.content) == {"mode": "preview", "include_seen": True}


def test_saved_rows_as_csv(api: FakeAPI) -> None:
    api.reply(recorded("saved_rows_csv"))
    page = api.client().saved_formulas.export(SAVED_ID, "csv", fields=["company_name", "job_title", "job_url"])
    assert_sent(api.last, "saved_rows_csv")
    assert page.text.splitlines()[0] == "company_name,job_title,job_url"


def test_pause_resume_reset_duplicate_and_archive(api: FakeAPI) -> None:
    api.reply(recorded("saved_pause"), recorded("saved_resume"), recorded("saved_seen_reset"), recorded("saved_duplicate"),
              recorded("saved_archive"))
    client = api.client()
    paused = client.saved_formulas.pause(SAVED_ID)
    assert_sent(api.last, "saved_pause")
    assert paused.status == "paused" and paused.paused_reason == "manual" and paused.schedule is not None
    assert paused.schedule.next_fire_at is None
    assert client.saved_formulas.resume(SAVED_ID).status == "active"
    assert_sent(api.last, "saved_resume")
    reset = client.saved_formulas.reset_seen(SAVED_ID)
    assert_sent(api.last, "saved_seen_reset")
    assert reset.cleared > 0 and reset.saved_formula.id == SAVED_ID
    copy = client.saved_formulas.duplicate(SAVED_ID, name="Java in London (copy)", copy_seen=True)
    assert_sent(api.last, "saved_duplicate")
    assert copy.id != SAVED_ID and copy.schedule is None
    archived = client.saved_formulas.archive(SAVED_ID)
    assert_sent(api.last, "saved_archive")
    assert archived.status == "archived" and archived.archived_at is not None


def test_snapshots_of_a_watch_formula(api: FakeAPI) -> None:
    api.reply(recorded("saved_snapshots"))
    found = api.client().saved_formulas.snapshots("sf_000000000000000000000001", entity_key="https://board.example/1")
    assert_sent(api.last, "saved_snapshots")
    assert [s.fields["job.title"] for s in found] == ["Senior Java Developer", "Java Developer"]


# --- the suppression list, the terms ---------------------------------------------------------------------------------------


def test_suppressions_add_list_and_delete(api: FakeAPI) -> None:
    api.reply(recorded("suppressions_add"), recorded("suppressions_list"), recorded("suppressions_delete"))
    client = api.client()
    added = client.suppressions.add([("domain", "https://www.globex.example/"), {"kind": "email", "value": "Ana@Initech.example"},
                                     ("company_name", "Umbrella, Inc.")])
    assert_sent(api.last, "suppressions_add")
    assert added == 3
    page = client.suppressions.list(limit=2)
    assert_sent(api.last, "suppressions_list")
    assert [s.kind for s in page.items] == ["company_name", "domain"] and page.next_cursor
    client.suppressions.delete("domain", "globex.example")
    assert_sent(api.last, "suppressions_delete")
    with pytest.raises(ValueError):
        client.suppressions.add([])


def test_suppressions_upload_a_csv_file(api: FakeAPI, tmp_path: Path) -> None:
    text = exchange("suppressions_upload")["request"]["text"]
    path = tmp_path / "suppress.csv"
    path.write_text(text)
    api.reply(recorded("suppressions_upload"))
    client = api.client()
    for given in (path, text, text.encode(), path.open("rb")):
        answer = client.suppressions.upload(given)
        assert_sent(api.last, "suppressions_upload")
        assert api.last.headers["content-type"] == "text/csv"
    assert answer.added == 3 and answer.already == 0 and [p.index for p in answer.invalid] == [5]


def test_attestations(api: FakeAPI) -> None:
    api.reply(recorded("attestations_list"))
    [terms] = api.client().attestations.list()
    assert_sent(api.last, "attestations_list")
    assert terms.kind == "personal_data" and terms.accepted is True and terms.accepted_at is not None and terms.text


# --- errors -------------------------------------------------------------------------------------------------------------


def test_attestation_required(api: FakeAPI) -> None:
    api.reply(recorded("error_attestation_required"))
    with pytest.raises(AttestationRequiredError) as caught:
        api.client().formulas.run("job-order-hunter", PARAMS)
    assert isinstance(caught.value, ConflictError) and caught.value.kind == "personal_data" and caught.value.text_version


def test_formula_unavailable_and_not_found(api: FakeAPI) -> None:
    api.reply(recorded("error_formula_unavailable"), recorded("error_formula_not_found"))
    client = api.client()
    with pytest.raises(FormulaUnavailableError) as caught:
        client.formulas.run("retired-formula", {"terms": ["java"]})
    assert caught.value.formula_status == "deprecated"
    with pytest.raises(NotFoundError) as missing:
        client.formulas.get("no-such-formula")
    assert missing.value.code == "formula_not_found"


def test_requirement_missing(api: FakeAPI) -> None:
    api.reply(recorded("error_requirement_missing"))
    with pytest.raises(RequirementMissingError) as caught:
        api.client().formulas.run("data-formula", {"terms": ["java"]})
    assert caught.value.missing == ["product:data"]


def test_unit_cap_too_low(api: FakeAPI) -> None:
    api.reply(recorded("error_unit_cap_too_low"))
    with pytest.raises(ValidationError) as caught:
        api.client().formulas.run("job-order-hunter", PARAMS, unit_cap=1)
    assert caught.value.code == "unit_cap_too_low" and caught.value.min_unit_cap is not None


def test_a_saved_formulas_monthly_cap(api: FakeAPI) -> None:
    api.reply(recorded("error_limit_reached"))
    with pytest.raises(LimitReachedError) as caught:
        api.client().saved_formulas.run("sf_000000000000000000000001")
    error = caught.value
    assert isinstance(error, QuotaExceededError) and error.scope == "saved_formula"
    assert error.saved_formula_id == "sf_000000000000000000000001" and error.limit_units == 3 and error.units_needed


def test_plan_limit_reached(api: FakeAPI) -> None:
    api.reply(recorded("error_plan_limit_reached"))
    with pytest.raises(PlanLimitReachedError) as caught:
        api.client().saved_formulas.create("posting-watch", {"terms": ["java"]},
                                           schedule={"cadence": "hourly", "local_time": "07:30", "timezone": "Europe/London"})
    assert_sent(api.last, "error_plan_limit_reached")
    error = caught.value
    assert isinstance(error, PermissionDeniedError) and error.limit == "min_interval_minutes" and error.allowed == 1440 and error.asked == 60


def test_saved_formula_archived(api: FakeAPI) -> None:
    api.reply(recorded("error_saved_formula_archived"))
    with pytest.raises(SavedFormulaArchivedError):
        api.client().saved_formulas.update(SAVED_ID, notify="none")
    assert_sent(api.last, "error_saved_formula_archived")


def test_an_idempotency_conflict_is_still_a_plain_conflict(api: FakeAPI) -> None:
    api.reply(httpx.Response(409, json={"error": {"code": "idempotency_conflict", "message": "Used.", "details": {"run_id": "frun_1"}}}))
    with pytest.raises(ConflictError) as caught:
        api.client().formulas.run("job-order-hunter", PARAMS)
    assert type(caught.value) is ConflictError
