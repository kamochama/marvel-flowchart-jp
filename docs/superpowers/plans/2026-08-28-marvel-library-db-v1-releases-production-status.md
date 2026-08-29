# Marvel Library DB v1 Releases and Production Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-class, source-auditable `releases` and `production_status_assertions` canonical tables, compile them into SQLite, and expose deterministic query views without changing the existing flowchart graph or HTML.

**Architecture:** `data/library/releases.csv` and `data/library/production_status_assertions.csv` become semantic homes for release facts and historical production-status assertions. The first migration imports the current `works.csv` metadata as explicitly labelled `legacy_seed` rows, retaining the existing work columns as a compatibility projection until a later, separately approved cleanup. SQLite receives strict foreign-key and enum checks plus two versioned public views; the current graph derivation continues to use its existing release-sort compatibility fields.

**Tech Stack:** Python 3.13 bundled Codex runtime, `csv`, `sqlite3`, `unittest`, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` (sections 4.1, 4.10, 5, 7, 10 Phase 2, 12, and 13)

## Global Constraints

- `data/library/` remains the human-auditable canonical source of truth; SQLite and files under `data/derived/` are generated products.
- `source_verified` facts require qualifying `primary` or `supporting` evidence and a consistent persistent review history; the initial imported rows remain `legacy_seed` unless explicitly promoted later.
- Preserve existing `work_id`, existing fact IDs, current graph behavior, and current `works.csv` release compatibility columns; do not perform a lossy silent rewrite.
- A release fact describes one territory/kind/date assertion; a production-status assertion describes a status observed at an explicit assertion time. Neither creates a work-to-work edge.
- Do not infer a territory, exact date, production milestone, or historical status date when the source does not establish it. Use `unknown`, `none`, or an empty nullable value and explain the limitation in `notes`.
- Ordinary builds must not mutate canonical CSVs or `data/content_audit/reviews.csv`; generated audit/DB outputs are disposable.
- Use TDD (RED test -> minimal implementation/data change -> GREEN -> full verification) and small auditable commits.
- At the start of execution, fetch/check fresh `origin/main`; create a new forward branch from that production baseline and do not commit directly to `main`.
- Use the bundled PowerShell runtime exactly as documented in `AGENTS.md`:

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

- For bounded independent audits, use a fresh subagent with `model: gpt-5.6-luna`, `reasoning_effort: xhigh`, and `fork_turns: none`; the primary agent independently inspects its diff and reruns verification.
- Do not change `index.html`, remove the old release fields, or begin the HTML DB-export cutover in this plan.

---

### Task 1: Define the canonical release/status contract and audit plumbing

**Files:**
- Create: `data/library/releases.csv`
- Create: `data/library/production_status_assertions.csv`
- Modify: `data/library/schema.json`
- Modify: `scripts/library_v5/audit.py`
- Modify: `scripts/library_v5/content_audit.py`
- Modify: `scripts/library_v5/apply_review_patch.py`
- Test: `tests/library_v5/test_ids_and_schema.py`
- Test: `tests/library_v5/test_audit.py`
- Test: `tests/library_v5/test_content_audit.py`
- Test: `tests/library_v5/test_apply_review_patch.py`

**Interfaces:**
- `releases.csv` header: `release_id,work_id,territory,release_kind,release_date,release_precision,status,certainty,verification_status,notes`.
- `production_status_assertions.csv` header: `production_status_assertion_id,work_id,status,asserted_at,certainty,verification_status,notes`.
- New release-kind vocabulary: `theatrical`, `streaming`, `broadcast`, `festival`, `re_release`, `home_video`, `special`, `series_start`, `imax_series_start`, `undated`, `other`.
- New release-precision vocabulary: `day`, `month`, `year`, `none`.
- New release-status vocabulary: `released`, `announced`, `delayed`, `cancelled`, `unknown`.
- New production-status vocabulary: `announced`, `in_development`, `filming`, `completed`, `delayed`, `cancelled`, `released`, `unknown`.
- Both tables reference `works.work_id`; both primary-key columns participate in evidence/review indexing.

- [ ] **Step 1: Write failing schema and plumbing tests**

  Add tests that assert the two exact headers and table metadata, that both tables are in the source-auditable fact set, that their paths are accepted by the review-patch allowlist, and that a `source_verified` fixture without qualifying evidence produces `source_verified_without_evidence`.

  ```python
  def test_release_and_production_status_tables_are_declared(self):
      schema = json.loads((ROOT / "data/library/schema.json").read_text(encoding="utf-8"))
      self.assertEqual(
          schema["tables"]["releases.csv"]["required_columns"],
          ["release_id", "work_id", "territory", "release_kind", "release_date",
           "release_precision", "status", "certainty", "verification_status", "notes"],
      )
      self.assertEqual(
          schema["tables"]["production_status_assertions.csv"]["required_columns"],
          ["production_status_assertion_id", "work_id", "status", "asserted_at",
           "certainty", "verification_status", "notes"],
      )
      self.assertIn("releases.csv", schema["tables"])
      self.assertIn("production_status_assertions.csv", schema["tables"])

  def test_release_status_facts_are_evidence_indexed(self):
      from scripts.library_v5.audit import check_evidence_coverage

      tables = {
          "releases.csv": [{"release_id": "release-a", "verification_status": "source_verified"}],
          "production_status_assertions.csv": [],
          "evidence.csv": [],
      }
      issues = check_evidence_coverage(tables)
      self.assertEqual(issues[0]["code"], "source_verified_without_evidence")
      self.assertEqual(issues[0]["fact_id"], "release-a")
  ```

- [ ] **Step 2: Run the focused tests and confirm RED**

  Run:

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_ids_and_schema tests.library_v5.test_audit tests.library_v5.test_content_audit tests.library_v5.test_apply_review_patch -v
  ```

  Expected: failure because the new schema tables, fact indexes, and patch paths do not yet exist.

