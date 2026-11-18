# EnrichedNow Python library

[![CI](https://github.com/enrichednow/enrichednow-python/actions/workflows/ci.yml/badge.svg)](https://github.com/enrichednow/enrichednow-python/actions/workflows/ci.yml)

The official Python library for the [EnrichedNow API](https://docs.enrichednow.com): run scrapers, read their records,
and query the job-postings datasets.

- Sync and async clients with the same surface
- Typed models and typed errors; ships `py.typed`
- Automatic pagination, retries with backoff, and waiting for a run to end
- One runtime dependency: [`httpx`](https://www.python-httpx.org/)
- Python 3.9+

## Install

```bash
pip install enrichednow
```

## Quickstart

Create an API key in the console under **API keys** and put it in the environment:

```bash
export ENRICHEDNOW_API_KEY="en_live_..."
```

```python
from enrichednow import EnrichedNow

client = EnrichedNow()  # reads ENRICHEDNOW_API_KEY

result = client.scrape("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})

print(result.run.status, result.run.record_count)
for record in result.records:
    print(record["title"])
```

`scrape` starts a run, waits for it to end and hands back the run with its records. Records are fetched page by
page as you iterate.

## The client

```python
from enrichednow import EnrichedNow

client = EnrichedNow(
    api_key="en_live_...",                    # default: the ENRICHEDNOW_API_KEY environment variable
    base_url="https://api.enrichednow.com",   # default
    timeout=30.0,                             # seconds for one HTTP request (or an httpx.Timeout)
    max_retries=2,                            # see "Retries"
)
```

Without a key, the constructor raises `MissingAPIKeyError`. Keep the key out of your code.

The client holds a connection pool. Use it as a context manager, or call `client.close()`, when you are done:

```python
with EnrichedNow() as client:
    print(client.health().status)  # "ok"
```

To bring your own `httpx.Client` (custom transport or TLS settings), pass `http_client=...`. The library does not
close a client it did not create.

## Scrapers

```python
for scraper in client.scrapers.list():          # the catalogue
    print(scraper.id, scraper.title, scraper.billing_unit)

scraper = client.scrapers.get("ats.board")      # with JSON Schemas
print(scraper.input_schema)                     # what goes in `input`
print(scraper.record_schema)                    # the shape of one record
```

### Start a run

```python
run = client.scrapers.run("careers.company", {"domain": "acme.com"})
print(run.id, run.status)                       # "queued"
```

`wait` (0 to 60 seconds) asks the API to hold the request open until the run ends or the time is up. Either way
you get the run as it is at that moment, so treat `queued` and `running` as ordinary answers:

```python
run = client.scrapers.run("careers.company", {"domain": "acme.com"}, wait=60)
if run.is_active:
    run = client.runs.wait(run.id)
```

The HTTP timeout of that one request is raised to `wait` + 30 seconds when yours is shorter.

## Runs

```python
run = client.runs.get("run_...")                # the run as it is now
run = client.runs.wait("run_...", timeout=600, poll_interval=2)   # poll until it has ended
run = client.runs.cancel("run_...")             # ask it to stop

for run in client.runs.list(scraper_id="ats.board", status="ok"):
    print(run.id, run.created_at, run.record_count)
```

A `Run` has `id`, `scraper_id`, `scraper_version`, `status`, `reason`, `input`, `record_count`, `units`,
`diagnostics`, `created_at`, `started_at` and `finished_at`, plus a few helpers:

| | |
| --- | --- |
| `run.is_active` | `queued` or `running` |
| `run.is_terminal` | the run has ended, however it ended |
| `run.succeeded` | ended `ok` or `partial` |
| `run.failed` | ended `failed`, `unsupported` or `cancelled` |
| `run.raise_for_status()` | raises `RunFailedError` when `run.failed`; otherwise returns the run |

`runs.wait` returns the run however it ended and raises `WaitTimeoutError` if it is still going after `timeout`
seconds. The run itself carries on; the error has it on `.run`.

Cancelling is cooperative: a run that was already finishing may still complete. Read the status it ended with.

### Records

```python
for record in client.runs.records(run.id):      # every record, page after page
    ...
```

Records are plain dicts in the shape of the scraper's `record_schema`. They are kept for 7 days after the run
ended; after that the list is empty and `page.expired` is `True`.

## The one-liner

```python
result = client.scrape(
    "ats.board",
    {"board_url": "https://boards.greenhouse.io/acme"},
    timeout=600,             # give up waiting after this many seconds (None: wait as long as it takes)
    poll_interval=2,
    raise_on_failure=True,
)
result.run        # the Run, ended
result.records    # iterable of records; `for record in result` works too
```

A run that ends `failed`, `unsupported` or `cancelled` raises `RunFailedError` with `.status`, `.reason` and
`.run`. Pass `raise_on_failure=False` to get the result instead. A run that ends `partial` is returned: it has
records, and `result.run.reason` says why it is not complete.

```python
from enrichednow import RunFailedError

try:
    result = client.scrape("careers.company", {"domain": "acme.com"})
except RunFailedError as error:
    print(error.status, error.reason, error.run.id)
```

## Usage

```python
from datetime import date

usage = client.usage.get()                      # this calendar month (UTC), by day
print(usage.total_units, "of", usage.allowance_units)

usage = client.usage.get(from_=date(2026, 11, 1), to="2026-11-18", group_by="scraper")
for row in usage.rows:
    print(row.key, row.units, row.runs)

client.usage.get(product="data")                # the data allowance and its usage
```

`group_by` is `day`, `scraper` or `product`. The period's first day is `from_` here (`from` in the API, a reserved
word in Python); the same goes for `usage.period.from_`.

## Datasets

The datasets reads live under `client.data`. Each record returned costs one data unit, so stop iterating when you
have what you need.

```python
# Search postings
for posting in client.data.postings.list(title="software engineer", country="DE", status="open", limit=200):
    print(posting.title_clean, posting.company.name, posting.location.city, posting.url)

# One posting, with its description and history
posting = client.data.postings.get("...")
print(posting.description, posting.history.events)

# Companies
for company in client.data.companies.list(q="acme", ats="greenhouse"):
    print(company.domain, company.postings.open)

company = client.data.companies.get("acme.com")
for posting in client.data.companies.postings("acme.com", status="open"):
    ...
```

Posting filters: `company_domain`, `title`, `location`, `country`, `remote`, `employment_type`, `seniority`,
`function`, `status`, `source`, `provenance`, `unmatched`, `posted_from`, `posted_to`, `first_seen_from`,
`first_seen_to`, `last_seen_from`, `last_seen_to`, `sort`. Dates and times can be `date` / `datetime` objects or
ISO 8601 strings; `provenance` can be a string or a list (`["feed", "page"]`).

To follow what is new, ask for what changed since you last asked:

```python
new = client.data.postings.list(first_seen_from=last_checked)
seen = client.data.postings.list(sort="last_seen_at", last_seen_from=last_checked)
```

Two fields are renamed because the models keep the original JSON on `.raw`: the API's `location.raw` and
`salary.raw` are `location.raw_text` and `salary.raw_text`.

## Pagination

Every list returns a page. Iterating it yields its items and then those of every later page, fetching each page
as it is reached:

```python
for run in client.runs.list(limit=100):         # `limit` is the size of a page
    ...

everything = client.runs.records(run_id, limit=1000).to_list()
```

For one page at a time:

```python
page = client.runs.records(run_id, limit=500)
page.items                # this page's records
page.next_cursor          # None on the last page
page.has_next_page()
page = page.next_page()   # None on the last page

for page in client.data.postings.list(status="open").iter_pages():
    save(page.items)
```

To resume later, keep `page.next_cursor` and pass it back as `cursor=` with the same other arguments. A cursor is
an opaque string; pass it back unchanged.

## Errors

Two different things can go wrong, and they are reported differently:

- **The request failed**: the API answered 4xx or 5xx, or did not answer. The library raises.
- **The scrape failed**: the request was fine, and the run ended `failed` or `unsupported`. `runs.get` and
  `runs.wait` return that run; `scrape()` and `run.raise_for_status()` raise `RunFailedError`.

```text
EnrichedNowError
├── MissingAPIKeyError
├── APIConnectionError              the request never got an answer
│   └── APITimeoutError
├── APIError                        the API answered with an error
│   ├── AuthenticationError         401 unauthorized
│   │   └── PermissionDeniedError   403 forbidden
│   ├── NotFoundError               404 not_found
│   ├── RateLimitError              429 too_many_runs, rate_limited
│   ├── ValidationError             422 invalid_input, and any other 4xx
│   │   └── QuotaExceededError      402 quota_exceeded
│   └── ServerError                 5xx internal, data_unavailable
├── RunFailedError                  a run ended failed, unsupported or cancelled
└── WaitTimeoutError                a run did not end within the time given
```

An `APIError` carries what the API said:

```python
import enrichednow

try:
    client.scrapers.run("ats.board", {"board": "acme"})
except enrichednow.QuotaExceededError as error:
    print(error.used_units, error.allowance_units)
except enrichednow.ValidationError as error:
    print(error.status_code)    # 422
    print(error.code)           # "invalid_input"  <- match on this
    print(error.message)        # a sentence for a person
    print(error.fields)         # [{"path": "input.board_url", "message": "Field required"}, ...]
except enrichednow.RateLimitError as error:
    print(error.code)           # "too_many_runs" or "rate_limited"
    print(error.active_runs, error.max_concurrent_runs, error.retry_after)
except enrichednow.APIError as error:
    print(error.status_code, error.code, error.message, error.details, error.request_id)
```

| Attribute | |
| --- | --- |
| `status_code` | The HTTP status. |
| `code` | The API's stable error code. |
| `message` | A sentence for a person. Show it or log it; do not parse it. |
| `details` | Always a dict. `fields` for `invalid_input`; `used_units` and `allowance_units` for `quota_exceeded`; `active_runs` and `max_concurrent_runs` for `too_many_runs`. |
| `reason` | `details["reason"]` when the API gives one, such as `email_not_verified` on a 403. |
| `request_id` | The request id, when the answer has one; otherwise `None`. |
| `body`, `response` | The parsed body and the `httpx.Response`. |

## Retries

A request that fails in a way worth retrying is sent again, up to `max_retries` times (default 2), with
exponential backoff and jitter: about half a second, then a second, then two, up to eight.

| Failure | Retried |
| --- | --- |
| The connection failed or the request timed out | Yes |
| `429` | Yes, after the seconds in `Retry-After` when the answer has it |
| `5xx` | Yes |
| Any other `4xx` | No: the same request would get the same answer |

A `Retry-After` longer than 60 seconds is not waited for: the `RateLimitError` is raised, with the wait on
`.retry_after`.

**Starting a run is the exception.** It is not idempotent: a repeated `POST` starts, and charges for, a second
run. So `scrapers.run()` and `scrape()` send it again only when no run can exist: the connection was never made,
or the answer was `429`. After a timeout or a `5xx` the error is raised instead. Look at `client.runs.list()` before
starting the run again; the first one may well exist.

```python
client = EnrichedNow(max_retries=0)   # never retry
client = EnrichedNow(max_retries=5)
```

## Async

`AsyncEnrichedNow` has the same resources, methods and arguments. Every call is awaited; lists are iterated with
`async for`.

```python
import asyncio
from enrichednow import AsyncEnrichedNow


async def main() -> None:
    async with AsyncEnrichedNow() as client:
        result = await client.scrape("ats.board", {"board_url": "https://boards.greenhouse.io/acme"})
        async for record in result.records:
            print(record["title"])

        run = await client.scrapers.run("careers.company", {"domain": "acme.com"}, wait=60)
        run = await client.runs.wait(run.id)

        async for posting in client.data.postings.list(status="open"):   # every item, page after page
            ...

        page = await client.runs.list(limit=50)                           # or one page
        page = await page.next_page()

        records = await client.runs.records(run.id).to_list()


asyncio.run(main())
```

## Models

Responses are frozen dataclasses with type hints. Timestamps are `datetime` objects (UTC), days are `date`
objects. Every model keeps the JSON it came from on `.raw` (also `.to_dict()`), so a field the API adds later is
there before this library knows its name, and never breaks parsing.

```python
run = client.runs.get("run_...")
run.finished_at                 # datetime
run.diagnostics.facts           # dict
run.raw                         # the JSON object, as returned
```

## Development

```bash
pip install -e ".[dev]"
pytest               # the tests
mypy                 # the strict type check
python -m build      # the wheel and the source distribution, into dist/ (pip install build)
```

The tests run against a mocked transport and make no network calls.

## Licence

MIT. See [LICENSE](LICENSE). To report a security problem, see [SECURITY.md](SECURITY.md).
