# Marvel UI Single Sheet Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** detail／reason／settings／表示ビュー選択を唯一の SheetHost へ集約し、現行モバイルのタップ＝ゴール操作と PC の閲覧操作を維持する。

**Architecture:** 公開 `index.html` の単一ファイル構成を維持し、既存 `mobileSheet` DOM を唯一の SheetHost として mobile modal／PC docked に投影する。既存 `marvelEffectiveSheetContent`、`marvelCloseUiOverlay`、`marvelUiCommands`、履歴 writer を利用し、旧表示ビュー選択は `settings.section='display'` へ移す。canonical データ、選択計算、描画エンジンを再実装しない。

**Tech Stack:** Vanilla JavaScript／HTML／CSS、Python unittest、Node.js Chrome/CDP browser audit、静的 GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-09-09-marvel-pc-mobile-ui-architecture-design.md` §9、§13 Phase 3。以下の操作境界は最新の依頼と現行 `v5.18.0` を優先し、旧仕様 §1.1／§8／§12 の mobile tap＝inspection へ変更しない。

## Global Constraints

- 公開プランは引き続き `site-proposal`（サイト提案ルート）と `complete`（完全版）の2つだけとする。
- canonical CSV、永続レビュー履歴、作品・人物・関係ID。
- 関係グラフ、世界線、時系列の既存トポロジーと意味論。
- 全作品探索、静的GitHub Pages、共有リンク、視聴済みデータ、配布ZIP構成。
- 上記3行は仕様 §14 の「変更しないもの」であり、本計画でも変更しない。
- モバイル作品タップは現行のゴール選択・再タップ解除。PC作品クリックは inspection、明示ゴール操作は goals。背景／ドラッグの既存回帰契約を維持する。
- シートを開く／閉じる／対象変更するだけでは goals、current goal、inspection、tier、panel、camera、search、plan scroll を変更しない。ただし inspection 由来の PC docked detail の閉じる操作だけは `clearInspection()`。
- `closed | detail | reason | settings` の一種類だけを描画し、検索結果は search surface に保持する。新しい search overlay や chooser overlay kind を作らない。
- Shell 判定式を変更しない。既存 canonical predicate に基づく mobile は modal、compact／desktop は docked とし、新しい幅判定を追加しない。
- 本成果物は計画のみ。以下のコード／テスト／コミットは将来の実装手順であり、計画作成時には実行しない。

---

## Execution boundary and file ownership

実装開始時に `git fetch origin`、`git status --short`、`git rev-parse HEAD`、`git rev-parse origin/main` で実 HEAD と差分を確認する。計画枝と最新 main の差分を照合してから通常 `codex/` 実装枝を使い、main へ直接コミットしない。既存の未追跡ファイルは削除しない。

| File | Future responsibility |
| --- | --- |
| `index.html` | SheetHost DOM/CSS、単一 lifecycle、detail/reason/settings renderer、既存 command/history adapter |
| `tests/library_v5/test_mobile_shell_contract.py` | DOM所有権、legacy adapter、非再構築の構造契約 |
| `tests/library_v5/test_ui_architecture_contract.py` | effective content／close の既存純粋関数契約 |
| `tests/library_v5/browser_mobile_shell_audit.mjs` | 実入力による単一 host、内容、dismiss、履歴、responsive監査 |
| `tests/library_v5/test_browser_mobile_shell_audit.py` | JSON report 必須項目・成功条件の検証 |

`mobileSheet`／`mobileSheetBody`／`mobileSheetClose` ID は互換性のため保持する。host 自身を body 直下へ一度だけ移し、docked 時は PC 右ペイン用 slot に同じ element を配置する。祖先を `inert` にしない位置に host を置く。PC の作品一覧／接続一覧／PATH説明は保持し、旧 `#detail` は重複する詳細 renderer の所有者として残さない。既存ローカル参照を無効にするような無計画な ID 削除は行わない。

### Shared interfaces for Tasks 1–7

