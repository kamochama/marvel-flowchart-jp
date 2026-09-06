# Marvel Mobile UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PC向けUIを縮小して使い回す方式から脱却し、共通エンジン上にスマートフォン専用シェルを段階的に導入する。

**Architecture:** 作品データ、選択、ゴール、点灯、予習計算を共通状態源として維持し、スマホ幅では専用DOMのMobile Shellを表示する。Mobile Shellは「チャート」「探す」「予習」の3画面を一つのNavigationStateと単一SheetControllerで切り替え、PC Shellは当面変更しない。

**Tech Stack:** 既存の単一静的`index.html`、標準JavaScript、SVG/Canvas、CSSメディアクエリ、Python標準ライブラリのunittest、Node.js + Chrome/CDP監査。

**Spec:** `docs/superpowers/specs/2026-09-04-marvel-mobile-ui-redesign-design.md`

## Global Constraints

- 共通エンジン、別プレゼンテーション: 作品データ、選択状態、点灯計算、予習計算はPCとスマホで共有し、画面骨格・DOM・ナビゲーション・操作モデルは分離する。
- スマホの主要画面は利用目的で「チャート」「探す」「予習」に分ける。
- 各画面は個別の選択状態を持たず、共通ストアを唯一の真実とする。
- 非アクティブ画面の重いDOMとrendererを常時生成しない。チャートのパン・ズーム状態は破棄しない。
- 既存の再タップ解除、空白タップ解除、別作品選択、44px以上のタッチ領域を維持する。
- `aria-modal="true"`、フォーカス復帰、Escape、背景タップ、ブラウザ戻る操作を実装する。
- 新規URLキーは`mview`、`goals`、`sheet`、`sheetWork`、`q`、`mfilter`とし、既存の`#room=...`を保持する。
- canonical CSV、作品間の線、世界線・時系列の意味論、PC Shellは変更しない。
- 各タスクはREDテスト → 最小実装 → GREEN → bundled-Python検証 → 小さいコミットの順で進める。

## File Map

- Modify: `index.html` — 共通状態の購読境界、Mobile Shell DOM/CSS、3画面renderer、SheetController、URL履歴同期。
- Create: `tests/library_v5/test_mobile_shell_contract.py` — Mobile ShellのDOM、状態境界、アクセシビリティ、非重複rendererの静的契約。
- Create: `tests/library_v5/browser_mobile_shell_audit.mjs` — Chrome/CDPで3画面とシートの実操作を行う監査ランナー。
- Create: `tests/library_v5/test_browser_mobile_shell_audit.py` — `MARVEL_BROWSER_MOBILE_SHELL_AUDIT=1`を要求するPythonラッパー。
- Modify: `.github/workflows/library-v5-ci.yml` — Mobile Shell監査ジョブを既存ブラウザ監査の後段に追加。
- Modify: `README.md` — 新しいスマホ導線、URL履歴、3画面の利用方法を追記（M5完了時）。

既存の`tests/library_v5/test_mobile_ux_contract.py`、`test_watch_scroll_navigation.py`、`test_browser_interaction_audit.py`は削除せず、旧契約と新契約の共存期間も実行する。

---

### Task 1: 共通状態の購読境界（M1）

**Files:**
- Modify: `index.html:4321-4322,5462-5490,5944-5965,6290-6335,7290-7308` — 既存の`selected`、`selectedIds`、`prepTier`を直接参照するUI境界に購読APIを追加。
- Create: `tests/library_v5/test_mobile_shell_contract.py` — store APIの静的契約。

**Interfaces:**
- Produces `createMobileUiStore(initialState)` returning `{getState,subscribe,setView,setGoals,setSheet,setSearch,setFilter}`.
- `getState()` returns `{view:'chart'|'search'|'plan', goalIds:string[], selectedId:string|null, sheet:'closed'|'detail'|'reason'|'settings', sheetWork:string|null, query:string, filter:string}`.
- `subscribe(listener)` calls `listener(nextState,previousState)` once for each changed state and returns an unsubscribe function.
- Existing `selectedIds`, `selected`, `prepTier`, `selectionStateCache` remain the semantic implementation and are updated through adapters; no second goal store is introduced.

- [ ] **Step 1: Write the failing contract tests**