- [ ] **Step 3: Implement the minimum contract**

  Add the exact table metadata and enum arrays to `schema.json`, add the two table names and ID columns to `FACT_ID_COLUMNS` in both audit modules, add explicit `releases.csv` and `production_status_assertions.csv` entries to `ALLOWED_PATHS`, and create header-only canonical CSVs. Keep `schema.json`'s schema version synchronized with the plan's canonical-schema bump to `5.2`.

- [ ] **Step 4: Run the focused tests and confirm GREEN**

  Run the same focused command. Expected: PASS, including the evidence-coverage regression.

- [ ] **Step 5: Commit the contract**

  ```powershell
  git add data/library/schema.json data/library/releases.csv data/library/production_status_assertions.csv scripts/library_v5/audit.py scripts/library_v5/content_audit.py scripts/library_v5/apply_review_patch.py tests/library_v5/test_ids_and_schema.py tests/library_v5/test_audit.py tests/library_v5/test_content_audit.py tests/library_v5/test_apply_review_patch.py
  git commit -m "feat: define release and production status canonical tables"
  ```

### Task 2: Deterministically seed the new canonical tables from existing work metadata

**Files:**
- Create: `scripts/library_v5/migrate_releases_status.py`
- Create: `data/migration/normalized-releases-status/README.md`
- Modify: `data/library/releases.csv`
- Modify: `data/library/production_status_assertions.csv`
- Create: `data/content_audit/applied/2026-08-28-normalized-releases-status-seed.json`
- Test: `tests/library_v5/test_db_v1_releases_status.py`

**Interfaces:**
- The one-shot migration command is:

  ```powershell
  & $MarvelPython -m scripts.library_v5.migrate_releases_status --repo-root . --output-dir data/migration/normalized-releases-status
  ```