```js
// Overlay は store の唯一の正本。旧 sheet/sheetWork は読み取り互換 projection。
// reason の relationId は reason_id ではなく既存 reason row の relation_id。
// settings section は 'display' | 'general' | 'legend'、不明値は 'general'。
// closed | {kind:'detail',workId:string}
// | {kind:'reason',relationId:string,sourceId:string,targetId:string}
// | {kind:'settings',section?:string}
// Presentation: 'modal' | 'docked'
window.marvelSheetHost = Object.freeze({
  open,       // (overlay, {origin?:HTMLElement}={}) => boolean
  close,      // ({restoreFocus?:boolean,syncHistory?:boolean}={}) => boolean
  refresh,    // () => void; projects current state, never writes history
  getSnapshot // () => {overlay,presentation,effectiveContent}
});
// readSheetRelation(relationId, sourceId?, targetId?) =>
// null | {relationId,sourceId,targetId,rows:Array<existing reason row>}
// renderSheetContent(content) => void; writes mobileSheetBody only
// syncSheetPresentation() => void; same DOM identity, no semantic writes
```

現行 `marvelLegacyUiBridge.getSnapshot()` の inspection/goals を読み取り、`marvelMobileUiStore` の overlay と組み合わせて `marvelCreateUiState` に渡す。第二の選択 store を作らない。既存 `setSheet(kind,id)`／`openMobileSheet(kind,id)`／`closeMobileSheet(options)` は互換 adapter として残すが、DOM更新・独立購読・独自の履歴書込みを持たせない。

## Verification commands used below

すべて実装 worktree のルートで実行する。

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_ui_architecture_contract tests.library_v5.test_browser_mobile_shell_audit -v
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
```

前者を以下「focused unit」、後者を「focused browser」と呼ぶ。Chrome 未検出時は実在する Chrome の絶対パスを `MARVEL_CHROME_BIN` に設定する。環境失敗を RED 証拠にしない。RED は新規 assertion が意図する現行動作との差で失敗したことを記録する。

### Task 1: Single state and host ownership

**Files:** Modify `index.html`（`createMobileUiStore`、M2 lifecycle、Sheet DOM）、`tests/library_v5/test_mobile_shell_contract.py`、`tests/library_v5/browser_mobile_shell_audit.mjs`。

**Interfaces:** Consumes `marvelLegacyUiBridge`、`marvelCreateUiState`、`marvelEffectiveSheetContent`。Produces 上記 `marvelSheetHost` API と store `setOverlay(overlay)`。`getState().overlay` を正本とし、`sheet/sheetWork` はそこから算出する。

- [ ] **Step 1: Add RED ownership assertions.** `MobileShellContractTests` に次を追加する。既存「host は main より前」のテストは mobileViewHost/nav の位置検証を残し、SheetHost の単一性・modal時の body 配置へ意図的に更新する。

```python
def test_shared_sheet_has_one_owner(self):
    self.assertEqual(self.source.count('id="mobileSheet"'), 1)
    self.assertIn('window.marvelSheetHost', self.source)
    self.assertIn('setOverlay', function_body(self.source, 'createMobileUiStore'))
    self.assertIn('marvelSheetHost.open', function_body(self.source, 'openMobileSheet'))
