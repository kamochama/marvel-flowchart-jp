# Marvel Library — 時系列表示契約 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 世界線・時系列表示を関係地図から分離したまま、固有 edge ID、選択モード、non-traversable 除外、SVG／Canvas parity を実装・監査する。

**Architecture:** `buildChronologyView` が生成する chronology edge を、作品関係 `EDGES` と別の表示トポロジーとして扱う。classifier は traversal adjacency を source/target で構築するが、結果と DOM／Canvas の実体化単位は stable `edge_id` で返す。`display_only=true` は必ず `traversable=false` とし、表示には残して選択・PATH・理由・予習ルートから除外する。

**Tech Stack:** 既存の単一 `index.html`、Node.js 標準 CDP、Python `unittest`、GitHub Actions。新規 npm 依存は追加しない。

**Spec:** `docs/superpowers/specs/2026-09-02-marvel-library-chronology-publication-order-contract.md` §3–4

## Global Constraints

- 関係地図の `EDGES`、`work_edges_all`、`work_pair_reasons` を時系列表示線の意味論に使用しない。
- `display_only=true => traversable=false` を不変条件とする。
- `order`、`track`、カード配置順から時系列 edge を自動生成しない。
- 公開5モード（`complete`、`site-proposal`、`OR`、`AND`、`PATH`）と、公開scope UIを追加しない内部unit-only契約 `previous1` は、明示された chronology edge だけに適用する。
- `traversable=false`／display-only は selection traversal、PATH、reason、公式予習ルート、Canvas 合成線に使用しない。
- SVG と Canvas の chronology edge ID 集合・分類結果を一致させる。
- canonical CSV、SQLite、persistent review ledger はこの viewer 実装計画では変更しない。
- Windows のローカル検証は AGENTS.md の bundled Python runtime を `& $MarvelPython` で起動する。

---

### Task 1: Chronology edge 契約の RED テストを追加する

**Files:**
- Modify: `tests/library_v5/test_flowchart_selection_contract.py`
- Modify: `tests/library_v5/test_runtime_selection_classifier.py`
- Modify: `tests/library_v5/runtime_selection_classifier.mjs`

**Interfaces:**
- Consumes: production `classifyChronologySelection`, `renderChronologySelectionState`, and chronology DOM metadata.
- Produces: failing tests that require `edge_id`, `display_only => !traversable`, stable duplicate-edge handling, and chronology-specific mode semantics.

- [ ] **Step 1: Write the failing static contract tests**

Add tests to `test_flowchart_selection_contract.py` that require the chronology edge generator to emit `data-chronology-edge-id`, `data-chronology-kind`, `data-chronology-display-only`, `data-chronology-traversable`, and require `renderChronologySelectionState` and the mobile chronology mapper to use the edge ID rather than only `source->target`.

```python
def test_chronology_edges_have_stable_identity_and_display_invariant(self) -> None:
    edge_group = function_body(self.source, "chronologyEdgeGroup")
    self.assertIn("data-chronology-edge-id", edge_group)
    self.assertIn("data-chronology-kind", edge_group)
    self.assertIn("data-chronology-display-only", edge_group)
    self.assertIn("displayOnly", edge_group)
    self.assertIn("displayOnly&&!traversable", edge_group)

def test_chronology_canvas_materialization_uses_edge_id(self) -> None:
    primitive = function_body(self.source, "canvasPrimitive")
    mapper = function_body(self.source, "mobileOverlayChronologyEdgeClassMap")
    self.assertIn("overlayChronologyEdgeId", primitive)
    self.assertIn("edgeId", mapper)
```

- [ ] **Step 2: Add independent duplicate-edge and display-only fixtures**

Extend `runtime_selection_classifier.mjs` with two records having the same `source` and `target` but distinct `edge_id` values, plus one `display_only` record. Invoke the production classifier through its VM export and expect both traversable IDs to receive the same directional class while the display-only ID is absent.

```js
const duplicateEdges = [
  { edge_id: "a-goal-sequence", source: "a", target: "goal", traversable: true, display_only: false },
  { edge_id: "a-goal-branch", source: "a", target: "goal", traversable: true, display_only: false },
  { edge_id: "goal-display", source: "goal", target: "next", traversable: false, display_only: true },
];
const duplicateResult = classifyChronologySelection(duplicateEdges, {
  selectedIds: ["goal"], tier: "complete", combineMode: "or",
});
```

- [ ] **Step 3: Run only the new tests and confirm RED**