- The migration reads `data/library/works.csv` only and writes deterministic candidate CSVs plus a JSON summary under the supplied output directory; it never writes canonical CSVs automatically.
- The migration module exposes `seed_release_rows(work_rows: Sequence[Mapping[str, str]], snapshot_date: str = "2026-08-28") -> tuple[list[dict[str, str]], list[dict[str, str]]]` for fixture tests and `write_seed_outputs(repo_root: Path, output_dir: Path, snapshot_date: str = "2026-08-28") -> dict[str, object]` for the CLI.
- Release IDs are stable and descriptive: `release-{work_id}-primary` for the existing `release_sort_date`/`release_kind` fact and `release-{work_id}-jp` for a non-empty `japan_date` fact. If a source row has no usable date, the primary row still exists with `release_precision=none` and `release_date=`.
- Production-status IDs are `production-status-{work_id}-snapshot-2026-08-28`; `asserted_at=2026-08-28` means “current status snapshot reviewed during this migration”, not an invented historical milestone date.
- Existing `works.status` values map only by explicit text: values beginning with `released` map to `released`; values beginning with `announced` map to `announced`; all other values map to `unknown` and retain the original text in `notes`.
- Existing `works.release_kind` values map mechanically (`home-video` -> `home_video`, `imax-series-start` -> `imax_series_start`, `series-start` -> `series_start`); unknown values map to `other` with the original value in `notes`.
- `release_precision` is copied from the existing precision when it is one of `day`, `month`, or `year`; otherwise it is `none`. Dates are copied only when already parseable as ISO `YYYY-MM-DD`, `YYYY-MM`, or `YYYY`; no guessed day is added.
- Territory is `US` only when the existing release source note explicitly says `U.S.`/`US`, `JP` for the separately recorded Japanese date, and `unknown` otherwise. The migration does not infer a territory from a franchise label.
- All imported rows are `legacy_seed`; the applied record documents that evidence-backed promotion is a later audit batch.

- [ ] **Step 1: Write failing migration/parity tests**

  ```python
  from scripts.library_v5.migrate_releases_status import seed_release_rows

  WORK = {
      "work_id": "work-a", "release_sort_date": "2020-01-01",
      "release_kind": "theatrical", "release_precision": "day",
      "release_source_note": "U.S. theatrical release record.",
      "status": "released", "japan_date": "", "japan_type": "",
  }

  def test_seed_migration_has_one_primary_release_and_status_per_work(self):
      releases, statuses = seed_release_rows([WORK])
      self.assertEqual(len(releases), 1)
      self.assertEqual(len(statuses), 1)
      self.assertEqual(releases[0]["work_id"], statuses[0]["work_id"])
      self.assertEqual(releases[0]["verification_status"], "legacy_seed")

  def test_seed_mapping_does_not_invent_dates_or_territories(self):
      work = {**WORK, "work_id": "work-undated", "release_sort_date": "", "release_kind": "undated", "release_precision": "none", "release_source_note": ""}
      releases, _ = seed_release_rows([work])
      row = releases[0]
      self.assertEqual(row["release_precision"], "none")
      self.assertEqual(row["release_date"], "")
      self.assertEqual(row["territory"], "unknown")

  def test_seed_output_is_byte_deterministic(self):
      first = seed_release_rows([WORK])
      second = seed_release_rows([WORK])
      self.assertEqual(first, second)
  ```