```

- [ ] **Step 2: Run focused unit; record missing SheetHost / setOverlay failures.** Existing goal-selection assertions must remain GREEN.
- [ ] **Step 3: Implement the state owner and projection.** Normalize overlay using the existing UI-state helper; calculate legacy fields without independent storage. Keep history policy in the existing writer and one subscription rendering the host.

```js
function openMobileSheet(kind,id){
  const overlay=kind==='detail'?{kind,workId:id}
    :kind==='reason'?{kind,relationId:id}
    :kind==='settings'?{kind,section:id||'general'}:{kind:'closed'};
  return window.marvelSheetHost.open(overlay);
}
function closeMobileSheet(options={}){
  return window.marvelSheetHost.close(options);
}
```

既存履歴テストで旧 wrapper の関数本文を検査する箇所は owner 本体に検証先を移す。意味条件、直接リンク、親entry判定の assertion は削らない。
- [ ] **Step 4: Run focused unit and focused browser.** Browser snapshot に `sheet.hostCount` を追加し、detail→settings を開いた全時点で `document.querySelectorAll('#mobileSheet').length===1` と同時可視 dialog 数≤1を確認する。
- [ ] **Step 5: Commit only this task.** `git add index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs` then `git commit -m "refactor: establish a single sheet state owner"`。

### Task 2: Shared detail content and PC docked projection

**Files:** Modify `index.html`（`mobileWorkDetailHtml`、`marvelRenderFocusedDetail`、right pane、Sheet CSS）、`tests/library_v5/browser_mobile_shell_audit.mjs`、`tests/library_v5/test_ui_architecture_contract.py`。

**Interfaces:** Consumes Task 1 host、`marvelUiCommands`。Produces `renderSheetContent(content)` の detail branch、`syncSheetPresentation()`。Work metadata は既存 `nm`／`WORK_DETAILS` から読む。

- [ ] **Step 1: Add RED live browser assertions.** 既存 CDP `pageEvaluate`／`clickPoint`／`pointForSelector`／`waitFor` を使い、PCでゴール[A,B]のままノードCをクリックし、host snapshot の `overlay.kind==='closed'` と `effectiveContent.workId===C` を検証する。設定を開いて閉じるとCへ戻り、docked detail自体の閉じるではinspectionだけ消える。純粋関数テストだけで実DOM成功としない。

```js
const detailState=await pageEvaluate(cdp, `return {
  sheet:window.marvelSheetHost.getSnapshot(),
  selection:window.marvelUiCommands.readSelection(),
  count:document.querySelectorAll('#mobileSheetBody').length
};`);
if(detailState.count!==1 || detailState.sheet.effectiveContent.workId!==inspectedId)
  failures.push('docked detail must display the inspected work in one body');
```

- [ ] **Step 2: Run focused browser; record missing docked content failure.** Keep mobile tap→goal／repeat tap→remove as independent positive control.
- [ ] **Step 3: Extract the shared detail renderer into the existing HTML script.** Reuse title/title_en/release, synopsis_ja/map_role_ja, existing official source metadata and previous/next links. Render goal toggle and chart action via commands; remove the second desktop detail-content renderer after migrating its callers.

```js
const effective=window.marvelEffectiveSheetContent(state,presentation);
renderSheetContent(effective);
// Explicit overlay closes without clearing inspection.
// Only fallback docked detail uses this branch:
if(state.overlay.kind==='closed' && presentation==='docked'){
  window.marvelUiCommands.clearInspection();
}
```

`marvelRenderFocusedDetail(id)` は host refresh 互換入口へ変え、ゴール操作や `renderFocusHighlight` から再帰的に選択を更新しない。PC一覧・接続タブ・PATH説明は残す。
- [ ] **Step 4: Run focused unit and focused browser.** Mobile detail open/close preserves current goal/order/tier and does not appear on chart tap; PC overlay priority and close fallback pass. Assert existing camera transform unchanged.
- [ ] **Step 5: Commit.** `git add index.html tests/library_v5/browser_mobile_shell_audit.mjs tests/library_v5/test_ui_architecture_contract.py` then `git commit -m "feat: share detail content across modal and docked sheets"`。

### Task 3: Real relation content with stable identity

**Files:** Modify `index.html`（`reasonsById` reader、connection reason actions、URL adapter）、`tests/library_v5/browser_mobile_shell_audit.mjs`、`tests/library_v5/test_mobile_shell_contract.py`。

**Interfaces:** Consumes Task 1 overlay API。Produces `readSheetRelation(relationId,sourceId?,targetId?)` and reason renderer. Existing payload rows have `reason_id`、`relation_id`、`source_work_id`、`target_work_id`、`notes`、`verification_statuses`、`certainty_values`。

- [ ] **Step 1: Add RED reason tests.** Use an existing `explicit_relation` row selected from `data/derived/flowchart.json` with nonempty `relation_id`, never synthetic `audit-relation`. Open through a visible connection reason button, verify canonical ID and exact endpoints. Invalid relation and mismatched endpoint must resolve to closed. Replace prior dummy reason-history scenario with this real fixture, preserving its history assertions.

```js
const relation=payload.reasons.find(row=>row.reason_kind==='explicit_relation'&&row.relation_id);
if(!relation)throw new Error('existing explicit relation fixture is required');
// payload is read once from served repo data by the runner, never mutated.
const expected={relationId:relation.relation_id,
  sourceId:relation.source_work_id,targetId:relation.target_work_id};
