# Marvel Connection Complete Audit Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 131作品・全361接続を、canonical facts・evidence・review・derived viewsの起点から再監査し、欠落・誤接続・過剰接続を根拠付きで分類して修正する。

**Architecture:** まず現在のmainを監査基準として固定し、3つの読み取り専用監査を独立に実行する。作品・接続の意味論はcanonical tablesとevidenceを優先し、HTMLや既存の線だけを正解とみなさない。統合後は、各修正をREDテスト→最小変更→GREEN→全体ビルドの順で適用する。

**Tech Stack:** Python 3 bundled runtime, SQLite compiler/views, canonical CSV, static `flowchart.json`, HTML viewer, GitHub CLI/API.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`

## Global Constraints

- canonical factsは`data/library/`、監査履歴は`data/content_audit/`を正本とし、read-only監査では編集しない。
- 公式根拠のない接続を、共有continuity・同一俳優・作品掲載だけから作らない。
- work-to-work edgeはderived viewであり、イベント・transition・appearanceの意味を混同しない。
- Earth番号、variant identity、transport mechanismは根拠がない限り推測しない。
- 既存IDを維持し、verified factの意味変更には evidenceとreview transitionを伴わせる。
- Windowsではbundled Pythonを`& $MarvelPython -m ...`で起動する。
- 並列エージェントは読み取り専用とし、canonical CSVを同時編集しない。

### Task 1: Audit baseline and complete inventory

**Files:**
- Read: `data/library/*.csv`, `data/content_audit/evidence.csv`, `data/content_audit/reviews.csv`
- Read: `data/derived/flowchart.json`, `data/derived/work_edges_all.csv`, `data/derived/work_pair_reasons.csv`
- Read: `scripts/library_v5/db_views.py`, `scripts/library_v5/db_rollup.py`, `scripts/library_v5/flowchart_export.py`
- Create: `docs/superpowers/reviews/2026-09-02-marvel-connection-baseline-audit.md`

- [ ] **Step 1: Capture the baseline**

Run:

```powershell
$MarvelPython='C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -q
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Record the exit codes and observed counts for works, edges, reasons, prewatch edges, audit issues, review issues, FK checks, and SQLite integrity.

- [ ] **Step 2: Build a pair-complete inventory**

For every derived pair, record source work, target work, edge ID, every reason ID, reason kind, source fact IDs, verification status, certainty, and evidence/review references. Separately list every work with zero incoming, zero outgoing, or only one reason kind.

- [ ] **Step 3: Write the baseline review**

The review must distinguish observed graph output from a correctness judgment and must list all 131 works exactly once. It must not mutate canonical data.

### Task 2: Independent semantic connection audit

**Files:**
- Read: all canonical work relation, appearance, continuity, event, transition, entity, credit, and production tables
- Read: `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`
- Create: `docs/superpowers/reviews/2026-09-02-marvel-connection-semantic-audit.md`

- [ ] **Step 1: Re-evaluate every edge reason**

For each reason, answer whether the canonical fact actually supports the directed source→target pair, whether the direction is meaningful, and whether the fact belongs in a work edge at all. Mark `retain`, `needs-evidence`, `wrong-direction`, `duplicate`, `over-broad`, or `defer` with a precise fact ID.

- [ ] **Step 2: Check all 131 works for missing high-confidence links**

Use only explicit sequel/lead-in/aftermath facts, source-verified appearance continuity, first-class transition/event semantics, and audited prewatch policy. Record candidate pairs separately from confirmed omissions; do not add an edge merely because two titles share a franchise label.

- [ ] **Step 3: Check known risk families**

Audit multiverse returns, same-performer variants, continuity-only fan-out, event depiction versus causality, chronology-only lines, production/release metadata, and official/curated prewatch routes. Keep uncertain candidates out of the confirmed correction list.

- [ ] **Step 4: Write the semantic review**

Include a complete table of all retained and disputed edge families, with canonical source IDs and an explicit no-inference reason for every deferred candidate.

### Task 3: Independent derived/export/UI consistency audit

**Files:**
- Read: `scripts/library_v5/db_*`, `scripts/library_v5/flowchart_export.py`, `index.html`
- Read: `tests/library_v5/test_derive_*.py`, `test_db_export_parity.py`, `test_flowchart_selection_contract.py`
- Create: `docs/superpowers/reviews/2026-09-02-marvel-connection-derived-audit.md`

- [ ] **Step 1: Verify source-to-export parity**

Recompute pair and reason counts from SQLite views and compare them to CSV exports and `flowchart.json`, including stable IDs and endpoint direction.

- [ ] **Step 2: Detect derivation fan-out and duplicate rendering**

Check one edge per work pair, all reasons preserved, no normalized release/status row entering graph derivation, and no chronology/prewatch display row becoming a semantic edge.

- [ ] **Step 3: Verify public viewer behavior**

Read-only browser checks must confirm all exported edges are visible by default, selection only restyles existing edges, site-proposal/complete are the only public plan tiers, and no hidden compatibility mode creates a new pair.

- [ ] **Step 4: Write the derived review**

List every parity mismatch or UI-only presentation issue separately from canonical semantic defects.

### Task 4: Reconcile findings and define correction batches

**Files:**
- Modify: `docs/superpowers/reviews/2026-09-02-marvel-connection-reconciliation.md`
- Test: new focused tests under `tests/library_v5/` only when a concrete defect is reproducible

- [ ] **Step 1: Compare the three reviews**

Join findings by exact work pair, reason ID, and fact ID. A single-agent assertion is not sufficient for a semantic correction; inspect the cited canonical row independently.

- [ ] **Step 2: Classify each finding**

Use exactly one disposition: `retain`, `presentation-only`, `needs-source`, `canonical-fix`, `derivation-fix`, `explicit-conflict`, or `defer`. Every one of 361 current edges and every zero-degree work must receive a disposition.

- [ ] **Step 3: Split into bounded correction batches**

Group only changes that share one semantic cause and can be tested independently. Do not bulk-rewrite all CSVs from an audit spreadsheet.

### Task 5: Apply correction batches with evidence and regression tests

**Files:**
- Modify: only the canonical tables, evidence/reviews, derivation code, or HTML files named by a reconciled batch
- Test: focused regression test for each batch

- [ ] **Step 1: Write a failing regression test**

The test must reproduce the exact wrong/missing pair or derivation behavior and assert the desired directed reason/evidence boundary.

- [ ] **Step 2: Apply the smallest audited change**

Preserve IDs, add or update evidence/review records when facts become verified, and keep unresolved candidates as explicit deferred/conflict records.

- [ ] **Step 3: Run focused tests and inspect the complete diff**

Use the bundled Python runtime and strict CSV shape checks. Verify unrelated pairs and canonical hashes remain unchanged unless the batch explicitly requires them.

- [ ] **Step 4: Re-run all three audits**

Refresh all review documents and ensure every changed pair has a new disposition.

### Task 6: Final verification and integration report

**Files:**
- Read: all changed files and all three audit reviews
- Modify: `docs/superpowers/reviews/2026-09-02-marvel-connection-final-report.md`

- [ ] **Step 1: Run full verification**

```powershell
$MarvelPython='C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
git diff --check
git status --short
```

- [ ] **Step 2: Confirm semantic invariants**

Confirm audit issues, review-integrity issues, FK rows, and SQLite integrity; report changed/retained/deferred/conflicted edge counts, not only a total count.

- [ ] **Step 3: Produce the final report**

The report must state what was corrected, what remains uncertain, which work pairs were intentionally not added, and whether a separate user approval is required for any remaining batch.


