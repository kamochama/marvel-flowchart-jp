# Marvel Library DB v1 Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile the frozen Library v5 canonical text facts into a deterministic SQLite query layer and reproduce the current work-connection graph from versioned SQL views without changing any canonical fact.

**Architecture:** `data/library/*.csv` plus persistent `data/content_audit/reviews.csv` remain Git-auditable source-of-truth inputs. A new compiler creates `data/derived/db/marvel.sqlite`, loads current canonical tables with SQLite constraints, materializes only internal helper data needed for identity resolution, defines versioned public views, fingerprints the logical database, and exports the existing derived work graph from those views. The current Python edge derivation remains temporarily available only as a regression oracle during Phase 1 and is not the production query path after Task 7.

**Tech Stack:** Python 3.12 standard library (`sqlite3`, `csv`, `hashlib`, `json`, `pathlib`, `dataclasses`), SQLite bundled with Python, existing `unittest` test suite, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`

## Global Constraints

- `main` remains unchanged during DB v1 design and implementation until explicit integration approval.
- `data/library/` remains canonical and ordinary build must preserve it byte-for-byte.
- `data/content_audit/reviews.csv` remains persistent human-audit input; ordinary build must not rewrite it.
- SQLite is generated query state, never the authoritative source.
- Use only Python 3.12 standard-library dependencies for DB v1 Phase 1.
- `PRAGMA foreign_keys = ON` is mandatory on every compiler/query connection.
- Existing stable `work_id` and audited fact IDs remain unchanged.
- `verification_status` vocabulary remains exactly `legacy_seed`, `source_verified`, `conflicted`, `superseded`.
- `certainty` vocabulary remains exactly `confirmed`, `probable`, `uncertain`, `unknown` where the existing table uses certainty.
- Same performer identity must never imply same fictional entity identity.
- `identity_of` may collapse aliases; `variant_of` must not collapse identities by default.
- No fixed edge count is a canonical correctness target; Phase 1 parity compares the current branch's semantic graph before and after DB cutover.
- Raw SQLite byte equality is not a reproducibility requirement; logical schema/table/view fingerprints are.
- Phase 1 does not add `events`, `multiverse_transitions`, releases, credits, memberships, aliases, or possessions; those belong to the next plan after DB parity is proven.

---

## File Structure

### New focused modules

- `scripts/library_v5/db_schema.py` — DB schema version, DDL, table-column contracts, FK/CHECK definitions, and versioned public-view registry.
- `scripts/library_v5/db_compile.py` — read frozen canonical CSV/review inputs, create a temporary SQLite database, load rows transactionally, build internal identity helpers, install views, run integrity checks, and atomically publish the DB.
- `scripts/library_v5/db_views.py` — SQL definitions for Phase 1 public views and internal identity-map materialization queries.
- `scripts/library_v5/db_fingerprint.py` — normalized schema/table/view logical hashes and `library_db_manifest.json` writer.
- `scripts/library_v5/db_export.py` — query public DB views and write compatibility `work_pair_reasons.csv` / `work_edges_all.csv` with current deterministic IDs.

### Existing files modified

- `scripts/library_v5/build.py` — invoke DB compiler/fingerprint/export as the production derived-graph path while preserving canonical SHA guard.
- `scripts/library_v5/derive_edges.py` — retain as regression oracle during Phase 1; no production build call after cutover.
- `.github/workflows/library-v5-ci.yml` — add DB fingerprint/parity checks without committing the SQLite binary to `main`.

### New tests

- `tests/library_v5/test_db_schema.py`
- `tests/library_v5/test_db_compile.py`
- `tests/library_v5/test_db_views.py`
- `tests/library_v5/test_db_fingerprint.py`
- `tests/library_v5/test_db_export_parity.py`
- `tests/library_v5/test_db_build_integration.py`

---

### Task 1: Define the Phase 1 SQLite schema contract

**Files:**
- Create: `scripts/library_v5/db_schema.py`
- Test: `tests/library_v5/test_db_schema.py`

**Interfaces:**
- Consumes: current CSV headers from `data/library/*.csv` and `data/content_audit/reviews.csv`.
- Produces: `DB_SCHEMA_VERSION: str`, `TABLE_SPECS: tuple[TableSpec, ...]`, `create_schema(connection: sqlite3.Connection) -> None`, and `canonical_table_names() -> tuple[str, ...]`.

- [ ] **Step 1: Write the failing schema-contract tests**

```python
from scripts.library_v5.db_schema import DB_SCHEMA_VERSION, canonical_table_names, create_schema


def test_phase1_schema_has_current_canonical_tables_and_reviews():
    assert DB_SCHEMA_VERSION == "1.0-phase1"
    assert canonical_table_names() == (
        "works", "entities", "entity_relations", "appearances", "people",
        "portrayals", "continuities", "work_continuities",
        "chronology_assertions", "work_relations", "sources", "evidence",
        "reviews",
    )


def test_schema_enables_foreign_keys_and_enforces_status_enum():
    db = sqlite3.connect(":memory:")
    create_schema(db)
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest_sqlite_integrity_error():
        db.execute(
            "INSERT INTO appearances(appearance_id,work_id,entity_id,appearance_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
            ("a", "missing-work", "missing-entity", "onscreen", "confirmed", "not-a-status", ""),
        )
```

Use `unittest.TestCase.assertRaises(sqlite3.IntegrityError)` rather than pytest helpers in the actual repository test.

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_schema -v
```
Expected: import failure because `scripts.library_v5.db_schema` does not exist.

- [ ] **Step 3: Implement explicit table DDL**

Implement `TableSpec` as a frozen dataclass and create explicit DDL for all Phase 1 tables. Do not infer constraints from CSV at runtime. Representative definitions:

```python
DB_SCHEMA_VERSION = "1.0-phase1"
VERIFICATION_CHECK = "CHECK (verification_status IN ('legacy_seed','source_verified','conflicted','superseded'))"
CERTAINTY_CHECK = "CHECK (certainty IN ('confirmed','probable','uncertain','unknown'))"

DDL = (
    "CREATE TABLE works (work_id TEXT PRIMARY KEY CHECK(length(trim(work_id)) > 0), ...)",
    "CREATE TABLE entities (entity_id TEXT PRIMARY KEY CHECK(length(trim(entity_id)) > 0), ...)",
    "CREATE TABLE appearances (appearance_id TEXT PRIMARY KEY, work_id TEXT NOT NULL REFERENCES works(work_id), entity_id TEXT NOT NULL REFERENCES entities(entity_id), appearance_kind TEXT NOT NULL, certainty TEXT NOT NULL " + CERTAINTY_CHECK + ", verification_status TEXT NOT NULL " + VERIFICATION_CHECK + ", notes TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE portrayals (portrayal_id TEXT PRIMARY KEY, work_id TEXT NOT NULL REFERENCES works(work_id), person_id TEXT NOT NULL REFERENCES people(person_id), entity_id TEXT REFERENCES entities(entity_id), portrayal_kind TEXT NOT NULL, certainty TEXT NOT NULL " + CERTAINTY_CHECK + ", verification_status TEXT NOT NULL " + VERIFICATION_CHECK + ", notes TEXT NOT NULL DEFAULT '')",
)

def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in DDL:
        connection.execute(statement)
```

The implementation must mirror every current CSV column exactly in Phase 1; DB normalization into new tables is explicitly deferred.

- [ ] **Step 4: Run the schema tests and full existing suite**

Run:
```bash
python -m unittest tests.library_v5.test_db_schema -v
python -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
```
Expected: PASS, with no existing test regression.

- [ ] **Step 5: Commit**

```bash
git add scripts/library_v5/db_schema.py tests/library_v5/test_db_schema.py
git commit -m "feat: define Marvel Library DB phase1 schema"
```

---

### Task 2: Compile frozen canonical text into SQLite transactionally

**Files:**
- Create: `scripts/library_v5/db_compile.py`
- Modify: `scripts/library_v5/db_schema.py`
- Test: `tests/library_v5/test_db_compile.py`

**Interfaces:**
- Consumes: `TABLE_SPECS`, canonical CSV paths, `data/content_audit/reviews.csv`.
- Produces: `CompileResult(db_path: Path, table_counts: dict[str, int])`, `compile_database(repo_root: Path, output_path: Path | None = None) -> CompileResult`, `open_query_connection(db_path: Path) -> sqlite3.Connection`.

- [ ] **Step 1: Write failing compiler tests using a minimal temporary repo fixture**

```python
def test_compile_loads_rows_without_mutating_canonical(tmp_path):
    repo = make_minimal_library_fixture(tmp_path)
    before = canonical_hashes(repo)
    result = compile_database(repo)
    after = canonical_hashes(repo)
    self.assertEqual(before, after)
    self.assertTrue(result.db_path.exists())
    self.assertEqual(result.table_counts["works"], 2)


def test_compile_is_atomic_on_fk_failure(tmp_path):
    repo = make_minimal_library_fixture(tmp_path)
    append_bad_appearance(repo, work_id="missing")
    output = repo / "data/derived/db/marvel.sqlite"
    with self.assertRaises(sqlite3.IntegrityError):
        compile_database(repo, output)
    self.assertFalse(output.exists())
```

- [ ] **Step 2: Run targeted tests and verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_compile -v
```
Expected: failure because compiler functions are absent.

- [ ] **Step 3: Implement transactional compiler and atomic publish**

Use a sibling temporary DB, not the final path:

```python
def compile_database(repo_root: Path, output_path: Path | None = None) -> CompileResult:
    repo_root = repo_root.resolve()
    output_path = output_path or repo_root / "data/derived/db/marvel.sqlite"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(".sqlite.tmp")
    temp_path.unlink(missing_ok=True)
    try:
        connection = sqlite3.connect(temp_path)
        create_schema(connection)
        with connection:
            for spec in TABLE_SPECS:
                rows = read_csv_rows(repo_root / spec.source_path)
                insert_rows(connection, spec, rows)
            run_integrity_checks(connection)
        connection.close()
        temp_path.replace(output_path)
    except Exception:
        try:
            connection.close()
        except UnboundLocalError:
            pass
        temp_path.unlink(missing_ok=True)
        raise
    return CompileResult(output_path, table_counts)
```

`run_integrity_checks` must require `PRAGMA foreign_key_check` to return zero rows and `PRAGMA integrity_check` to return exactly `ok`.

- [ ] **Step 4: Run fixture tests, then compile the actual branch data in CI/local checkout**

Run:
```bash
python -m unittest tests.library_v5.test_db_compile -v
python -m scripts.library_v5.db_compile --repo-root .
```
Expected actual-data table counts to equal the source CSV row counts; no canonical file changes.

- [ ] **Step 5: Commit**

```bash
git add scripts/library_v5/db_compile.py scripts/library_v5/db_schema.py tests/library_v5/test_db_compile.py
git commit -m "feat: compile frozen Marvel facts into SQLite"
```

---

### Task 3: Materialize canonical fictional identity resolution inside the DB

**Files:**
- Create: `scripts/library_v5/db_views.py`
- Modify: `scripts/library_v5/db_compile.py`
- Test: `tests/library_v5/test_db_views.py`

**Interfaces:**
- Consumes: `entities`, `entity_relations`, existing `identity_of` semantics.
- Produces: internal table `_entity_identity_map(raw_entity_id TEXT PRIMARY KEY, canonical_entity_id TEXT NOT NULL)` and `install_internal_helpers(connection: sqlite3.Connection) -> None`.

- [ ] **Step 1: Write RED tests for alias collapse, variant non-collapse, and conflicting identities**

```python
def test_identity_of_alias_collapses_but_variant_does_not():
    db = compile_fixture_with_entity_relations(
        identity=("alias-frank", "frank-castle"),
        variant=("strange-838", "strange-616"),
    )
    identity = dict(db.execute("SELECT raw_entity_id, canonical_entity_id FROM _entity_identity_map"))
    self.assertEqual(identity["alias-frank"], "frank-castle")
    self.assertNotEqual(identity.get("strange-838", "strange-838"), "strange-616")


def test_conflicting_identity_targets_abort_compile():
    with self.assertRaisesRegex(ValueError, "conflicting identity_of"):
        compile_fixture_with_conflicting_identity_targets()
```

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_views.MultiverseIdentityHelperTests -v
```
Expected: `_entity_identity_map` does not exist.

- [ ] **Step 3: Implement the helper using the already-tested canonical identity algorithm**

Do not make actor/portrayal identity part of this helper. The compiler may call the existing `_identity_canonical_map(entity_relations)` from `derive_edges.py` during Phase 1 to preserve exact semantics, then insert the result plus identity rows for unmapped appearance entities:

```python
connection.execute("CREATE TABLE _entity_identity_map(raw_entity_id TEXT PRIMARY KEY, canonical_entity_id TEXT NOT NULL REFERENCES entities(entity_id))")
identity_map = _identity_canonical_map(entity_relation_rows)
for entity_id in all_entity_ids:
    connection.execute(
        "INSERT INTO _entity_identity_map VALUES (?, ?)",
        (entity_id, identity_map.get(entity_id, entity_id)),
    )
```

This table is compiled helper state, not canonical data and not a public view.

- [ ] **Step 4: Run identity tests and existing edge-derivation tests**

Run:
```bash
python -m unittest tests.library_v5.test_db_views -v
python -m unittest tests.library_v5.test_entity_identity_resolution tests.library_v5.test_derive_edges -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/library_v5/db_views.py scripts/library_v5/db_compile.py tests/library_v5/test_db_views.py
git commit -m "feat: compile fictional identity resolution into DB"
```

---

### Task 4: Define versioned public SQL views and reproduce work-connection semantics

**Files:**
- Modify: `scripts/library_v5/db_views.py`
- Modify: `scripts/library_v5/db_compile.py`
- Test: `tests/library_v5/test_db_views.py`
- Test: `tests/library_v5/test_db_export_parity.py`

**Interfaces:**
- Consumes: loaded canonical tables and `_entity_identity_map`.
- Produces public views `v_entity_work_history`, `v_continuity_works`, `v_work_connection_reasons`, `v_work_connections_all`, `v_flowchart_nodes`, `v_flowchart_edge_candidates`; `install_public_views(connection) -> None`.

- [ ] **Step 1: Write RED tests for public view contracts**

```python
def test_public_view_contracts_are_present():
    names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='view'")}
    self.assertTrue({
        "v_entity_work_history",
        "v_continuity_works",
        "v_work_connection_reasons",
        "v_work_connections_all",
        "v_flowchart_nodes",
        "v_flowchart_edge_candidates",
    } <= names)


def test_shared_entity_reason_keeps_supporting_fact_metadata():
    row = db.execute("""
        SELECT reason_kind, canonical_entity_id, support_fact_ids,
               appearance_kinds, verification_statuses, certainty_values
        FROM v_work_connection_reasons
        WHERE source_work_id=? AND target_work_id=? AND reason_kind='shared_entity'
    """, ("work-a", "work-b")).fetchone()
    self.assertEqual(row[0], "shared_entity")
    self.assertIn("appearance-work-a-character-x", row[2])
    self.assertIn("source_verified", row[4])


def test_same_actor_different_entities_creates_no_shared_entity_reason():
    count = db.execute("""
        SELECT count(*) FROM v_work_connection_reasons
        WHERE source_work_id='actor-work-a' AND target_work_id='actor-work-b'
          AND reason_kind='shared_entity'
    """).fetchone()[0]
    self.assertEqual(count, 0)
```

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_views -v
```
Expected: missing-view failures.

- [ ] **Step 3: Implement SQL views**

`v_work_connection_reasons` must union two reason classes only in Phase 1:

1. shared canonical entity appearances, excluding `superseded` appearances;
2. explicit non-`superseded` `work_relations`.

Use deterministic `group_concat` through ordered subqueries; never rely on unspecified SQLite row order. Keep a readable `reason_discriminator` rather than reproducing Python hash IDs inside SQL.

Representative structure:

```sql
CREATE VIEW v_work_connection_reasons AS
WITH resolved_appearances AS (
  SELECT a.appearance_id, a.work_id,
         m.canonical_entity_id,
         a.appearance_kind, a.verification_status, a.certainty
  FROM appearances a
  JOIN _entity_identity_map m ON m.raw_entity_id = a.entity_id
  WHERE a.verification_status <> 'superseded'
), shared_pairs AS (
  SELECT a.canonical_entity_id,
         CASE WHEN wa.release_sort_date <= wb.release_sort_date THEN a.work_id ELSE b.work_id END AS source_work_id,
         CASE WHEN wa.release_sort_date <= wb.release_sort_date THEN b.work_id ELSE a.work_id END AS target_work_id
  FROM resolved_appearances a
  JOIN resolved_appearances b
    ON a.canonical_entity_id=b.canonical_entity_id AND a.work_id < b.work_id
  JOIN works wa ON wa.work_id=a.work_id
  JOIN works wb ON wb.work_id=b.work_id
)
SELECT ...
UNION ALL
SELECT ... FROM work_relations WHERE verification_status <> 'superseded';
```

The actual ordering expression must use `(release_sort_date, work_id)` exactly like `_work_sort_key` / `_ordered_pair`, including `9999-99-99` fallback.

`v_work_connections_all` groups by `(source_work_id,target_work_id)` and exposes `reason_count` plus a deterministic ordered reason-key aggregation.

- [ ] **Step 4: Run view tests plus a semantic parity test against the existing Python oracle**

The parity test compares semantic tuples, not raw SQLite binary bytes or SQL-generated reason keys:

```python
old = semantic_reason_tuples(derive_reasons(..., mode="combined_all_pairs"))
new = semantic_reason_tuples_from_db(db)
self.assertEqual(old, new)
```

Run:
```bash
python -m unittest tests.library_v5.test_db_views tests.library_v5.test_db_export_parity -v
```
Expected: exact semantic-set equality on the actual canonical branch data.

- [ ] **Step 5: Commit**

```bash
git add scripts/library_v5/db_views.py scripts/library_v5/db_compile.py tests/library_v5/test_db_views.py tests/library_v5/test_db_export_parity.py
git commit -m "feat: expose versioned Marvel Library SQL views"
```

---

### Task 5: Add logical DB fingerprinting

**Files:**
- Create: `scripts/library_v5/db_fingerprint.py`
- Test: `tests/library_v5/test_db_fingerprint.py`

**Interfaces:**
- Consumes: compiled SQLite DB plus canonical hashes.
- Produces: `logical_fingerprint(connection, canonical_hashes) -> dict[str, object]`, `write_db_manifest(repo_root: Path, db_path: Path) -> Path` writing `data/derived/db/library_db_manifest.json`.

- [ ] **Step 1: Write RED tests proving logical reproducibility and change sensitivity**

```python
def test_two_compiles_have_same_logical_fingerprint(tmp_path):
    db1 = compile_database(repo, tmp_path / "a.sqlite").db_path
    db2 = compile_database(repo, tmp_path / "b.sqlite").db_path
    self.assertEqual(fingerprint(db1), fingerprint(db2))


def test_fact_change_changes_table_and_public_view_hashes(tmp_path):
    before = fingerprint(compile_database(repo).db_path)
    change_fixture_appearance_note(repo)
    after = fingerprint(compile_database(repo).db_path)
    self.assertNotEqual(before["tables"]["appearances"]["content_sha256"], after["tables"]["appearances"]["content_sha256"])
```

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_fingerprint -v
```
Expected: missing fingerprint module.

- [ ] **Step 3: Implement normalized hashing**

Rules:

```python
def hash_query_rows(connection, query: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for row in connection.execute(query):
        payload = json.dumps(list(row), ensure_ascii=False, separators=(",", ":"))
        digest.update(payload.encode("utf-8"))
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()
```

- normalize `sqlite_master.sql` whitespace before hashing schema/view SQL;
- hash each table ordered by its declared primary key;
- hash each public view ordered by its documented stable key columns;
- include SQLite version only under `diagnostics`, not in the equivalence key;
- include canonical input SHA-256 hashes copied from `canonical_hashes(repo_root)`.

- [ ] **Step 4: Run fingerprint tests and two real compiles**

Run:
```bash
python -m unittest tests.library_v5.test_db_fingerprint -v
python -m scripts.library_v5.db_compile --repo-root . --output /tmp/marvel-a.sqlite
python -m scripts.library_v5.db_compile --repo-root . --output /tmp/marvel-b.sqlite
python -m scripts.library_v5.db_fingerprint --repo-root . --db /tmp/marvel-a.sqlite
```
Expected: the two logical fingerprints match.

- [ ] **Step 5: Commit**

```bash
git add scripts/library_v5/db_fingerprint.py tests/library_v5/test_db_fingerprint.py
git commit -m "feat: fingerprint Marvel Library SQLite semantics"
```

---

### Task 6: Export current derived graph from SQLite views

**Files:**
- Create: `scripts/library_v5/db_export.py`
- Test: `tests/library_v5/test_db_export_parity.py`

**Interfaces:**
- Consumes: `v_work_connection_reasons`, `v_work_connections_all`, existing `slug_id()`.
- Produces: `export_work_graph(db_path: Path, derived_dir: Path) -> dict[str, int]`, writing compatibility `work_pair_reasons.csv` and `work_edges_all.csv`.

- [ ] **Step 1: Write RED tests requiring byte-stable compatibility exports**

```python
def test_db_export_matches_current_python_export_on_actual_canonical(tmp_path):
    oracle = tmp_path / "oracle"
    db_out = tmp_path / "db"
    write_python_oracle_edges(REPO_ROOT, oracle)
    db = compile_database(REPO_ROOT, tmp_path / "marvel.sqlite").db_path
    export_work_graph(db, db_out)
    self.assertEqual(read_semantic_csv(oracle / "work_pair_reasons.csv"), read_semantic_csv(db_out / "work_pair_reasons.csv"))
    self.assertEqual((oracle / "work_edges_all.csv").read_bytes(), (db_out / "work_edges_all.csv").read_bytes())
```

For reasons, compare all existing semantic columns and regenerate current `reason_id` with `slug_id()` in the exporter from the SQL view's discriminator; require exact bytes once parity is achieved.

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_export_parity -v
```
Expected: export function absent.

- [ ] **Step 3: Implement exporter that never reads canonical CSV directly**

```python
def export_work_graph(db_path: Path, derived_dir: Path) -> dict[str, int]:
    connection = open_query_connection(db_path)
    reason_rows = [reason_export_row(row) for row in connection.execute(
        "SELECT * FROM v_work_connection_reasons ORDER BY source_work_id,target_work_id,reason_kind,reason_discriminator"
    )]
    edge_rows = collapse_exported_reasons(reason_rows)
    write_csv(derived_dir / "work_pair_reasons.csv", reason_rows, REASON_FIELDS)
    write_csv(derived_dir / "work_edges_all.csv", edge_rows, EDGE_FIELDS)
    return {"work_pair_reasons": len(reason_rows), "work_edges_all": len(edge_rows)}
```

`db_export.py` may use generic CSV writing and `slug_id`, but it must not import/read `data/library/*.csv` or call `derive_reasons`.

- [ ] **Step 4: Run parity twice and verify deterministic bytes**

Run:
```bash
python -m unittest tests.library_v5.test_db_export_parity -v
```
Expected: DB export matches the current branch graph semantics; repeated DB export bytes are identical.

- [ ] **Step 5: Commit**

```bash
git add scripts/library_v5/db_export.py tests/library_v5/test_db_export_parity.py
git commit -m "feat: export work graph from Marvel SQLite views"
```

---

### Task 7: Cut ordinary build over to the DB query path with oracle regression protection

**Files:**
- Modify: `scripts/library_v5/build.py`
- Modify: `.github/workflows/library-v5-ci.yml`
- Test: `tests/library_v5/test_db_build_integration.py`
- Modify: `tests/library_v5/test_canonical_freeze.py`

**Interfaces:**
- Consumes: `compile_database`, `write_db_manifest`, `export_work_graph`.
- Produces: ordinary build result containing `database` and DB-derived `derived_edges`; generated `data/derived/db/marvel.sqlite` and `library_db_manifest.json`; current compatibility files remain available.

- [ ] **Step 1: Write RED build-boundary tests**

```python
def test_ordinary_build_uses_db_export_not_python_edge_writer():
    with mock.patch("scripts.library_v5.build.write_derived_edges", side_effect=AssertionError("legacy writer called")):
        result = build(FIXTURE_REPO)
    self.assertTrue(result["audit_ok"])
    self.assertTrue((FIXTURE_REPO / "data/derived/db/marvel.sqlite").exists())


def test_ordinary_build_preserves_canonical_and_is_repeatable():
    before = canonical_hashes(FIXTURE_REPO)
    first = build(FIXTURE_REPO)
    first_manifest = load_db_manifest(FIXTURE_REPO)
    second = build(FIXTURE_REPO)
    second_manifest = load_db_manifest(FIXTURE_REPO)
    self.assertEqual(before, canonical_hashes(FIXTURE_REPO))
    self.assertEqual(first_manifest, second_manifest)
    self.assertEqual(first["derived_edges"], second["derived_edges"])
```

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m unittest tests.library_v5.test_db_build_integration -v
```
Expected: ordinary build still calls `write_derived_edges`.

- [ ] **Step 3: Replace the production edge path in `build.py`**

Target flow:

```python
before = canonical_hashes(repo_root)
if clean:
    clean_generated(repo_root)

db_result = compile_database(repo_root)
result["database"] = {
    "path": str(db_result.db_path.relative_to(repo_root)),
    "table_counts": db_result.table_counts,
}
result["derived_edges"] = export_work_graph(db_result.db_path, repo_root / "data/derived")
write_db_manifest(repo_root, db_result.db_path)
result["compatibility"] = write_compatibility_outputs(repo_root)
...
assert_canonical_unchanged(before, canonical_hashes(repo_root))
```

The ordinary build must no longer call `write_derived_edges`. Keep `derive_edges.py` only for tests/oracle until Phase 1 is accepted.

- [ ] **Step 4: Extend CI with DB-specific verification**

Add steps after unit tests:

```yaml
- name: Build DB-backed derived outputs
  run: python -m scripts.library_v5.build --repo-root .

- name: Verify DB logical determinism
  run: |
    cp data/derived/db/library_db_manifest.json /tmp/db-manifest-1.json
    python -m scripts.library_v5.build --repo-root .
    cmp /tmp/db-manifest-1.json data/derived/db/library_db_manifest.json
```

Keep the existing canonical SHA, index.html-removal, bootstrap-isolation, and ordinary-build-determinism checks. Do not `git add data/derived/db/marvel.sqlite` in any auto-commit step.

- [ ] **Step 5: Run the complete suite and fresh real-data build twice**

Run:
```bash
python -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
python -m scripts.library_v5.build --repo-root .
cp data/derived/db/library_db_manifest.json /tmp/library-db-manifest.json
python -m scripts.library_v5.build --repo-root .
cmp /tmp/library-db-manifest.json data/derived/db/library_db_manifest.json
```
Expected: all tests PASS, audit issue count 0, canonical hashes unchanged, DB logical manifest identical across builds, current work-graph semantics preserved.

- [ ] **Step 6: Commit**

```bash
git add scripts/library_v5/build.py .github/workflows/library-v5-ci.yml tests/library_v5/test_db_build_integration.py tests/library_v5/test_canonical_freeze.py
git commit -m "feat: route Marvel Library builds through SQLite"
```

---

### Task 8: Phase 1 completion audit and handoff to normalized facts

**Files:**
- Create: `docs/superpowers/reviews/2026-08-27-marvel-library-db-v1-phase1-review.md`
- Modify only if a discovered defect requires it: Phase 1 modules/tests above.

**Interfaces:**
- Consumes: fresh CI evidence, DB manifest, old-oracle parity test results.
- Produces: Phase 1 review documenting exact parity, known deferred work, and the boundary for DB v1 Phase 2.

- [ ] **Step 1: Run final verification from a clean checkout/CI run**

Required evidence:

```bash
python -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
python -m scripts.library_v5.build --repo-root .
```

Also verify:

- `git diff -- data/library data/content_audit/reviews.csv` is empty after ordinary build;
- `v_work_connection_reasons` semantic tuple set equals the Python oracle;
- DB export is deterministic;
- `PRAGMA foreign_key_check` returns no rows;
- `PRAGMA integrity_check` returns `ok`;
- public-view names and column contracts match tests;
- `main` still points to the production v5.20.5 baseline unless the user separately approves integration.

- [ ] **Step 2: Write the Phase 1 review**

The review must explicitly record:

- canonical table row counts loaded into DB;
- public view row counts;
- logical fingerprint hash summary;
- current graph reason/edge counts as observations, not correctness targets;
- parity differences, if any, with every difference either fixed or explicitly blocking completion;
- deferred tables for Phase 2: `releases`, `production_status_assertions`, `credits`, `entity_aliases`, `entity_memberships`, `events`, `event_occurrences`, `event_participants`, `event_relations`, `multiverse_transitions`, `transition_participants`, `entity_possessions`;
- explicit statement that multiverse relations have not yet been decomposed into transition facts in Phase 1.

- [ ] **Step 3: Commit the review**

```bash
git add docs/superpowers/reviews/2026-08-27-marvel-library-db-v1-phase1-review.md
git commit -m "docs: review Marvel Library DB phase1"
```

- [ ] **Step 4: Stop before Phase 2 semantic migration**

Do not add or migrate new canonical semantic tables under this plan. Phase 2 requires its own approved implementation plan because it changes the canonical fact model rather than only the compiled query layer.

---

## Plan Self-Review

### Spec coverage

- Canonical text remains authoritative: Tasks 2 and 7.
- SQLite compiled query layer: Tasks 1–2.
- FK/CHECK/integrity enforcement: Tasks 1–2.
- Alias identity vs variant distinction: Task 3.
- Versioned SQL public views: Task 4.
- Current graph parity before semantic migration: Tasks 4, 6, 8.
- Logical rather than raw-byte DB reproducibility: Task 5.
- Derived products query DB rather than canonical CSV: Tasks 6–7.
- Canonical immutability through ordinary build: Tasks 2 and 7.
- Static-HTML boundary is prepared but HTML itself is intentionally deferred to the later HTML-cutover plan.
- New normalized domains/events/transitions are intentionally deferred to Phase 2 as required by the spec's incremental migration section.

### Placeholder scan

The plan contains no `TBD`, `TODO`, `implement later`, generic “add tests”, or unspecified error-handling steps. Deferred work is explicitly scoped to a later approved plan, not left as an implementation placeholder inside Phase 1.

### Type/signature consistency

- `compile_database(repo_root: Path, output_path: Path | None = None) -> CompileResult` is consumed consistently by Tasks 5–7.
- `open_query_connection(db_path: Path) -> sqlite3.Connection` is used by views/exporters.
- `export_work_graph(db_path: Path, derived_dir: Path) -> dict[str, int]` is the sole production graph export entry point after Task 7.
- `write_db_manifest(repo_root: Path, db_path: Path) -> Path` is the manifest boundary used by ordinary build and CI.
- Public view names are fixed once in Task 4 and reused unchanged thereafter.
