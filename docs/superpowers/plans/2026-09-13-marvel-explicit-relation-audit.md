# Marvel Explicit Relation Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a read-only, fact-level inventory of every canonical `work_relations.csv` row so that explicit work-to-work connections can be promoted in small evidence-backed waves without altering graph semantics.

**Architecture:** Add a standalone Python auditor that joins `work_relations.csv` to exact `(fact_table, fact_id)` evidence/review records and registered sources, classifies each relation by its current verification disposition, and emits deterministic JSON/Markdown reports. Add regression tests that make full relation coverage, provenance isolation, and graph compatibility executable; do not modify canonical CSVs, HTML, or derived graph data in this audit PR.

**Tech Stack:** Bundled Python 3 runtime, `csv`/`json`/`pathlib`, `unittest`, existing `scripts.library_v5.connectivity_audit` and `connection_inventory` helpers, Markdown reports.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-v5-audit-status-clarification.md` and the current production handoff in `AGENTS.md`.

## Global Constraints

- Treat `(fact_table, fact_id)` as the canonical provenance key; evidence/reviews from another table must never satisfy a relation row.
- Do not change `data/library/work_relations.csv`, `sources.csv`, `evidence.csv`, `data/content_audit/reviews.csv`, HTML, or derived graph files in this audit PR.
- Active relation rows are those whose `verification_status` is not `superseded`; retain `superseded` rows in the inventory with a separate disposition.
- `source_verified` requires at least one exact same-fact primary/supporting evidence row, one exact review row, and a source ID that exists in `sources.csv`; review-linked external evidence is recorded separately and cannot satisfy this condition.
- `legacy_seed` is `needs-source` unless an explicit conflict marker is present; do not infer a semantic conflict from missing evidence.
- Preserve all relation IDs, directions, relation kinds/scopes, certainty values, and graph counts.
- Use the bundled runtime through PowerShell's `&` call operator.

---

### Task 1: Define the RED audit contract

**Files:**
- Create: `tests/library_v5/test_explicit_relation_inventory.py`
- Read: `data/library/work_relations.csv`, `data/library/sources.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, `data/derived/work_edges_all.csv`, `data/derived/work_pair_reasons.csv`

**Interfaces:**
- Consumes: `scripts.library_v5.explicit_relation_inventory.build_inventory(root)` once Task 2 exists.
- Produces: assertions for deterministic relation counts, exact provenance, full row coverage, and unchanged graph topology.

- [ ] **Step 1: Write the failing test**

  Add tests with these exact behaviors:

  ```python
  def test_inventory_covers_every_relation_row(self):
      report = build_inventory(ROOT)
      self.assertEqual(report["summary"], {
          "total": 164,
          "active": 161,
          "source_verified": 54,
          "legacy_seed": 107,
          "superseded": 3,
      })
      self.assertEqual(report["coverage"]["missing_relation_ids"], [])
      self.assertEqual(report["coverage"]["duplicate_relation_ids"], [])

  def test_source_verified_relations_have_exact_provenance(self):
      report = build_inventory(ROOT)
      self.assertEqual(report["coverage"]["source_verified_missing_evidence"], [])
      self.assertEqual(report["coverage"]["source_verified_missing_review"], [])
      self.assertEqual(report["coverage"]["source_verified_missing_source"], [])
      for row in report["relations"]:
          if row["verification_status"] == "source_verified":
              self.assertTrue(row["evidence_ids"])
              self.assertTrue(row["review_ids"])
              self.assertEqual(row["disposition"], "retain")

  def test_relation_provenance_does_not_fan_out_by_fact_id(self):
      report = build_inventory(ROOT)
      row = next(item for item in report["relations"]
                 if item["work_relation_id"] ==
                 "work-relation-avengers-age-of-ultron-2015-captain-america-civil-war-2016-aftermath")
      self.assertTrue(all(item["fact_table"] == "work_relations.csv"
                          for item in row["source_facts"]))

  def test_graph_topology_is_unchanged(self):
      report = build_inventory(ROOT)
      self.assertEqual(report["graph"], {"works": 131, "edges": 355, "reasons": 562})
      self.assertEqual(report["coverage"]["projection_mismatches"], 0)
      self.assertEqual(report["coverage"]["reason_orphans"], 0)
  ```