Run:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_runtime_selection_classifier -v
```

Expected: FAIL because the current generator and classifier expose only `source->target` identity and do not preserve duplicate edge IDs.

### Task 2: Stable chronology edge recordsを実装する

**Files:**
- Modify: `index.html` in `buildChronologyView`, `chronologyEdgeGroup`, `drawSequence`, and `branchBetweenRows`
- Test: `tests/library_v5/test_flowchart_selection_contract.py`

**Interfaces:**
- Consumes: existing chronology call sites and `CHRONOLOGY_META` layout records.
- Produces: `chronologyEdgeGroup(edgeId, source, target, d, klass, options)` with explicit metadata and deterministic IDs.

- [ ] **Step 1: Change the edge generator signature without changing layout geometry**

Implement the following shape and update every call in `buildChronologyView` to pass a deterministic edge ID. Keep existing `source` and `target` attributes for compatibility.

```js
function chronologyEdgeGroup(
  edgeId, source, target, d, klass,
  { kind = "sequence", traversable = true, displayOnly = false } = {},
) {
  if (displayOnly && traversable) throw new Error(`display-only chronology edge must be non-traversable: ${edgeId}`);
  return `<g class="chronology-edge"
    data-chronology-edge-id="${esc(edgeId)}"
    data-chronology-source="${esc(source)}"
    data-chronology-target="${esc(target)}"
    data-chronology-kind="${esc(kind)}"
    data-chronology-display-only="${displayOnly ? "true" : "false"}"
    data-chronology-traversable="${traversable ? "true" : "false"}">
    <title>${esc(edgeId)}</title><path class="${esc(klass)}" d="${d}"/></g>`;
}
```

Use `sequence-<source>-<target>-<lane>-<column>`, `branch-<source>-<target>-<row>`, and an explicit ID for every crossing/merge call. Do not derive IDs from `order` alone. Keep the existing Morbius sequence and Deadpool→Logan display-only cases as `displayOnly:true, traversable:false`.

- [ ] **Step 2: Add the invariant test and run it**

Run the focused test command from Task 1. Expected: the static metadata tests pass, while classifier duplicate-edge tests remain RED.

- [ ] **Step 3: Commit the self-contained generator change**

```powershell
git add index.html tests/library_v5/test_flowchart_selection_contract.py
git commit -m "feat: give chronology edges stable display identities"
```

### Task 3: Make the chronology classifier edge-ID based

**Files:**
- Modify: `index.html` in `classifyChronologySelection`, `renderChronologySelectionState`, and `mobileOverlayChronologyEdgeClassMap`
- Modify: `tests/library_v5/runtime_selection_classifier.mjs`
- Modify: `tests/library_v5/test_runtime_selection_classifier.py`

**Interfaces:**
- Consumes: records `{edge_id, source, target, traversable, display_only}` and selection state `{selectedIds, tier, combineMode, pathEdges, tierNodeIds}`.
- Produces: `Map<edge_id, "backhl"|"forwardhl"|"bothhl"|"pathhl"|"contexthl">`.

- [ ] **Step 1: Keep adjacency pair-based but store classification by edge ID**

Normalize each record once, reject `display_only && traversable`, build incoming/outgoing adjacency from `source`/`target`, and add the record's `edge_id` to the result whenever its pair is admitted. Never overwrite a result because another record has the same source/target pair.

```js
const normalized = edges.map((edge, index) => ({
  edgeId: edge.edge_id || edge.key || `${edge.source}->${edge.target}#${index}`,
  source: edge.source, target: edge.target,
  traversable: edge.traversable !== false && edge.display_only !== true,
}));
```

- [ ] **Step 2: Preserve the six mode rules as explicit edge-ID rules**

Keep the current semantics: complete walks all traversable chronology adjacency; site-proposal applies `tierNodeIds` only to incoming/back traversal; previous1 admits direct incoming only; OR unions each goal's edge-ID map; AND intersects edge IDs; PATH filters the supplied `pathEdges` against materialized traversable chronology IDs without performing a new chronology search. Display-only IDs never enter any map.

- [ ] **Step 3: Update SVG and Canvas materialization to carry the same ID**

In `renderChronologySelectionState`, read `data-chronology-edge-id` and classify by that ID. In `canvasPrimitive` and `prepareMobileSelectionWorldResources`, preserve `overlayChronologyEdgeId`, `overlayChronologyDisplayOnly`, and `overlayChronologyTraversable`. `mobileOverlayChronologyEdgeClassMap` must return the same ID-keyed map as SVG.

- [ ] **Step 4: Run the runtime fixture and focused tests to confirm GREEN**

Run:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_runtime_selection_classifier tests.library_v5.test_flowchart_selection_contract -v
```

Expected: duplicate traversable IDs receive the same class, display-only is absent, and existing previous1/AND/PATH/tier tests remain GREEN.

