# Changelog

What changed in each version of the library. Versions before 0.4.0 are in the API's changelog,
<https://docs.enrichednow.com/changelog/>.

## 0.4.0 (not released yet)

Formulas: ready-made workflows that turn a few parameters into a finished list of rows.

- `client.formulas`: `list` (`query` in your own words, best matches first; each formula's `basics`, the questions it
  asks), `get`, `estimate` (free; parameters that cannot run come back `valid=False` with what to
  change) and `run` (`preview`, `unit_cap`, `row_cap`, `wait`, and an `Idempotency-Key` on every start, as on a
  scraper run).
- `client.formula_runs`: `list`, `get`, `wait` (each look held by the API for up to a minute), `rows` across pages
  (`fields`, `min_score`, `view="company"`), `export` and `export_all` as CSV or NDJSON, `cancel`.
- `client.run_formula()`: starts a run, waits for it and returns it with its rows; `download()` writes the whole run
  to a file. `FormulaRunFailedError` when the run fails.
- `client.saved_formulas`: `create` (with a schedule), `list`, `get`, `update` (`None` removes the schedule or the
  monthly cap), `archive`, `duplicate`, `run`, `pause`, `resume`, `reset_seen`, `rows` since a time, `export`,
  `snapshots`, `limits`.
- `client.suppressions` (`list`, `add`, `upload` a CSV file, `delete`), `client.attestations.list()` and
  `client.formula_rows.feedback()`.
- `enrichednow.formula_params`: each formula's parameters as a `TypedDict`.
- New errors: `PlanLimitReachedError` (403), `AttestationRequiredError`, `FormulaUnavailableError`,
  `RequirementMissingError` and `SavedFormulaArchivedError` (409, each a `ConflictError`). `LimitReachedError` also
  names a saved formula's monthly cap (`scope="saved_formula"`, `saved_formula_id`); `ValidationError.min_unit_cap`
  for `unit_cap_too_low`.
