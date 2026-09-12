# Phase 6 旧表示層の所有権ベース撤去 — Implementation Plan

**Date:** 2026-09-12  
**Design:** `docs/superpowers/specs/2026-09-12-marvel-phase6-legacy-layer-retirement-design.md`  
**Review:** ordinary ChatGPT repository review, Phase 6方針レビュー  
**Branch:** `codex/marvel-phase6-legacy-retirement`

## Objective

Phase 5で確定した `data-shell="mobile|compact|desktop"` の表示所有権を回帰テストで固定し、旧表示層のうち「実到達不能で、正本状態・意味論・computed styleに寄与しない」CSS／DOM fragment／handlerだけを同一ownerのクラスタ単位で撤去する。PC/compactの `main/#right`、mobileの `#mobileAppShell/#mobileViewHost/#mobileBottomNav/#sheetHost`、SheetHostのmodal/docked facade、検索のDOM projection、ゴール・選択・予習計算、canonical dataは保持する。

## Constraints and stop conditions

- `index.html` の大規模分割、canonical CSV、レビュー台帳、`official_prewatch_routes`、graph/worldline/chronology意味論は対象外。
- `#right` はPCの作品一覧、ゴール、Works/Links/PATH、直接接続UIとdocked SheetHostのownerなので削除しない。
- `renderMobileSearchResults()` の `#q/#branch/#character/#status` projection と `pass()`／`NODES.filter(pass)` は、DOM非依存predicateを別途作るまで削除しない。
- `openDockedInspection()`／`closeDockedInspection()` の `#detail` mirror は、writer棚卸しと実操作監査なしに削除しない。
- 旧 `body.mobile-details-open #right` と `#right` bottom-sheet `transform:translateY(...)` は「不在」を再導入防止契約として保つ。
- REDまたは実Chrome監査が失敗したら、そのクラスタの実装・削除だけを止める。既存の意味論・canonical入力を変更して帳尻を合わせない。

## Task 1 — Baseline and ownership inventory (read-only)

**Files:** `index.html`, `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/test_mobile_ux_contract.py`, `tests/library_v5/browser_mobile_shell_audit.mjs`, this plan.

1. `rg`で `#right`, `#detail`, `sheetHost`, `renderMobileSearchResults`, `openDockedInspection`, `syncSheetPresentation`, `mobile-details-open`, `translateY` のCSS／DOM／writer／listenerを列挙する。
2. `#detail.innerHTML/textContent`、`#right`のappend/insert/mount、SheetHostのparent移動、shell sync、history hydration、orientation listenerを関数単位でowner表に記録する。
3. Phase 5 baselineの全unitを実行し、削除前のRED/GREEN比較値（selected IDs、goal order/current goal、tier、active panel、camera、history、chart rebuild/fitView）を保存する。

**Gate:** canonical CSV／audit ledgerに差分がなく、baseline suiteがGREENであること。参照入口が曖昧なクラスタは削除候補に昇格しない。

## Task 2 — RED: `#right` desktop-only presentation boundary

**Files:** `tests/library_v5/test_phase6_legacy_layer_contract.py` (new), `tests/library_v5/test_mobile_shell_contract.py` (only if an existing assertion is extended), `tests/library_v5/browser_mobile_shell_audit.mjs`.

1. まず失敗する契約を追加する（RED）。テスト名は `test_phase6_right_is_desktop_only_presentation_root` とする。
2. 390×844、844×390、760pxでは `<html data-shell="mobile">` のactive presentation rootがmobile shell／SheetHostだけで、`#right`が表示・開閉・modal ownerにならないことを確認する。
3. 761、980、981pxでは `#right` のworks/links/PATH/docked SheetHostが存在し、`#right`のPC機能を失わないことを確認する。
4. 既存の `test_mobile_right_panel_has_no_legacy_bottom_sheet_transform_path` と `test_mobile_shell_is_the_only_active_mobile_presentation_root` は再導入防止として残す。

**GREEN implementation:** 実コードが既に満たす契約は最小差分で固定する。違反が見つかった場合のみ、`data-shell`境界をowner判定の単一入口に修正し、`#right`をmobile用に操作する経路を除去する。SheetHostの `docked` 親移動（`syncSheetPresentation()`）は保持する。

**Verification:** focused unit、`MARVEL_BROWSER_MOBILE_SHELL_AUDIT=1` の代表viewport、既存interaction audit。active root count、`#right`のvisibility/pointer-events、SheetHost parent/presentationをJSONで比較する。

## Task 3 — RED: `#detail` is goal summary only

**Files:** `tests/library_v5/test_phase6_legacy_layer_contract.py`, `tests/library_v5/browser_mobile_shell_audit.mjs` or a new focused browser scenario.

