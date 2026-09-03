# Marvel Library — 公開順表示契約 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 公開順表示を日付軸・作品カードのフォーカス表示として固定し、関係地図・時系列の線やモバイル合成線を生成しないことを PC／モバイルで保証する。

**Architecture:** `buildReleaseView` は作品カード、公開日、精度、時代区分、レーンだけを描画する。選択対象の `work_id` と詳細パネルは全ビューで共有するが、公開順での点灯対象はカードだけとし、関係地図の `backEdges`／`forwardEdges`／`contextEdges`／`pathEdges` を公開順 Canvas の合成線へ渡さない。

**Tech Stack:** 既存の単一 `index.html`、Node.js 標準 CDP、Python `unittest`、GitHub Actions。新規 npm 依存は追加しない。

**Spec:** `docs/superpowers/specs/2026-09-02-marvel-library-chronology-publication-order-contract.md` §3、§5

## Global Constraints

- 公開順は作品間の因果・前史・後続を表す関係グラフではない。
- SVG は `data-relationship-edges="off"` を持ち、`g.edge` と `g.chronology-edge` を生成しない。
- モバイル Canvas の合成処理も同じ線なし契約を守り、関係・時系列線を一本も描かない。
- 選択対象の `work_id` と詳細パネルはビュー間で共有し、関係地図へ戻った時は関係地図の通常ハイライトを再構築する。
- exact date、month only、year only、undated/TBD を混同せず、実日付を推測しない。
- 同日順は意味論を持たない canonical stable sort index、最後に `work_id` で決定する。
- canonical CSV、SQLite、persistent review ledger はこの viewer 実装計画では変更しない。
- Windows のローカル検証は AGENTS.md の bundled Python runtime を `& $MarvelPython` で起動する。

---

### Task 1: 公開順構造と幾何不変の RED テストを追加する

**Files:**
- Modify: `tests/library_v5/test_flowchart_selection_contract.py`
- Modify: `tests/library_v5/test_flowchart_layout_contract.py`

**Interfaces:**
- Consumes: `buildReleaseView`, `releaseMetaDate`, `releaseCardDateLabel`, and existing release SVG output.
- Produces: failing tests for all-card coverage, line-free DOM, precision labels, stable same-date ordering, and selection-independent geometry.

- [ ] **Step 1: Add static release-view structure assertions**

Require `data-relationship-edges="off"`, no `chronology-edge` in the release builder, and explicit release precision/TBD metadata in each card. Add a fixture-level test that release cards use the canonical 131-work ID set exactly once.

```python
def test_release_cards_are_a_complete_line_free_date_axis(self) -> None:
    release = function_body(self.source, "buildReleaseView")
    self.assertIn('data-relationship-edges="off"', release)
    self.assertNotIn("chronology-edge", release)
    self.assertIn("data-release-precision", release)
    self.assertIn("data-release-sort-key", release)
```

- [ ] **Step 2: Add date precision and deterministic tie-break tests**

Exercise exact day, month-only, year-only, undated/TBD, and two same-day records through the production formatting/sort helpers. Assert that display labels retain precision, no synthetic day is emitted, TBD records are in their own bucket, and the final order is stable sort index then `work_id`.

```python
def test_release_date_precision_never_invents_a_day(self) -> None:
    self.assertIn("month_only", self.source)
    self.assertIn("year_only", self.source)
    self.assertIn("date-tbd", self.source)
    self.assertRegex(self.source, r"stableSortIndex[\s\S]{0,220}work_id")
```

- [ ] **Step 3: Run focused tests and confirm RED**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_flowchart_layout_contract -v
```

Expected: FAIL because current release cards do not expose a stable sort key/TBD bucket contract and the mobile path has not yet been prohibited by a release-specific assertion.

### Task 2: Make release date layout deterministic without changing canonical dates

**Files:**
- Modify: `index.html` in `buildReleaseView`, release metadata helpers, and release card markup
- Test: `tests/library_v5/test_flowchart_selection_contract.py`
- Test: `tests/library_v5/test_flowchart_layout_contract.py`

**Interfaces:**
- Consumes: existing `RELEASE_META`, `RELEASE_HISTORY_ERAS`, `RELEASE_LANES`, `releaseMetaDate`, and `releaseCardDateLabel`.
- Produces: release cards with explicit `data-release-precision`, `data-release-sort-key`, `data-release-tbd`, and deterministic geometry.

- [ ] **Step 1: Separate display precision from the layout sort key**

Keep the source metadata unchanged. Add a helper that returns `{sortKey, precision, isTbd}` and use a layout-only sort key for month/year records. Never expose the layout anchor as a day in text or tooltip.

```js
function releaseLayoutMeta(meta, stableSortIndex, workId) {
  const precision = meta?.precision || "unknown";
  const isTbd = !meta?.sortDate || precision === "undated" || precision === "tbd";
  const sortKey = isTbd ? "9999-99-99" : String(meta.sortDate);
  return { precision, isTbd, sortKey, stableSortIndex, workId };
}
function compareReleaseItems(a, b) {
  return a.sortKey.localeCompare(b.sortKey) ||
    a.stableSortIndex - b.stableSortIndex || a.workId.localeCompare(b.workId);
}
```

- [ ] **Step 2: Render an explicit TBD bucket and stable card metadata**

Place all `isTbd` cards in an `Upcoming / date TBD` lane or terminal bucket, add the metadata attributes to each `g.release-node`, and preserve all existing card geometry for dated records.

- [ ] **Step 3: Run the focused tests to confirm GREEN**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_flowchart_layout_contract -v
```

