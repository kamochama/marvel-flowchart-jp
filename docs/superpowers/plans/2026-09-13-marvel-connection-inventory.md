# Marvel Connection Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 現行`main`の131作品・派生接続・理由を、canonical fact、provenance、projection、defer/conflict境界まで一つの読み取り専用inventoryとして固定する。

**Architecture:** 既存の独立監査器`connectivity_audit.audit_repository`を唯一の入力源とし、その出力を純粋な正規化関数でinventory契約へ変換する。canonical CSV、evidence、reviews、HTML、derived CSVは変更せず、JSONとレビュー文書だけを生成する。

**Tech Stack:** bundled Python 3、既存`connectivity_audit.py`、CSV/JSON、unittest、Markdown。

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` および `docs/superpowers/plans/2026-09-02-marvel-connection-complete-audit.md`

## Global Constraints

- canonical factsは`data/library/`、監査履歴は`data/content_audit/`を正本とし、本計画では編集しない。
- `work_edges_all.csv`の派生edgeはsemantic truthではなく、必ずreasonのsupport fact IDとprovenanceを併記する。
- `legacy_seed`は`needs-source`、`conflicted`は`explicit-conflict`、根拠なしの遷移は`defer`として保持し、推測で`source_verified`へ昇格しない。
- 共有continuity、同一俳優、タイトル類似だけで新しいwork pairを追加しない。
- Windowsではbundled Pythonを`& $MarvelPython -B -m ...`で起動する。
- この工程はinventory-onlyであり、semantic correction、CSV追記、evidence/review追加、公開HTML変更を行わない。

---

### Task 1: RED inventory coverage contract

**Files:**
- Create: `tests/library_v5/test_connection_inventory.py`
- Read: `scripts/library_v5/connectivity_audit.py`

**Interfaces:**
- Consumes: `scripts.library_v5.connection_inventory.build_inventory(report)`（Task 2で実装）
- Produces: `ConnectionInventoryTests`が要求する`works`、`edges`、`reasons`、`coverage`、`dispositions`、`zero_degree_works`フィールド契約。

- [ ] **Step 1: Write failing tests**

```python
from scripts.library_v5.connection_inventory import audit_inventory