```python
def test_mobile_store_has_single_state_source(self):
    body = function_body(self.source, "createMobileUiStore")
    self.assertIn("getState", body)
    self.assertIn("subscribe", body)
    self.assertIn("setGoals", body)
    self.assertIn("setSheet", body)

def test_mobile_store_normalizes_invalid_view_and_sheet(self):
    self.assertIn("view==='chart'", self.source)
    self.assertIn("sheet==='closed'", self.source)
    self.assertIn("window.marvelMobileUiStore", self.source)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run from the repository root:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract -v
```

Expected: FAIL because `createMobileUiStore` and the public store handle do not exist.

- [ ] **Step 3: Implement the minimal adapter**

Add one store after the global selection declarations. Normalize every input before publishing:

```javascript
function createMobileUiStore(initial={}){
  let state={view:'chart',goalIds:[],selectedId:null,sheet:'closed',sheetWork:null,query:'',filter:'',...initial};
  const listeners=new Set();
  const publish=next=>{const previous=state;state=next;listeners.forEach(fn=>fn(state,previous));};
  return {getState:()=>({...state,goalIds:[...state.goalIds]}),subscribe(fn){listeners.add(fn);return()=>listeners.delete(fn);},
    setView(view){publish({...state,view:view==='search'||view==='plan'?view:'chart'});},
    setGoals(goalIds,selectedId=null){publish({...state,goalIds:[...new Set((goalIds||[]).filter(id=>nm[id]))],selectedId});},
    setSheet(sheet,sheetWork=null){publish({...state,sheet:['detail','reason','settings'].includes(sheet)?sheet:'closed',sheetWork});},
    setSearch(query){publish({...state,query:String(query||'')});},
    setFilter(filter){publish({...state,filter:String(filter||'')});}};
}
window.marvelMobileUiStore=createMobileUiStore();
```

Wire `setGoals` from the existing `select`, `clearAllGoalsWithUndo`, and `undoClearGoals` paths after their semantic updates; do not move the graph calculation into the store.

- [ ] **Step 4: Run the focused tests and the existing mobile contracts**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_mobile_ux_contract tests.library_v5.test_watch_scroll_navigation -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add index.html tests/library_v5/test_mobile_shell_contract.py
git commit -m "refactor: expose shared mobile UI state"
```

### Task 2: Mobile Shell骨格・単一シート・履歴（M2）

**Files:**
- Modify: `index.html:613-640,813-820,4311-4313,7921-8090` — 新しいShell DOM、CSS、view/sheet/navigation handlers。
- Modify: `tests/library_v5/test_mobile_shell_contract.py` — DOMと履歴契約。

**Interfaces:**
- Produces `ensureMobileShell()`, `mountMobileView(view)`, `setMobileView(view,{pushHistory=true})`, `openMobileSheet(kind,workId)`, `closeMobileSheet({restoreFocus=true})`, `readMobileUrlState()`, `writeMobileUrlState({replace})`.
- `mountMobileView` keeps only the active view content mounted under `#mobileViewHost`; the chart renderer instance is retained in `viewStates`.

- [ ] **Step 1: Add RED tests for shell and history**

Assert that `#mobileAppShell` contains `#mobileViewHost`, `#mobileBottomNav`, one `#mobileSheet`, and that the handlers use `history.pushState`, `popstate`, `aria-modal`, and `aria-current`.

- [ ] **Step 2: Run RED**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract -v
```

Expected: FAIL because the new shell IDs and handlers are absent.

- [ ] **Step 3: Add the shell markup and styles**

Place the mobile shell after `#mobilePrimaryNav` and before `<main>` so it is independent of `#left`/`#right`. Use a fixed bottom navigation with `padding-bottom:calc(8px + env(safe-area-inset-bottom))`, 44px controls, and a single sheet with `role="dialog" aria-modal="true"`.

- [ ] **Step 4: Implement view and sheet state transitions**

`setMobileView` updates the store, mounts one view, marks one bottom-nav button `aria-current="page"`, and calls `writeMobileUrlState`. `openMobileSheet` records the opener, sets `sheetWork`, moves focus to the sheet heading, and pushes a history entry. `closeMobileSheet` sets `sheet:'closed'`, restores opener focus, and never rebuilds the chart.

- [ ] **Step 5: Implement exact URL synchronization**

Read/write `mview`, `goals`, `sheet`, `sheetWork`, `q`, and `mfilter` with `URLSearchParams`; preserve `location.hash` and ignore unknown keys. `popstate` first closes a sheet, then restores the previous view and goals.