- [ ] **Step 2: Run the focused migration tests and confirm RED**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_db_v1_releases_status -v
  ```

  Expected: failure because the migration module and seed outputs do not yet exist.

- [ ] **Step 3: Implement the one-shot seed generator**

  Use `csv.DictReader`/`csv.DictWriter` with UTF-8 and `lineterminator="\n"`, sort rows by stable ID, preserve the original work row in the migration summary, and fail if any work receives zero primary release rows or more than one primary/status row. Write the migration README with the exact command, mapping rules, row counts, and the explicit `legacy_seed` limitation.

- [ ] **Step 4: Generate candidates, inspect diffs, and install canonical rows**

  Run the command from Step 2, inspect both candidate CSVs and the summary, then copy only the reviewed candidate rows into the two canonical CSVs. Add the applied record with source file hashes, generated row counts, mapping rules, and deferred promotion scope. Do not edit `works.csv` or `reviews.csv` in this task.

- [ ] **Step 5: Run the migration tests and confirm GREEN**

  Re-run the focused migration test module and the strict CSV shape scan. Expected: deterministic output, one primary release and one current status snapshot per work, no fabricated date/territory, and zero malformed rows.

- [ ] **Step 6: Commit the seed batch**

  ```powershell
  git add scripts/library_v5/migrate_releases_status.py data/migration/normalized-releases-status/README.md data/library/releases.csv data/library/production_status_assertions.csv data/content_audit/applied/2026-08-28-normalized-releases-status-seed.json tests/library_v5/test_db_v1_releases_status.py
  git commit -m "feat: seed normalized release and production status facts"
  ```

### Task 3: Compile the new tables with strict SQLite contracts

**Files:**
- Modify: `scripts/library_v5/db_schema.py`
- Modify: `scripts/library_v5/db_compile.py`
- Modify: `scripts/library_v5/db_fingerprint.py`
- Modify: `tests/library_v5/test_db_schema.py`
- Modify: `tests/library_v5/test_db_compile.py`
- Modify: `tests/library_v5/test_db_fingerprint.py`
- Modify: `tests/library_v5/test_phase2_db_compile.py`

**Interfaces:**
- Set `DB_SCHEMA_VERSION = "1.2-normalized-releases-status"`.
- Add `releases` and `production_status_assertions` to `TABLE_SPECS` after `works` and before entity tables so their `work_id` foreign keys are loaded after `works`.
- DDL must enforce non-empty IDs, `works(work_id)` foreign keys, the exact release-kind/status/precision vocabularies, and the shared certainty/verification vocabularies. `release_date` and `asserted_at` remain text values so year/month precision and the migration snapshot can be represented without lossy parsing.
- `canonical_table_names()` and the logical fingerprint must include both tables; the ordinary compiler remains atomic and must still run `PRAGMA foreign_key_check` and `PRAGMA integrity_check`.

- [ ] **Step 1: Add failing schema/compiler tests**

  ```python
  def test_normalized_release_tables_have_fk_and_enum_checks(self):
      connection = sqlite3.connect(":memory:")
      create_schema(connection)
      connection.execute("INSERT INTO works(work_id) VALUES('work-a')")
      with self.assertRaises(sqlite3.IntegrityError):
          connection.execute("INSERT INTO releases(release_id,work_id,territory,release_kind,release_date,release_precision,status,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?)", ("r1", "missing", "unknown", "theatrical", "", "none", "unknown", "unknown", "legacy_seed", ""))
      with self.assertRaises(sqlite3.IntegrityError):
          connection.execute("INSERT INTO releases(release_id,work_id,territory,release_kind,release_date,release_precision,status,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?)", ("r1", "work-a", "unknown", "not-a-kind", "", "none", "unknown", "unknown", "legacy_seed", ""))
  ```

- [ ] **Step 2: Run the focused compiler tests and confirm RED**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_db_schema tests.library_v5.test_db_compile tests.library_v5.test_db_fingerprint tests.library_v5.test_phase2_db_compile -v
  ```

  Expected: failure because the compiler does not know the new tables or schema version.

- [ ] **Step 3: Implement DDL/spec/fingerprint integration**

  Add the constants, table specs, DDL, and schema-version assertions. Keep CSV insertion generic; only extend `_NULLABLE_COLUMNS` if a field is intentionally nullable by the contract. Update fixture headers in `test_db_compile.py` so minimal repositories include empty new tables.

- [ ] **Step 4: Run the focused compiler tests and confirm GREEN**

  Expected: the new tables compile, invalid enum/FK rows fail atomically, fingerprints include both tables, and all existing Phase 2 compiler checks remain green.

- [ ] **Step 5: Commit the compiler contract**

  ```powershell
  git add scripts/library_v5/db_schema.py scripts/library_v5/db_compile.py scripts/library_v5/db_fingerprint.py tests/library_v5/test_db_schema.py tests/library_v5/test_db_compile.py tests/library_v5/test_db_fingerprint.py tests/library_v5/test_phase2_db_compile.py
  git commit -m "feat: compile normalized release status tables"
  ```

