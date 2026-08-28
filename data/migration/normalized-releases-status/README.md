# Normalized release/status seed migration

This directory contains deterministic candidate outputs for Task 2 of the
Marvel Library DB v1 releases/production-status migration. The migration reads
only `data/library/works.csv`; it does not write or replace canonical tables.

## Command

From the repository root, run:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m scripts.library_v5.migrate_releases_status --repo-root . --output-dir data/migration/normalized-releases-status
```

The command writes the candidate `releases.csv`,
`production_status_assertions.csv`, and `summary.json` files in this directory.
Candidates are reviewed before being copied into `data/library/`.

## Mapping rules

- Every work receives exactly one `release-{work_id}-primary` row and one
  `production-status-{work_id}-snapshot-2026-08-28` current-status row.
- A non-empty `japan_date` receives a separate `release-{work_id}-jp` row with
  territory `JP`. Primary territory is `US` only when
  `release_source_note` explicitly contains `U.S.` or `US`; otherwise it is
  `unknown`. No territory is inferred from a title or franchise label.
- Dates are copied only when already valid ISO `YYYY-MM-DD`, `YYYY-MM`, or
  `YYYY` values. The existing precision is retained only for `day`, `month`,
  or `year` when a usable date exists; otherwise precision is `none`. No day
  is guessed. For example, the current Japanese display strings are retained
  in notes rather than parsed as guessed dates.
- `works.status` values beginning with `released` map to `released`; values
  beginning with `announced` map to `announced`; all other values map to
  `unknown` and retain the original text in notes.
- Existing release kinds remain unchanged when already canonical. The legacy
  values `home-video`, `imax-series-start`, and `series-start` map to
  `home_video`, `imax_series_start`, and `series_start`. Unknown values map to
  `other` and retain the original value in notes.
- Release certainty is normalized from `release_certainty` to the shared
  `confirmed`, `probable`, `uncertain`, or `unknown` vocabulary.
- All generated facts have `verification_status=legacy_seed`. The applied
  record documents that evidence-backed promotion is a later, separate audit
  batch; this migration does not add evidence or reviews.
- `asserted_at=2026-08-28` records the current status snapshot review date. It
  is not an invented historical production milestone.

## Generated row counts

The checked-in candidate snapshot contains 131 work rows, 138 release rows
(131 primary and 7 Japanese-date rows), and 131 production-status assertions.
The exact source and candidate SHA-256 values and the preserved source work
rows are recorded in `summary.json`.

## Scope limitation

This is a deterministic legacy seed, not an evidence-backed content audit.
Canonical rows remain `legacy_seed` until a later review supplies qualifying
evidence and an auditable promotion transition. `works.csv`,
`data/content_audit/reviews.csv`, `index.html`, and graph derivation are outside
this task.