report = audit_inventory(REPO_ROOT)
assert report["counts"]["works"] == len(report["works"])
assert report["counts"]["edges"] == len(report["edges"])
assert report["coverage"]["missing_reason_ids"] == []
assert report["coverage"]["duplicate_reason_ids"] == []
assert report["coverage"]["projection_mismatches"] == 0
assert report["coverage"]["reason_orphans"] == 0
assert report["coverage"]["unsupported_transition_edges"] == 0
assert set(report["dispositions"]) <= {"retain", "needs-source", "explicit-conflict", "defer"}
```

Add a synthetic fixture test that removes one reason from an otherwise valid report and asserts `missing_reason_ids` contains that exact ID. The test must fail before the implementation exists.

- [ ] **Step 2: Run the focused tests to verify RED**

```powershell
$MarvelPython='C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -B -m unittest tests.library_v5.test_connection_inventory -v
```

Expected: import/attribute failure for the new inventory module.

---

### Task 2: Implement pure inventory normalization

**Files:**
- Create: `scripts/library_v5/connection_inventory.py`
- Test: `tests/library_v5/test_connection_inventory.py`

**Interfaces:**
- Consumes: `connectivity_audit.audit_repository(root)` report with `edge_inventory` and `work_inventory`.
- Produces: `audit_inventory(root: Path) -> dict[str, Any]`, `build_inventory(report: Mapping[str, Any]) -> dict[str, Any]`, and `render_markdown(inventory: Mapping[str, Any]) -> str`.

- [ ] **Step 1: Implement coverage normalization**

Implement `build_inventory` without importing production derivation code. It must:

1. copy the baseline SHA, canonical hash, counts, and existing edge/work inventories;
2. flatten every nested reason into one `reasons` list keyed by `reason_id`;
3. attach `source_fact_table`, normalized source fact IDs, evidence IDs, review IDs, verification statuses, and certainty values to every reason;
4. report exact `missing_reason_ids`, `duplicate_reason_ids`, `missing_work_ids`, `duplicate_work_ids`, and `duplicate_edge_pairs`;
5. independently compare canonical work IDs and derived edge/reason IDs with `flowchart.json`, and fail on missing/extra payload nodes, pairs, or reasons;
6. copy `edge_pair_mismatches`, `reason_orphans`, `unsupported_pair_edges`, and verified-reason provenance gaps into `coverage`;
7. count dispositions by edge, work, and reason, while preserving `zero_degree_works` as an explicit list;
8. reject an unknown disposition with a deterministic `ValueError` instead of silently mapping it to `defer`.

```python
def build_inventory(report: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the independent connectivity audit into a complete inventory."""
```

- [ ] **Step 2: Add CLI output**

Implement `audit_inventory(root)` by calling only `audit_repository(root)` and passing its result to `build_inventory`. Add:

```text
python -m scripts.library_v5.connection_inventory --root . --json <path> --markdown <path>
```

The command must exit nonzero when `coverage` contains a mismatch/orphan/unsupported transition or when any work/reason ID is missing or duplicated.

- [ ] **Step 3: Run focused tests to verify GREEN**

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_connection_inventory tests.library_v5.test_connectivity_audit tests.library_v5.test_connectivity_projection_contract -v
```

---

### Task 3: Generate the current inventory review artifact

**Files:**
- Create: `docs/superpowers/reviews/2026-09-13-marvel-connection-inventory.md`
- Read: `data/derived/work_edges_all.csv`, `data/derived/work_pair_reasons.csv`, all canonical fact tables

**Interfaces:**
- Consumes: `connection_inventory --json/--markdown` output from Task 2.
- Produces: a committed, read-only baseline review with all works and all derived pairs represented.

- [ ] **Step 1: Generate JSON and Markdown in a temporary location**

```powershell
$tmpJson=Join-Path $env:TEMP 'marvel-connection-inventory.json'
$tmpMd=Join-Path $env:TEMP 'marvel-connection-inventory.md'
& $MarvelPython -B -m scripts.library_v5.connection_inventory --root . --json $tmpJson --markdown $tmpMd
```

- [ ] **Step 2: Review the artifact before copying it**

The document must record the current observed counts (131 works, 355 edge pairs, 562 reasons), baseline SHA `e720da7270192b007115e27c60a0749c2046a816`, canonical input hash, zero-degree works, disposition counts, source fact table/evidence/review links, payload parity, and the zero structural coverage failures. It must explicitly say that `needs-source`, `explicit-conflict`, and `defer` are dispositions, not requests to mutate canonical data.

- [ ] **Step 3: Commit only the review artifact and inventory implementation**

```powershell
git add scripts/library_v5/connection_inventory.py tests/library_v5/test_connection_inventory.py docs/superpowers/reviews/2026-09-13-marvel-connection-inventory.md docs/superpowers/plans/2026-09-13-marvel-connection-inventory.md
git diff --cached --check
git commit -m "audit: add complete connection inventory"
```

The staged diff must contain no `data/library/**`, `data/content_audit/**`, or `index.html` changes.

---

### Task 4: Full verification and review gate

**Files:**
- Read: complete branch diff and generated review artifact
- Test: all `tests/library_v5/test_*.py`

- [ ] **Step 1: Run the full bundled suite and deterministic build**

```powershell
& $MarvelPython -B -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -B -m scripts.library_v5.build --repo-root .
```

- [ ] **Step 2: Re-run inventory and strict invariants**

Verify that the inventory reports zero missing/duplicate IDs, zero pair/reason orphans, zero unsupported transition edges, and that canonical hashes before/after build are unchanged. Remove only known transient build outputs and `__pycache__` paths.

- [ ] **Step 3: Request independent read-only review**

Send the branch SHA, base SHA, complete diff file list, inventory counts, and full verification results to ordinary ChatGPT. The review question must ask whether the artifact is inventory-only and whether any disposition incorrectly asserts semantic correctness.

- [ ] **Step 4: Stop before semantic correction**

Do not promote, delete, or rewrite any work relation, appearance, transition, chronology, release, or status fact in this plan. Any `needs-source`, `explicit-conflict`, or `defer` item becomes input to a separately approved evidence/review batch.