### Task 4: Add deterministic public views without changing graph derivation

**Files:**
- Modify: `scripts/library_v5/db_views.py`
- Modify: `tests/library_v5/test_phase2_db_views.py`
- Modify: `tests/library_v5/test_db_export_parity.py`
- Create: `tests/library_v5/test_db_v1_releases_status_views.py`

**Interfaces:**
- Extend `PUBLIC_VIEW_NAMES` with `v_work_releases` and `v_work_production_status`.
- `v_work_releases` exposes `release_id`, `work_id`, work titles, territory, release kind/date/precision/status, certainty, verification status, and notes; exclude rows whose own verification status is `superseded`.
- `v_work_production_status` exposes `production_status_assertion_id`, `work_id`, work titles, status, asserted-at, certainty, verification status, and notes; exclude superseded assertions.
- Both views join only to `works` and must not feed `_v_entity_work_presence`, `_v_entity_work_pairs`, `v_work_connection_reasons`, or any existing edge view.
- Tests select with an explicit `ORDER BY` because SQL view row order is not a contract.
- The view test module defines `_compile_fixture_with_release_status_rows()` by calling the existing `make_minimal_repo()` helper, writing one valid release/status row to the fixture CSVs, and calling `compile_database()`; it returns `open_query_connection(result.db_path)`.

- [ ] **Step 1: Write failing view and non-fan-out tests**

  ```python
  def test_release_and_status_views_are_public_and_do_not_create_work_pairs(self):
      connection = _compile_fixture_with_release_status_rows()
      self.assertIn("v_work_releases", PUBLIC_VIEW_NAMES)
      self.assertIn("v_work_production_status", PUBLIC_VIEW_NAMES)
      self.assertEqual(connection.execute("SELECT count(*) FROM v_work_releases").fetchone()[0], 1)
      self.assertEqual(connection.execute("SELECT count(*) FROM v_work_production_status").fetchone()[0], 1)
      self.assertEqual(connection.execute("SELECT count(*) FROM v_work_connection_reasons").fetchone()[0], 0)
  ```

- [ ] **Step 2: Run the focused view tests and confirm RED**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_db_v1_releases_status_views tests.library_v5.test_phase2_db_views tests.library_v5.test_db_export_parity -v
  ```

- [ ] **Step 3: Implement the two views**

  Drop/recreate the names alongside the existing public views, use explicit column lists, join `works` by `work_id`, and preserve all legacy view SQL unchanged except for the public-name registry.

- [ ] **Step 4: Run the focused view/parity tests and confirm GREEN**

  Confirm that superseded rows are hidden, current rows retain work metadata, and the existing graph/reason export has byte-equivalent output for the canonical fixture.

- [ ] **Step 5: Commit the public query contract**

  ```powershell
  git add scripts/library_v5/db_views.py tests/library_v5/test_phase2_db_views.py tests/library_v5/test_db_export_parity.py tests/library_v5/test_db_v1_releases_status_views.py
  git commit -m "feat: expose normalized release status views"
  ```

### Task 5: Prove audit, build, and backward-compatibility behavior

**Files:**
- Modify: `tests/library_v5/test_db_build_integration.py`
- Modify: `tests/library_v5/test_derive_compat.py`
- Modify: `tests/library_v5/test_content_audit.py`
- Modify: `tests/library_v5/test_audit.py`
- Modify: `tests/library_v5/test_db_fingerprint.py`

**Interfaces:**
- The normal build must count and fingerprint the two new canonical tables, preserve canonical hashes, preserve the legacy release-sort graph, and leave `data/content_audit/reviews.csv` byte-identical.
- The review queue must include legacy-seed rows from the new tables with a deterministic priority/reason, without pretending they are source-verified.
- Existing compatibility invariants remain observations to compare, not fixed row-count targets; no new release/status row may create an edge or alter `prewatch_edges.csv`/`story_paths.csv`.

- [ ] **Step 1: Add failing integration assertions**

  Assert that two builds have equal logical fingerprints, that new table counts are nonzero on the canonical repository, that the protected-input hashes are unchanged, and that graph exports equal a fixture generated before adding the two new views.

- [ ] **Step 2: Run the integration tests and confirm RED**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_db_build_integration tests.library_v5.test_derive_compat tests.library_v5.test_content_audit tests.library_v5.test_audit tests.library_v5.test_db_fingerprint -v
  ```