- [ ] **Step 5: Commit classifier and materialization changes**

```powershell
git add index.html tests/library_v5/runtime_selection_classifier.mjs tests/library_v5/test_runtime_selection_classifier.py tests/library_v5/test_flowchart_selection_contract.py
git commit -m "feat: classify chronology selections by stable edge id"
```

### Task 4: Add the independent chronology browser audit

**Files:**
- Create: `tests/library_v5/browser_chronology_audit.mjs`
- Create: `tests/library_v5/test_browser_chronology_audit.py`
- Modify: `.github/workflows/library-v5-ci.yml`

**Interfaces:**
- Consumes: exported `index.html`, real Chrome CDP pointer events, the independent runtime fixture/oracle.
- Produces: JSON report containing structural, mode, non-traversable, duplicate-ID, SVG/Canvas parity, and round-trip results.

- [ ] **Step 1: Write the Python wrapper contract**

Require a dedicated `browser-chronology-audit` job, `MARVEL_BROWSER_CHRONOLOGY_AUDIT=1`, and a summary with `failures: 0`. Keep the normal test suite environment-gated, as the existing browser audits do.

```python
def test_runner_help_declares_chronology_contract(self) -> None:
    result = subprocess.run(["node", str(RUNNER), "--help"], cwd=ROOT, capture_output=True, text=True)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("non-traversable", result.stdout)
    self.assertIn("edge-id", result.stdout)
```

- [ ] **Step 2: Implement real pointer-event cases without calling production selection functions**

Use the existing CDP helper pattern from `browser_interaction_audit.mjs`: load the page, click a chronology card, snapshot `g.chronology-edge` IDs/classes, switch `complete/site-proposal`, exercise previous1/OR/AND/PATH with public controls, click display-only endpoints, and verify no display-only ID becomes highlighted. After switching overview↔chronology, verify the selected work and chronology edge highlight repaint. Use condition polling instead of fixed sleeps.

- [ ] **Step 3: Add SVG/Canvas materialization parity assertions**

For the same selected work and mode, collect `data-chronology-edge-id` from SVG and `overlayChronologyEdgeId` from the mobile resource map. Assert equality of the full materialized ID set and of each ID's category. Assert that the release/overview `g.edge` set is not used by this audit.

- [ ] **Step 4: Add the CI job after the existing interaction audit**

The job must build the fixture, set `MARVEL_BROWSER_CHRONOLOGY_AUDIT=1`, run the dedicated unittest, and print the JSON summary. It must not weaken or skip the existing selection and interaction jobs.

- [ ] **Step 5: Run the audit locally when Chrome is available**

```powershell
$env:MARVEL_BROWSER_CHRONOLOGY_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_chronology_audit.BrowserChronologyAuditTests.test_headless_chronology_contract -v
Remove-Item Env:MARVEL_BROWSER_CHRONOLOGY_AUDIT
```

Expected: all chronology structural/five-public-mode/parity cases pass; the report explicitly includes a `previous1` internal-unit-only coverage gap when the public scope control is absent. When Chrome is unavailable, only the environment-gated test is skipped and static wrapper tests still pass.

### Task 5: Full verification and documentation handoff

**Files:**
- Modify: `docs/superpowers/reviews/2026-09-02-marvel-library-chronology-display-contract-review.md`
- Modify: `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`
- Modify: `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`

**Interfaces:**
- Consumes: all implementation commits, focused/browser reports, and build output.
- Produces: an auditable review listing passed tests, deferred canonical data work, and the new production boundary.

- [ ] **Step 1: Run the exact full local verification**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Expected: all existing tests pass, browser tests are skipped only without their opt-in environment, build reports `audit_issue_count=0`, FK rows `0`, and SQLite `integrity_check=ok`.

- [ ] **Step 2: Inspect generated output and restore a clean worktree**

Check `git diff -- data/library data/content_audit`, remove only known generated paths under `data/content_audit/` and `data/derived/` when the workflow requires it, then run `git status --short --untracked-files=all` and confirm no canonical or review file changed.

- [ ] **Step 3: Record the review boundary**

The review must explicitly state that chronology display lines are not relation facts, that no canonical chronology assertion was added, and that the browser audit covers edge IDs and SVG/Canvas materialization parity.

- [ ] **Step 4: Commit documentation and stop at the merge gate**

```powershell
git add docs/superpowers/reviews/2026-09-02-marvel-library-chronology-display-contract-review.md NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md
git commit -m "docs: record chronology display audit boundary"
```

Do not merge or publish until the branch diff, CI, and generated artifacts have been reviewed under the repository's normal approval gate.