```

- [ ] **Step 2: Run focused browser; record placeholder/identity failure.** Do not promote or create facts to obtain a fixture.
- [ ] **Step 3: Implement exact lookup and real content.** Public reason links use canonical `relation_id`; derived reasons lacking one retain their current connection explanation and receive no fabricated relation overlay.

```js
function readSheetRelation(relationId,sourceId,targetId){
  const rows=Object.values(reasonsById).filter(row=>
    row.reason_kind==='explicit_relation'&&row.relation_id===relationId);
  if(!rows.length)return null;
  const first=rows[0],source=first.source_work_id,target=first.target_work_id;
  if(rows.some(row=>row.source_work_id!==source||row.target_work_id!==target))return null;
  if((sourceId&&sourceId!==source)||(targetId&&targetId!==target))return null;
  return {relationId,sourceId:source,targetId:target,rows};
}
```

Render escaped endpoint titles、registered notes/type、verification/certainty; do not invent citations absent from payload. Keep `sheet=reason&sheetWork=<relation_id>` compatible and add optional `sheetSource`／`sheetTarget` keys for endpoint validation. `sheetWork` on old detail links still means work ID. No relation inference from a work ID or chronology adjacency.
- [ ] **Step 4: Run focused unit and focused browser.** Direct URL, reload, Back/Forward preserve exact relation; malformed target closes safely and unknown query/hash survives.
- [ ] **Step 5: Commit.** `git add index.html tests/library_v5/browser_mobile_shell_audit.mjs tests/library_v5/test_mobile_shell_contract.py` then `git commit -m "feat: render sheet reasons from canonical relation identifiers"`。

### Task 4: Settings and display chooser migration

**Files:** Modify `index.html`（`mobileAreaSheet` markup/CSS/lifecycle、settings renderer）、`tests/library_v5/test_mobile_shell_contract.py`、`tests/library_v5/browser_mobile_shell_audit.mjs`。

**Interfaces:** Consumes host `open({kind:'settings',section:'display'})`、`activatePanel`、`setMobileView`、`marvelSetConnectionTier` and existing combine/path controls. Produces functional settings content; old `openMobileAreaMenu`／`closeMobileAreaMenu` become wrappers.

- [ ] **Step 1: Add RED structure and interaction tests.** Remove no coverage: change chooser selectors from `#mobileAreaSheet` to `#mobileSheet [data-sheet-section="display"]`. Test detail→chooser→reason replaces visible content without double modal.

```python
def test_display_chooser_uses_shared_settings_host(self):
    self.assertNotIn('id="mobileAreaSheet"', self.source)
    self.assertIn('marvelSheetHost.open', function_body(self.source,'openMobileAreaMenu'))
    self.assertIn("section:'display'", function_body(self.source,'openMobileAreaMenu'))
```

- [ ] **Step 2: Run focused unit and focused browser; record legacy chooser failure.** Keep existing release/overview/characters and non-chart chooser scenarios.
- [ ] **Step 3: Move chooser content and migrate lifecycle.** Keep `data-mobile-target` for overview/release/chronology/watch/characters. `watch` maps to plan; other targets call the existing panel switch and chart surface transition. Settings exposes existing two tiers, OR/AND/PATH and registered legend content. Delegate setting changes to existing control command paths, without cloning state or dispatching duplicate changes.

```js
window.openMobileAreaMenu=function(){
  return window.marvelSheetHost.open({kind:'settings',section:'display'},
    {origin:document.activeElement});
};
window.closeMobileAreaMenu=function(){return window.marvelSheetHost.close();};
```