Expected: release structure, precision, TBD, and tie-break tests pass; no relation or chronology elements are introduced.

- [ ] **Step 4: Commit the deterministic date-axis change**

```powershell
git add index.html tests/library_v5/test_flowchart_selection_contract.py tests/library_v5/test_flowchart_layout_contract.py
git commit -m "feat: make publication-order dates explicit and stable"
```

### Task 3: Enforce shared selection state with release-specific rendering

**Files:**
- Modify: `index.html` in `renderSelectionState`, `renderFocusHighlight`, `activatePanel`, and release card interaction paths
- Modify: `tests/library_v5/test_flowchart_selection_contract.py`

**Interfaces:**
- Consumes: shared `selectedIds`, `marvelDetailFocusId`, `currentSelectionState`, and panel activation.
- Produces: release card focus/detail behavior that never applies relationship edge state to the release panel.

- [ ] **Step 1: Add RED tests for card focus and panel round-trip**

Require a release card click to set the shared work selection and detail focus, require returning to overview to repaint normal relation highlights, and require release SVG to remain line-free after each transition.

```python
def test_release_selection_shares_work_focus_but_not_edges(self) -> None:
    render = function_body(self.source, "renderSelectionState")
    self.assertIn("data-relationship-edges", self.source)
    self.assertIn("release-node", self.source)
    self.assertIn("marvelDetailFocusId", render)
```

- [ ] **Step 2: Implement the release branch in the renderer**

Before applying relationship-edge classes, detect `svg.closest('.panel')?.id === 'release'`. Retain `focus`/`current-goal` on matching release cards and clear `dim`/edge classes from the release SVG. Do not mutate `selectedIds` differently from overview; `activatePanel` remains responsible for detail restoration.

- [ ] **Step 3: Run focused selection tests**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_flowchart_selection_contract -v
```

Expected: release card focus and overview round-trip tests pass while existing relation and chronology tests remain GREEN.

### Task 4: Block mobile synthetic relationship overlays in release view

**Files:**
- Modify: `index.html` in `mobileOverlaySyntheticSpecs`, `drawMobileSelectionOverlay`, and mobile release initialization
- Modify: `tests/library_v5/test_flowchart_selection_contract.py`
- Modify: `tests/library_v5/test_browser_interaction_audit.py`

**Interfaces:**
- Consumes: active panel metadata, `mobileCanvasStates`, `overlayStaticEdgeKeys`, and shared selection state.
- Produces: `mobileOverlaySyntheticSpecs` returning no relationship specs whenever the active SVG has `data-relationship-edges="off"`.

- [ ] **Step 1: Add the failing mobile prohibition test**

Require the production helper to inspect the active SVG's relationship-edge policy and the browser audit wrapper to assert `overlaySyntheticDrawn === 0` for release selection.

```python
def test_release_disables_mobile_synthetic_edges(self) -> None:
    synthetic = function_body(self.source, "mobileOverlaySyntheticSpecs")
    self.assertRegex(synthetic, r"data-relationship-edges")
    self.assertIn("relationship-edges", synthetic)
```

- [ ] **Step 2: Implement the guard at the synthetic-spec boundary**

Return an empty list before building the `backhl`/`forwardhl`/`contexthl`/`pathhl` specs when `cs.svg?.dataset.relationshipEdges === "off"` or the active panel is `release`. Do not disable chronology overlays in the chronology panel; the guard must be scoped to release only.

```js
function mobileOverlaySyntheticSpecs(cs, state) {
  const panel = cs?.svg?.closest?.(".panel")?.id;
  if (panel === "release" || cs?.svg?.dataset?.relationshipEdges === "off") return [];
  // existing overview/chronology generation follows here
}
```

- [ ] **Step 3: Run static and opt-in mobile tests**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_browser_interaction_audit -v
```