1. `#detail`の全writer（特に `renderDetail()`、`openDockedInspection()`、`closeDockedInspection()`周辺）を関数名と書き込み内容で固定する。
2. `test_phase6_detail_is_goal_summary_only` を追加する（RED）。goal summary以外のinspection/detail/reason/settings本文が `#detail`に書かれず、SheetHostだけが表示ownerであることを検査する。
3. 実操作で「作品Aを開く → reason/settings → close → A」を行い、SheetHost/legacy mirrorのvisibility、focus、scroll lock、selected IDs、goal order/current goalを記録する。

**GREEN implementation:** `#detail`にgoal summary以外を書いている到達可能writerがあれば、SheetHost rendererへ一本化する。mirrorがgoal summary用途で必要な場合はその属性と理由を `ACTIVE_ADAPTER` コメント／仕様に明記し、削除しない。

**Stop:** writerがhistory hydration、goal mutation、PC detail fallbackのいずれかに依存していた場合は削除せず、監査結果だけを計画のdebtとして記録する。

## Task 4 — Reachability audit and removable-cluster selection

**Files:** `index.html`, `tests/library_v5/test_phase6_legacy_layer_contract.py`, optionally `tests/library_v5/browser_phase6_ownership_audit.mjs`.

1. 初期ロード、`syncShellPresentation`、history hydration/popstate、surface mount、orientation／`matchMedia` listenerから各候補への入口を静的に追跡する。
2. browser auditで候補のDOM Mutation、computed style、active root、history write、chart rebuild/fitViewを計測する。
3. 候補は「同じownerのCSS＋DOM＋handler」単位に限定する。候補例は、実到達不能と証明できた旧overlay／旧close handler、重複する非表示DOM fragment、現行shellから呼ばれないCSS selector。ただし `.mobile-sheet-*` はPC/dockedでも共有されるため名前だけで候補化しない。
4. 候補ごとに削除前スナップショット、削除後スナップショット、rollback条件を記録する。

**Gate:** 入口なし、正本stateのread/writeなし、computed style差分なし、全shellでvisibility差分なし、browser auditの状態差分ゼロの5条件を満たさない候補はKEEP/`ACTIVE_ADAPTER`に戻す。

## Task 5 — Remove one approved cluster at a time (TDD loop)

For each approved cluster:

1. RED testで、そのクラスタの不要性と「保持すべき所有者」を表す。
2. CSS、DOM fragment、handlerを同一commitで最小削除する。canonical data、selection/goal/plan engines、renderer、SheetHost facadeを変更しない。
3. focused unit＋focused browser auditをGREENにする。
4. diffをクラスタ単位でレビューし、別クラスタを同じcommitに混ぜない。
5. 失敗時はクラスタだけを戻し、root baselineとの差分を保存する。

削除対象が一つも安全に証明できない場合、Phase 6は契約監査と `ACTIVE_ADAPTER` 文書化までで完了とし、無理にコード量を減らさない。

## Task 6 — Phase 6 ownership browser audit

**Files:** `tests/library_v5/browser_phase6_ownership_audit.mjs` (new), `tests/library_v5/test_browser_phase6_ownership_audit.py` (new), `.github/workflows/library-v5-ci.yml`.

Add one bounded Chrome/CDP scenario that records before/after deltas for:

- mobile/compact/desktop active presentation root count and computed visibility;
- SheetHost, overlay, backdrop count, parent, owner, focus, inert and scroll lock;
- `#right` and `#detail` MutationObserver events;
- history `pushState`/`replaceState` deltas;
- chart rebuild/fitView counters;
- selected IDs, goal order/current goal, preparation tier, active panel, camera;
- chart → search → plan, plan → chart, reason/settings open/close, Back/Forward, desktop → mobile → desktop, and 761/980/981 boundaries.

**RED→GREEN:** add the scenario and CI declaration first; then make only the minimal implementation/removal needed for the contract. The audit must fail on duplicate active owners or state deltas, not merely on string counts.

## Task 7 — Full verification and integration handoff

Run from the worktree root using the bundled runtime:

```powershell
$MarvelPython='C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
$env:MARVEL_BROWSER_AUDIT='1'; & $MarvelPython -m unittest tests.library_v5.test_browser_selection_audit.BrowserSelectionAuditTests.test_headless_dom_matches_python_oracle_for_both_public_tiers -v
$env:MARVEL_BROWSER_INTERACTION_AUDIT='1'; & $MarvelPython -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_headless_interactions_preserve_selection_contract -v
```

Also run chronology, publication-order, mobile-shell and the new Phase 6 ownership audit with their existing environment gates. Inspect generated outputs and remove only known transient paths. Confirm canonical CSV/review ledgers unchanged, SQLite integrity, CI required checks, Pages deployment, and public HTTP 200.

## PR and completion boundary

Prefer PRs in this order: (1) RED ownership contracts, (2) one or more independently proven removal clusters, (3) ownership browser audit/CI and docs. Do not merge a removal cluster whose audit is not independently GREEN. Final completion means unique display owners, proven unreachable code removed (or explicitly retained as `ACTIVE_ADAPTER`), existing semantic/UI behavior unchanged, full CI GREEN, and Pages/public behavior verified. `index.html` splitting and DOM-independent search predicate extraction remain later plans.