Remove old `mobileAreaOpen`／focus owner／Escape handler／backdrop handler/CSS and `mobileAreaSheet` DOM. Update aria-controls to mobileSheet; aria-expanded derives from current settings section. Panel choice is an intentional navigation change; dismiss its overlay before saving destination history so Back cannot undo the selected panel accidentally. Do not call history.back asynchronously and then replace the departing entry with a new panel.
- [ ] **Step 4: Run focused unit and focused browser.** All five chooser targets work from chart/search/plan, tier exposes only two options, each action occurs once. Opening settings alone has zero chart rebuilds; intentional panel change may mount the selected existing renderer.
- [ ] **Step 5: Commit.** `git add index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs` then `git commit -m "feat: move settings and view chooser into shared sheet"`。

### Task 5: Modal accessibility, pointer dismissal and 44px controls

**Files:** Modify `index.html`（SheetHost lifecycle/CSS）、`tests/library_v5/browser_mobile_shell_audit.mjs`。

**Interfaces:** Consumes current effective content/presentation; produces shared modal enter/leave lifecycle with prior inert/style snapshots and ordered focus restoration (origin → corresponding work card → current surface heading).

- [ ] **Step 1: Add RED physical interaction assertions.** With actual CDP Tab/Shift+Tab/Escape/pointer events test focus wrap, background scroll lock, backdrop down+up, card down→backdrop up, backdrop down→card up, pointercancel, and close focus fallback when origin was removed. Check every visible sheet action and plan goal removal control with boundingClientRect width/height ≥44.

```js
const a11y=await pageEvaluate(cdp, `const host=document.getElementById('mobileSheet');
return {modal:host.getAttribute('aria-modal'),
  sizes:[...host.querySelectorAll('button,input,select,a[href]')]
    .filter(el=>el.getClientRects().length)
    .map(el=>({label:el.textContent,width:el.getBoundingClientRect().width,
      height:el.getBoundingClientRect().height}))};`);
if(a11y.sizes.some(size=>size.width<44||size.height<44))
  failures.push('visible sheet action smaller than 44px');
```

- [ ] **Step 2: Run focused browser; record missing inert/scroll lock/38px failures.** Pointer-only clicks are insufficient for the drag-crossing cases.
- [ ] **Step 3: Implement one modal lifecycle.** Modal gets role=dialog, aria-modal=true, backdrop, focus trap, background inert and scroll lock; docked removes those modal attributes/effects and uses an Inspector region. Restore prior background inert flags and body styles precisely on close or transition. Persist document scroll without a history write, and restore it without auto-fit.

```js
let backdropPointer=null;
backdrop.addEventListener('pointerdown',event=>{
  backdropPointer=event.target===backdrop?event.pointerId:null;
  event.stopPropagation();
});
backdrop.addEventListener('pointerup',event=>{
  const dismiss=event.target===backdrop&&backdropPointer===event.pointerId;
  backdropPointer=null;event.stopPropagation();
  if(dismiss)window.marvelSheetHost.close();
});
backdrop.addEventListener('pointercancel',()=>{backdropPointer=null;});
backdrop.addEventListener('click',event=>event.stopPropagation());
```

Card pointerdown must clear stale backdropPointer; backdrop is modal-only and closing input never bubbles to chart background selection handlers. Change `.mobile-plan-goal-remove` from 38px to minimum 44×44 and make shared sheet links/buttons measurable targets; do not blanket-enlarge unrelated desktop controls.
- [ ] **Step 4: Run focused browser and focused unit.** Assert PC Tab can leave docked region, background remains interactive, Escape closes correct content, all modal dismissal variants preserve selection/inspection/camera.
- [ ] **Step 5: Commit.** `git add index.html tests/library_v5/browser_mobile_shell_audit.mjs` then `git commit -m "fix: enforce accessible sheet dismissal and touch targets"`。

### Task 6: History ownership and responsive lifecycle

**Files:** Modify `index.html`（existing history adapters／viewport subscription）、`tests/library_v5/browser_mobile_shell_audit.mjs`、`tests/library_v5/test_mobile_shell_contract.py`。