- [ ] **Step 6: Run contracts and commit**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_mobile_ux_contract -v
git add index.html tests/library_v5/test_mobile_shell_contract.py
git commit -m "feat: add mobile shell navigation and sheet"
```

### Task 3: チャート面の移行（M3）

**Files:**
- Modify: `index.html:4411-4579,4984-5005,7350-7598` — Mobile Chart renderer wiring and compact chart controls.
- Modify: `tests/library_v5/test_mobile_shell_contract.py` — chart preservation contracts.
- Create: `tests/library_v5/browser_mobile_shell_audit.mjs` — first chart scenarios.

**Interfaces:**
- Produces `mountMobileChartView(host)`, which mounts the existing active chart panel into the mobile host without copying SVG/Canvas data.
- Consumes `mobileCanvasStates`, `viewStates`, `select`, `clearAllGoalsWithUndo`, `fitView`, and `centerNodeInView`.

- [ ] **Step 1: Write RED chart contracts**

Require `mountMobileChartView`, `mobileCanvasStates`, `viewStates`, and an explicit no-rebuild path when a sheet opens or closes.

- [ ] **Step 2: Run RED**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract -v
```

- [ ] **Step 3: Mount the existing chart renderer**

Render only the active chart view into `#mobileViewHost`, reuse its `svg-wrap`, preserve the `WeakMap` camera state, and route chart taps to the existing `select` contract. Add compact controls for 全体、選択へ、詳細、表示ビュー.

- [ ] **Step 4: Add browser audit scenarios**

The Node runner must set a 390×844 viewport and verify: chart visible; one tap selects; second tap clears; blank tap clears; drag changes camera but keeps selection; opening/closing the sheet keeps the same `data-mobile-camera` snapshot; bottom-nav buttons are reachable.

- [ ] **Step 5: Run focused tests and commit**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_browser_interaction_audit -v
git add index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs
git commit -m "feat: move chart into mobile shell"
```

### Task 4: 探す面の移行（M4）

**Files:**
- Modify: `index.html:4321-4360,5430-5510,8790-8812` — mobile search renderer and selection actions.
- Modify: `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/browser_mobile_shell_audit.mjs`.

**Interfaces:**
- Produces `mountMobileSearchView(host)` and `renderMobileSearchResults(query,filter)`.
- Search results call `window.marvelMobileUiStore.setGoals` through the existing selection adapter; they never call chart rebuild functions.

- [ ] **Step 1: Add RED search contracts**

Require a semantic search input, 44px result buttons, `renderMobileSearchResults`, and a search-to-chart action that calls `setMobileView('chart')`.

- [ ] **Step 2: Run RED**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract -v
```

- [ ] **Step 3: Implement search view**

Filter `NODES` with the existing `pass` predicate plus `mfilter`, render one button per result with title/English title/release, and expose separate buttons for 選択、チャートで見る、詳細. Debounce only DOM result updates; do not redraw SVG/Canvas while typing.

- [ ] **Step 4: Extend browser audit**

Verify Search → Spider-Man 3 → Chart preserves the selected ID and highlighted predecessor chain; query text survives a view switch and `popstate`; an empty result announces `該当なし` through an `aria-live` region.

- [ ] **Step 5: Run focused tests and commit**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract -v
git add index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs
git commit -m "feat: add mobile search view"
```

### Task 5: 予習面の移行（M5）

**Files:**
- Modify: `index.html:6690-6755,7090-7188,7308-7324` — mobile plan renderer and watched-state subscriptions.
- Modify: `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/browser_mobile_shell_audit.mjs`.
- Modify: `README.md:88-94` — mobile usage description.

**Interfaces:**
- Produces `mountMobilePlanView(host)` and `renderMobilePlanScreen()`.
- Consumes `buildMultiGoalPlan`, `renderPrepPlan`, `prepTier`, `orderedGoalIds`, and the existing watched checkbox persistence.

- [ ] **Step 1: Add RED plan contracts**

Require the public selectors `site-proposal` and `complete`, the absence of a public official-route selector, a goal summary, watched checkboxes, and a chart-return action.

- [ ] **Step 2: Run RED**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_watch_scroll_navigation -v
```

- [ ] **Step 3: Implement plan view**

