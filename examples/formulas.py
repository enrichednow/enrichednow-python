"""Formulas from Python: estimate one, run it, read its rows, download them, and keep it as a saved formula that runs
every weekday and is polled for what is new.

    export ENRICHEDNOW_API_KEY=en_live_...
    python examples/formulas.py
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from enrichednow import AttestationRequiredError, EnrichedNow, PlanLimitReachedError
from enrichednow.formula_params import JobOrderHunterParams


def main() -> None:
    client = EnrichedNow()                               # reads ENRICHEDNOW_API_KEY

    # What a formula takes and returns, and what a run of it would cost: both free.
    formula = client.formulas.get("job-order-hunter")
    print(formula.title, "-", formula.summary)
    params: JobOrderHunterParams = {
        "job_titles": ["Java Developer"],
        "locations": ["London"],
        "posted_within_days": 2,
        "company_size": {"min": 11, "max": 5000},
    }
    answer = client.formulas.estimate("job-order-hunter", params, unit_cap=2000)
    if not answer.valid:
        for problem in answer.errors:
            print(f"{problem.path}: {problem.message}")
        return
    assert answer.estimate is not None
    print(f"about {answer.estimate.expected_units} units, at most {answer.estimate.max_units}")

    # Run it: wait for it to end, then read every row, best first. A preview is at most 10 rows and 50 units.
    try:
        result = client.run_formula("job-order-hunter", params, unit_cap=2000)
    except AttestationRequiredError:
        print("An owner or an admin must first accept this formula's terms, in the console.")
        return
    print(result.run.status, result.run.rows_total, "rows,", result.run.units_spent, "units")
    for row in result:
        print(row.score, row.data["company_name"], row.data["job_title"])

    # One row per company, only some columns, and the whole run as a CSV file.
    for company in result.rows(view="company", fields=["company_name", "job_title", "contact_email"]):
        print(company.data)
    result.download("java-london.csv")

    # Keep it: every weekday at 07:30 London time, mailing a daily digest when there is something new.
    try:
        saved = client.saved_formulas.create(
            "job-order-hunter", params, notify="digest",
            schedule={"cadence": "weekdays", "local_time": "07:30", "timezone": "Europe/London"})
    except PlanLimitReachedError as error:
        print(f"The plan allows {error.allowed} ({error.limit}).")
        return

    # What a daily job reads: the rows its runs delivered since yesterday. A run delivers only rows it never delivered.
    since = datetime.now(timezone.utc) - timedelta(days=1)
    for row in client.saved_formulas.rows(saved.id, since=since):
        print(row.first_seen_at, row.data["company_name"])

    # Never return these again, from any formula: a domain, an address, a company by name, or a CSV file of them.
    client.suppressions.add([("domain", "existing-client.example"), ("email", "someone@example.com")])

    # A row that names the wrong company: from now on this account's runs match it to the right domain.
    first = next(iter(result), None)
    if first is not None:
        client.formula_rows.feedback(first.id, "wrong_company", correct_domain="the-real-company.example")


if __name__ == "__main__":
    main()