**Interfaces:** Consumes host refresh/close and existing `viewerNavigation` entryId/parentEntryId/sheetOwner guard. Produces a single history application path including settings section, reason identity and resize presentation changes.

- [ ] **Step 1: Add RED lifecycle scenarios.** Save the actual host reference in page context; test detail A→B replaces one entry, close→Back/Forward, URL-origin detail→app-child reason→close restores URL parent, direct close never navigates away, popstate does zero writes. Test 390×844, 844×390 coarse, widths 760/761/980/981 with appropriate fine/coarse metrics; same host and content survive shell changes.

```js
await pageEvaluate(cdp, `window.auditSheetElement=document.getElementById('mobileSheet');
window.auditHistoryWrites=0;
for(const method of ['pushState','replaceState']){
  const original=history[method].bind(history);
  history[method]=function(...args){window.auditHistoryWrites++;return original(...args);};
} return true;`);
// After each popstate: compare write counter with value recorded before traversal.
// After each metrics update:
const sameHost=await pageEvaluate(cdp,
  `return window.auditSheetElement===document.getElementById('mobileSheet');`);
if(!sameHost)failures.push('responsive transition replaced the sheet owner');
```

- [ ] **Step 2: Run focused browser; record identity/ownership failure.** Counter instrumentation is observation only; normal user interaction drives UI, direct URL fixtures use navigation.
- [ ] **Step 3: Route history through owner.** New overlay pushes; same detail target replacement replaces; close uses history.back only for validated current app-owned entry with matching parent identity. URL-origin close replaces to closed. During popstate use existing depth guard and render arrived snapshot without writes. Preserve unknown query keys and `#room=...`.

```js
function syncSheetPresentation(){
  const state=readSheetState();
  // readSheetState(): compose legacy bridge selection + store.overlay,
  // using marvelCreateUiState; no writes and no secondary cache.
  const shell=window.marvelClassifyShell({
    layoutWidth:document.documentElement.clientWidth,
    screenWidth:window.screen.width,screenHeight:window.screen.height,
    coarse:window.matchMedia('(pointer:coarse)').matches
  });
  const presentation=shell==='mobile'?'modal':'docked';
  applySheetPresentation(presentation);
  // applySheetPresentation(mode): move the existing host to body/PC slot;
  // enter/leave Task 5 modal lifecycle; no selection/history/chart calls.
  renderSheetContent(window.marvelEffectiveSheetContent(state,presentation));
}
```

現行コードに data-shell marker はないため、既存 `marvelClassifyShell` に layout/screen/input metrics を渡す。`visualViewport.height` は判定に使わず、キーボード開閉でpresentationを変更しない。No resize-triggered closeMobileAreaMenu, history write, or inspection mutation. Focus remains inside modal after docked→modal; modal→docked releases inert/scroll lock without losing content.
- [ ] **Step 4: Run focused unit and focused browser.** Verify goals/order/current goal, inspection, tier, active panel, camera, search query and plan scroll across transitions; no phantom open modal on mobile inspection-only state.
- [ ] **Step 5: Commit.** `git add index.html tests/library_v5/browser_mobile_shell_audit.mjs tests/library_v5/test_mobile_shell_contract.py` then `git commit -m "fix: preserve sheet history and responsive ownership"`。

### Task 7: Required audit report and full integration verification

**Files:** Modify `tests/library_v5/test_browser_mobile_shell_audit.py`、`tests/library_v5/browser_mobile_shell_audit.mjs`、`tests/library_v5/test_mobile_shell_contract.py` only for final audit consolidation. No new production functionality in this task.

**Interfaces:** Consumes all six completed contracts. Produces report `sheet.singleHost`, `realDetail`, `realReason`, `settings`, `modalA11y`, `dockedA11y`, `pointerDismiss`, `historyOwnership`, `responsive`, `touchTargets` (all boolean true), with existing report fields preserved.

- [ ] **Step 1: Add a RED wrapper test rejecting incomplete sheet evidence.** Update `_successful_report()` with these explicit true fields; retain existing timeout diagnostics and semantic-failure-no-retry contracts.