Reuse `buildMultiGoalPlan` and current watch persistence. Render the current goal, site proposal/complete selector, checklist, remaining time, and a `チャートで見る` button. Tapping a plan item opens the shared detail sheet; changing a checkbox updates the store and leaves the chart camera untouched.

- [ ] **Step 4: Extend browser audit**

Verify Plan → detail sheet → Chart, watched toggle persistence, multi-goal summary, and no public `公式予習ルート` control. Verify plan DOM is absent while Chart is active.

- [ ] **Step 5: Update documentation and commit**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_watch_scroll_navigation -v
git add index.html README.md tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs
git commit -m "feat: add mobile preparation view"
```

### Task 6: 実ブラウザ監査とCI統合

**Files:**
- Create: `tests/library_v5/test_browser_mobile_shell_audit.py`.
- Modify: `tests/library_v5/browser_mobile_shell_audit.mjs`, `.github/workflows/library-v5-ci.yml`.

**Interfaces:**
- `test_browser_mobile_shell_audit.py` resolves `$ChromePath` from `MARVEL_CHROME_BIN` or the existing Chrome discovery helper and runs `node tests/library_v5/browser_mobile_shell_audit.mjs --root . --chrome $ChromePath` only when `MARVEL_BROWSER_MOBILE_SHELL_AUDIT=1`; it fails if the runner emits no JSON.
- Runner emits `{viewport,views,selection,history,sheet,rerenders,failures}` with `failures=[]` as the success contract.

- [ ] **Step 1: Add the failing Python wrapper test**

Mirror the existing browser audit wrappers, assert the environment gate, Chrome discovery, JSON output, and `failures == []`.

- [ ] **Step 2: Run the wrapper in ordinary mode**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit -v
```

Expected: the environment-gated real-browser case is skipped; static wrapper tests pass.

- [ ] **Step 3: Add the CI job after `browser-publication-order-audit`**

Use the existing Chrome discovery/build pattern, set `MARVEL_BROWSER_MOBILE_SHELL_AUDIT: '1'`, and run `test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v`.

- [ ] **Step 4: Run the real audit locally**

```powershell
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
Remove-Item Env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT -ErrorAction SilentlyContinue
```

Expected: all chart/search/plan/sheet/history scenarios pass with `failures=[]`.

- [ ] **Step 5: Commit the audit and CI changes**

```powershell
git add tests/library_v5/test_browser_mobile_shell_audit.py tests/library_v5/browser_mobile_shell_audit.mjs .github/workflows/library-v5-ci.yml
git commit -m "test: audit mobile shell flows in Chrome"
```

### Task 7: 旧モバイル層の撤去と最終検証（M6）

**Files:**
- Modify: `index.html:198-250,613-745,778-809,4311-4313` — remove obsolete mobile-only overlays and duplicate panel transforms after the new shell has full coverage.
- Modify: `tests/library_v5/test_mobile_shell_contract.py` — assert old shell is not mounted at the same time.
- Modify: `README.md` — mark the mobile shell as current behavior.

- [ ] **Step 1: Add RED cleanup contracts**

Assert that only `#mobileAppShell` is active at mobile width, old `#right` bottom-sheet transforms are absent from the mobile path, and chart/search/plan do not duplicate heavy renderers.

- [ ] **Step 2: Run RED**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract -v
```

- [ ] **Step 3: Remove only superseded CSS/handlers**

Keep shared Canvas, SVG, selection, plan, and desktop rules. Remove the old mobile-only `#right` transform path, duplicate area/search overlays, and handlers that are no longer reachable from the new shell. Do not delete `official_prewatch_routes` data or existing semantic tests.

- [ ] **Step 4: Run the complete verification surface**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Then run the real selection, interaction, chronology, publication-order, and mobile-shell audits with their environment variables. Confirm canonical hashes and graph compatibility are unchanged.

- [ ] **Step 5: Inspect and clean generated outputs**

Remove only the known generated build paths (`data/content_audit/CONTENT_AUDIT.md`, `data/content_audit/queue.csv`, `data/derived/LIBRARY_AUDIT.md`, `data/derived/audit.json`, `data/derived/db/`, `data/derived/library_manifest.json`, and Python `__pycache__` directories), then run `git diff --check` and `git status --short`.

- [ ] **Step 6: Commit the cleanup**

```powershell
git add index.html README.md tests/library_v5/test_mobile_shell_contract.py
git commit -m "refactor: retire legacy mobile presentation layer"
```