Expected: the guard tests pass; chronology overlay tests still require and preserve chronology metadata.

- [ ] **Step 4: Commit the release overlay guard**

```powershell
git add index.html tests/library_v5/test_flowchart_selection_contract.py tests/library_v5/test_browser_interaction_audit.py
git commit -m "fix: keep publication order free of mobile relation overlays"
```

### Task 5: Add the independent publication-order browser audit

**Files:**
- Create: `tests/library_v5/browser_publication_order_audit.mjs`
- Create: `tests/library_v5/test_browser_publication_order_audit.py`
- Modify: `.github/workflows/library-v5-ci.yml`

**Interfaces:**
- Consumes: exported `index.html`, real Chrome CDP pointer/touch events, and the release DOM/canvas state.
- Produces: JSON report with card coverage, focus, geometry, line-free, precision, TBD, tie-break, and panel-round-trip results.

- [ ] **Step 1: Write the Python wrapper and structural RED tests**

Require a dedicated `browser-publication-order-audit` job and `MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT=1`. The wrapper must fail if the runner emits no JSON report or if `overlaySyntheticDrawn` is nonzero.

```python
def test_runner_help_declares_release_contract(self) -> None:
    result = subprocess.run(["node", str(RUNNER), "--help"], cwd=ROOT, capture_output=True, text=True)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("geometry", result.stdout)
    self.assertIn("synthetic", result.stdout)
```

- [ ] **Step 2: Implement PC card selection and geometry snapshots**

Use the existing CDP `Input.dispatchMouseEvent` helper. Snapshot before and after selection: active panel, exact release work ID set, card `path d`, `viewBox`, year-axis line signatures, era/lane frame signatures, `g.edge` count, and `g.chronology-edge` count. Click a representative dated, month-only/year-only, and TBD card. Assert only the intended card focus/detail state changes.

- [ ] **Step 3: Implement mobile selection and no-line assertions**

Run the same representative works at the mobile viewport. Observe `marvelCanvasAudit()` and the mobile state map. Assert release `nodeBoxes` covers all works, goal focus points to the same `work_id`, and `overlaySyntheticDrawn === 0` after selection, re-tap, background tap, and drag-end.

- [ ] **Step 4: Implement panel round-trip assertions**

Select a release card, go to overview, then release again. Assert detail focus remains the same work, overview relation highlights appear only in overview, and release remains line-free. Repeat with chronology in the middle to ensure no chronology edge leaks into release.

- [ ] **Step 5: Add the CI job separately from chronology and existing audits**

Build the fixture, set `MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT=1`, run only the dedicated unittest, and print a summary such as `cards=131, failures=0, syntheticEdges=0`. Do not make the normal test job depend on a browser that is not installed locally; the dedicated job installs/detects Chrome as existing jobs do.

- [ ] **Step 6: Run the audit locally when Chrome is available**

```powershell
$env:MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_headless_publication_order_contract -v
Remove-Item Env:MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT
```

Expected: all PC/mobile line-free and geometry cases pass; without Chrome only the opt-in test skips and static wrapper tests remain GREEN.

### Task 6: Full verification and documentation handoff

**Files:**
- Create: `docs/superpowers/reviews/2026-09-02-marvel-library-publication-order-display-review.md`
- Modify: `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`
- Modify: `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`

**Interfaces:**
- Consumes: release implementation commits, focused tests, browser report, and build output.
- Produces: an auditable release-view review and updated production boundary.

- [ ] **Step 1: Run the exact full local verification**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Expected: all existing tests pass, browser tests are skipped only without opt-in environment, build reports `audit_issue_count=0`, FK rows `0`, and SQLite `integrity_check=ok`.

- [ ] **Step 2: Inspect the full diff and generated files**

Confirm that only viewer/tests/CI/docs changed; `data/library/**` and `data/content_audit/reviews.csv` remain unchanged. Remove only known generated audit/DB paths when necessary and rerun `git diff --check` and `git status --short --untracked-files=all`.

- [ ] **Step 3: Record the line-free publication-order boundary**

The review must state that shared work selection/detail focus does not turn publication order into a relation graph, that mobile synthetic relation/chronology edges are zero, and that date precision/TBD values are not inferred.

- [ ] **Step 4: Commit documentation and stop at the merge gate**

```powershell
git add docs/superpowers/reviews/2026-09-02-marvel-library-publication-order-display-review.md NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md
git commit -m "docs: record publication-order display audit boundary"
```

Do not merge or publish until the branch diff, CI, and generated artifacts have been reviewed under the repository's normal approval gate.