- [ ] **Step 3: Implement only the required priority/version assertions**

  Update hard-coded schema-version expectations and add explicit queue handling for `releases.csv` and `production_status_assertions.csv`; do not add release/status joins to graph derivation.

- [ ] **Step 4: Run the integration tests and confirm GREEN**

  Run the same command and inspect the generated diff. Expected: audit issues 0, review issues 0, deterministic fingerprints, unchanged graph semantics, and canonical CSV hashes preserved.

- [ ] **Step 5: Commit the compatibility gate**

  ```powershell
  git add tests/library_v5/test_db_build_integration.py tests/library_v5/test_derive_compat.py tests/library_v5/test_content_audit.py tests/library_v5/test_audit.py tests/library_v5/test_db_fingerprint.py scripts/library_v5/audit.py scripts/library_v5/content_audit.py
  git commit -m "test: protect graph compatibility during release normalization"
  ```

### Task 6: Full verification and a separate execution-boundary review

**Files:**
- Create: `docs/superpowers/reviews/2026-08-28-marvel-library-db-v1-releases-production-status-review.md`
- Modify: `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md` (only after the implementation is complete and reviewed)
- Modify: `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md` (only to record the new boundary and exact verification evidence)

**Interfaces:**
- The review document records the branch/base SHAs, table headers, migration counts, explicit `legacy_seed` limitation, tests, build output, audit/review/FK/integrity results, graph compatibility, deferred evidence-promotion work, and whether a PR is ready for user authorization.
- The handoff must distinguish this normalized-release/status subproject from the already completed Events & Multiverse execution plan and from the later HTML DB-export phase.

- [ ] **Step 1: Run the exact full verification commands from the repository root**

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

  Record exit codes and the observed audit issue count, review issue count, SQLite FK/integrity results, table counts, logical fingerprint, and graph compatibility. Remove only the known generated paths after inspection.

- [ ] **Step 2: Run strict CSV shape and diff checks**

  ```powershell
  git diff --check
  ```

  Also run the repository's strict `csv.reader` shape scan across `data/**/*.csv`; expected bad-row count is zero. Inspect every canonical CSV diff, especially commas in `notes`.

- [ ] **Step 3: Write the review and update the handoff/roadmap**

  Include the exact evidence, what was deliberately not promoted, and the next separately approved subproject. Do not claim the HTML DB-export milestone has begun.

- [ ] **Step 4: Commit the review documentation**

  ```powershell
  git add docs/superpowers/reviews/2026-08-28-marvel-library-db-v1-releases-production-status-review.md NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md
  git commit -m "docs: record normalized release status verification"
  ```

- [ ] **Step 5: Push the branch and stop at the PR integration gate**

  Push the new forward branch, open/review the PR against the fresh `main`, and obtain explicit user authorization before merging. Do not merge or publish merely because this plan is GREEN.

## Self-review checklist

- The plan covers canonical schema, deterministic migration, SQLite compilation, public query views, audit/review integration, compatibility, and full verification.
- It intentionally excludes credits, aliases, memberships, possessions, broader multiverse decomposition, and HTML DB-export work; each remains a separate plan boundary.
- No initial row is promoted to `source_verified` without evidence and review history.
- No step changes `index.html` or the existing graph policy.
- Every new table has stable IDs, a `works` foreign key, explicit vocabulary, deterministic ordering, and a review/evidence path.