```python
def test_report_rejects_missing_sheet_single_host(self):
    report = _successful_report()
    report['sheet'].pop('singleHost')
    with self.assertRaisesRegex(AssertionError, 'singleHost'):
        _validate_report(report)
```

- [ ] **Step 2: Run focused unit; confirm validator currently accepts missing field.** Then add validation of every named flag with `is True`; a field's presence or a skipped scenario is not success.
- [ ] **Step 3: Bind flags to completed browser assertions.** Set each flag from measured outcomes, never constant success. Keep existing selection/search/plan/rerenders failures visible. Remove obsolete static assertions only where they demand retired ownership, replacing them with the corresponding new contract.

```python
for key in ('singleHost','realDetail','realReason','settings','modalA11y',
            'dockedA11y','pointerDismiss','historyOwnership','responsive','touchTargets'):
    if report['sheet'].get(key) is not True:
        raise AssertionError(f'mobile shell sheet contract failed: {key}')
```

- [ ] **Step 4: Run focused unit/browser then full verification once against final code.** Required commands:

```powershell
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
$env:MARVEL_BROWSER_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_selection_audit.BrowserSelectionAuditTests.test_headless_dom_matches_python_oracle_for_both_public_tiers -v
$env:MARVEL_BROWSER_INTERACTION_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_headless_interactions_preserve_selection_contract -v
$env:MARVEL_BROWSER_CHRONOLOGY_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_chronology_audit.BrowserChronologyAuditTests.test_headless_chronology_contract -v
$env:MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_headless_publication_order_contract -v
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
git diff --check
git diff -- data/library data/content_audit/reviews.csv
git status --short
```

Ordinary suite の browser skip は実ブラウザ成功を意味しない。既存 workflow の canonical hash preservation、DB logical determinism、graph regeneration without index、bootstrap isolation、FK／SQLite integrity、review integrity を既存 CI job 全体で確認する。選択監査131作品×公開2プラン exact-set mismatch=0、公開順 synthetic edges=0、時系列・PC操作・モバイル全ケース GREEN を要求する。行数を新しい固定目標にしない。

- [ ] **Step 5: Audit and commit the final diff.** `git diff <verified-base>...HEAD` と未コミット差分の両方を見る。canonical／永続review差分ゼロ、旧 area modal と二重 detail renderer 廃止、chart rebuild counterゼロ（単純open/close/target更新時）を確認する。build が作った生成物は一覧を確認し、必要な既存成果物のみ扱い、広域削除しない。

```powershell
git add tests/library_v5/test_browser_mobile_shell_audit.py tests/library_v5/browser_mobile_shell_audit.mjs tests/library_v5/test_mobile_shell_contract.py
git commit -m "test: require complete single sheet browser audit evidence"
```

通常 feature branch／PR 経路でレビューし、現在の standing authorization と unresolved risk の有無を確認して統合する。計画作成だけで push／merge／公開は行わない。実装PRの最終報告には検証結果、mobile tap=goal／PC inspection 維持、canonical変更ゼロ、公開影響を明記する。統合後の main／CI／Pages確認とhandoff更新は実装の統合チェックポイントとして行う。

## Self-review and completion boundary

- Phase 3 の二重modal禁止／実内容 → Tasks 1–4。
- PC fallback detail／explicit overlay優先／mobile auto-open禁止 → Task 2。
- 38px解除修正／focus復帰／inert／scroll lock／pointer背景伝播防止 → Task 5。
- 対象変更／直接リンク／履歴／responsive owner維持 → Task 6。
- 実測reportと全回帰／canonical隔離 → Task 7。
- Phase 4 の検索・予習全般の最適化、Phase 5 の全面レイアウト改修、Phase 6 の編集用ソース分割は開始しない。ここでの非再構築監査と境界幅監査は SheetHost の変更に限定する。
- 実装中に DOM所有者の移行以上の意味変更が必要になった場合は、理由を報告し、この計画の境界を広げず独立課題にする。