- [ ] **Step 2: Run the focused test to verify RED**

  Run:

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  & $MarvelPython -m unittest tests.library_v5.test_explicit_relation_inventory -v
  ```

  Expected: import failure because `scripts.library_v5.explicit_relation_inventory` does not yet exist.

### Task 2: Implement the deterministic relation inventory

**Files:**
- Create: `scripts/library_v5/explicit_relation_inventory.py`
- Test: `tests/library_v5/test_explicit_relation_inventory.py`

**Interfaces:**
- Consumes: repository root path.
- Produces: `build_inventory(root) -> dict[str, Any]` and a CLI accepting `--root`, optional `--json`, and optional `--markdown`.

- [ ] **Step 1: Implement exact CSV readers and provenance joins**

  Read rows with `utf-8-sig` and `csv.DictReader`; validate each canonical relation ID is unique. Build evidence/review maps keyed by `("work_relations.csv", relation_id)`, and resolve each evidence `source_id` against `sources.csv`. Never join by bare `fact_id`.

- [ ] **Step 2: Implement dispositions and coverage failures**

  Classify `source_verified` as `retain` only when exact same-fact qualifying evidence, exact review, and registered source IDs exist; classify `legacy_seed` as `needs-source`; classify `superseded` as `superseded`; classify an explicit `verification_status == "conflicted"` or note containing a deliberate conflict marker as `explicit-conflict`. Return sorted coverage arrays for missing/duplicate relation IDs and all provenance failures.

- [ ] **Step 3: Reuse the independent graph audit for topology checks**

  Call `scripts.library_v5.connectivity_audit.audit_repository(root)` and expose only the stable compatibility counts (`works`, `edges`, `reasons`) plus projection/reason-orphan failures. Independently enforce the reverse bijection `161 active relations <-> 161 explicit_relation reasons`, exact reason ID/pair/support/status/certainty/notes parity, exact once-on-edge membership, and zero superseded/unknown reason references. Do not regenerate or mutate derived CSVs.

- [ ] **Step 4: Add deterministic JSON/Markdown output**

  JSON must use sorted relation IDs and stable key order. Markdown must include the summary, coverage failures, and a table with relation ID, endpoints, kind, verification status, disposition, exact same-fact evidence IDs, qualifying evidence IDs, external review-linked evidence IDs, exact review IDs, and source IDs. A second section must list all `needs-source` IDs for the next bounded promotion waves.

- [ ] **Step 5: Run focused tests to verify GREEN**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_explicit_relation_inventory -v
  ```

### Task 3: Produce the audit report without canonical edits

**Files:**
- Create: `docs/superpowers/reviews/2026-09-13-marvel-explicit-relation-inventory.md`
- Create: `data/content_audit/reports/explicit_relation_inventory.json`
- Create: `data/content_audit/reports/explicit_relation_inventory.md`

**Interfaces:**
- Consumes: the Task 2 CLI and exact main baseline.
- Produces: a reproducible snapshot for selecting later 3–6 relation promotion waves.

- [ ] **Step 1: Generate reports**

  ```powershell
  & $MarvelPython -m scripts.library_v5.explicit_relation_inventory --root . --json data/content_audit/reports/explicit_relation_inventory.json --markdown data/content_audit/reports/explicit_relation_inventory.md
  ```

- [ ] **Step 2: Verify canonical isolation**

  Hash and compare all files under `data/library/` and `data/derived/` before/after report generation. The only new files may be under `data/content_audit/reports/`; no canonical or graph file may change.

- [ ] **Step 3: Write the review note**

  Record current counts (164 total / 161 active / 54 source-verified / 107 legacy-seed / 3 superseded), the zero-failure coverage result, the list of deferred IDs, and the rule that the next PR must promote at most 3–6 relations with source/evidence/review rows.

### Task 4: Full verification and independent review

**Files:**
- Read-only verification of all repository files.

- [ ] **Step 1: Run focused and full bundled tests**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_explicit_relation_inventory -v
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

- [ ] **Step 2: Run audit invariants**

  Confirm audit issues 0, review-integrity issues 0, SQLite FK 0, SQLite `integrity_check=ok`, graph topology unchanged, and `git diff --check` clean. Remove only known transient build outputs if created.

- [ ] **Step 3: Ask ordinary ChatGPT for a read-only semantic review**

  Send the branch SHA, base SHA, complete diff, generated summary, and the explicit no-canonical-edit boundary. Request checks for provenance fan-out, unsupported relation promotion, graph-topology drift, and whether the report is sufficient to select the next bounded wave.

- [ ] **Step 4: Integrate normally**

  Commit the audit-only files on a `codex/` branch, push through the GitHub API/CLI path, open a PR, wait for required CI, merge under standing authorization only after all checks and ChatGPT review are green, then verify main SHA and Pages remain unchanged semantically.

## Self-review checklist

- [ ] Every active relation ID appears exactly once in the inventory.
- [ ] No evidence/review from another fact table can satisfy a relation row.
- [ ] The auditor does not write canonical CSVs or derived graph data.
- [ ] All plan commands use the bundled Python runtime and PowerShell call operator.
- [ ] The generated report makes deferred relation IDs explicit rather than silently treating them as verified.
