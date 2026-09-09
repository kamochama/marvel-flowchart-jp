# Marvel UI Single Sheet Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 表示ビュー選択・作品詳細・接続理由・設定を唯一のSheetHostへ統合し、PCのdocked表示とモバイルのmodal表示で、既存のゴール・点灯・URL・履歴を維持する。

**Architecture:** `createMobileUiStore`のoverlayを唯一の明示シート状態とし、既存の`sheet`/`sheetWork`は互換投影にする。SheetHostはこのoverlayと`marvelLegacyUiBridge`のinspectionを読み、既存の`marvelEffectiveSheetContent`で表示内容を決める。作品情報、理由、設定は同じDOMへ描画し、履歴操作は既存のpolicy writerとpopstate guardへ集約する。

**Tech Stack:** 単一の静的`index.html`、既存の`flowchart.json`、Browser History/Pointer/Focus API、Python unittest、Node VM、Chrome/CDP。

**Spec:** `docs/superpowers/specs/2026-09-09-marvel-pc-mobile-ui-architecture-design.md` §§6.1, 9, 10, 11, 13 Phase 3。直前の履歴基準は`docs/superpowers/plans/2026-09-10-marvel-ui-history-scroll-snapshot.md`（PR #83）。

## Global Constraints

- 調査基準HEADは`db6e4879b4174824487d69e0a969d64d2f4401e0`（PR #83）。実装開始時に`git fetch origin`とHEAD比較を再実施し、新しいremoteとの差分を調停する。古い文書のSHAへコードを戻さない。
- この計画はUI統合設計のPhase 3であり、Events & MultiverseのPhase 2とは別である。
- `data/library/`、`data/content_audit/reviews.csv`、永続レビュー履歴、作品・人物・関係ID、export schemaを変更しない。
- 関係グラフ、世界線、時系列、点灯集合、予習計算、人物同一性を変更しない。公開順の合成関係線は引き続き0。
- 公開プランは`site-proposal`と`complete`の2つ。内部公式ルートデータを公開selectorへ出さない。
- 現行v5.18の操作契約を維持する。PCの作品クリックはinspection、モバイルのチャートタップは既存のgoal/connection selectionである。古い設計文書にあるモバイルタップ意味論の変更をこのPhaseへ混ぜない。inspectionだけでmodalは開かない。
- `overlay=closed, inspection=A`のPCではdetail Aを表示する。明示overlayが優先し、それを閉じてもinspectionとgoalsを保持する。inspection由来のdocked detailだけを閉じた場合は`clearInspection`を実行する。
- シートのopen/target change/closeだけで`render()`、`fitView()`、SVG生成、Canvas cache再構築を呼ばない。明示したpanel変更は既存`activatePanel`経路を使う。
- `popstate`およびそれに付随するfocus/scroll復元中の`pushState`/`replaceState`は0。PR #83の`panelId`/`prepTier`/`scrollX`/`scrollY`を保持し、初期ロードでは古いscroll snapshotを復元しない。
- 未知のquery、既存`#room=...`、視聴済みlocalStorage、静的Pages、所定ZIP構成を維持する。
- Phase 4の検索/予習全体の更新設計、Phase 5の全shell判定置換、Phase 6の広範な旧コード撤去・ファイル分割は対象外。単一Sheetを成立させる旧シート撤去だけは本Phaseに含む。
- Shell全面移行前は現行`mobileChartMotion.matches`をpresentation判定に用い、同じ端末で既存shellとSheetだけが別判定になる状態を作らない。`<=760px`はmodal、その他はdocked。`marvelClassifyShell`のcoarse/横向き規則を全UIへ適用する作業はPhase 5に残す。

## File Map

| ファイル | 責務と変更範囲 |
| --- | --- |
| `index.html` | Store overlay、URL codec、共通Sheet DOM、render/controller、PC detail adapter、modal lifecycle、設定・理由入口、44px修正 |
| `tests/library_v5/test_ui_architecture_contract.py` | 純粋なoverlay正規化・URL・effective content・履歴policyのNode VM検証 |
| `tests/library_v5/test_mobile_shell_contract.py` | 所有者、URL、history/scroll、旧関数adapter、チャート非再構築契約 |
| `tests/library_v5/test_mobile_ux_contract.py` | 唯一のdialog、起点復帰、pointer sequence、44px、PC非modal契約 |
| `tests/library_v5/browser_mobile_shell_audit.mjs` | 既存全シナリオを維持し、単一Sheetの実操作・focus・scroll・履歴・PC presentationを追加 |
| `tests/library_v5/test_browser_mobile_shell_audit.py` | 追加したJSON監査結果を必須化し、未実行をPASSとして受け付けない |
| `tests/library_v5/browser_chronology_audit.mjs` | 旧`#mobileAreaSheet`を使う表示選択操作だけを新hostへ移す |
| `tests/library_v5/browser_interaction_audit.mjs`, `browser_publication_order_audit.mjs` | 必要時にdetail表示のselectorだけを移行。既存点灯・panel・public order期待値は維持 |

行番号は調査時の目安。`index.html`のCSS 603–696、旧DOM 875–919/4381、store 5551、mobile lifecycle 8067–8840、area menu 8920–8949/9654–9675、facade 9820–9948、PC detail 9998–10198を起点に関数名で検索する。

## URL and State Contract

```javascript
// 正本はstore.overlayのみ。sheet/sheetWorkはgetState()で導く互換値。
// detailのworkId、reasonのrelationIdをselectedIdへ流用しない。
overlay = {kind:'closed'}
  // または {kind:'detail', workId}
  // または {kind:'reason', relationId, sourceId, targetId}
  // または {kind:'settings', section:'display'|'plan'|'legend'}
```

| URL key | 読み書き規則 |
| --- | --- |
| `mview`, `goals`, `q`, `mfilter` | 現在の意味とcodecを維持 |
| `sheet` | `detail`/`reason`/`settings`。closedなら削除 |
| `sheetWork` | detailの既存work ID。reason旧リンクはcanonical relation IDと厳密一致する場合のみ互換読取 |
| `sheetRelation` | 新規。reasonのcanonical `relation_id`。新規reason URLの正本 |
| `sheetSection` | 新規。settingsの`display`/`plan`/`legend`。欠落・未知は`display` |

他kindへ変更したら無関係なsheetキーを削除する。reasonの端点はURLへ追加せずexportから導く。URLにcamera/scrollを追加しない。tier/panelの全面的な共有URL化はこのPhaseで導入しない。旧`sheet=reason&sheetWork=<work id>`から近隣関係を推測してはならず、解決不能ならclosed。history内の端点がcanonical relationと不一致でもclosed。データ読込完了前は検証・URL正規化を待ち、正しい直接リンクを未読込理由で削除しない。

## Tasks

### Task 1: overlay正本と検証可能なURL codecを導入する

**Files:** `index.html`, `tests/library_v5/test_ui_architecture_contract.py`, `tests/library_v5/test_mobile_shell_contract.py`。

**Interfaces:** `marvelResolveSheetOverlay(value, repository)`、`marvelReadSheetParams(params, repository)`、`marvelWriteSheetParams(params, overlay)`をfacadeへ追加する。repositoryは`{hasWork(id), getRelation(id)}`。getRelationは既存`reasonsById`の`relation_id`を検索し、端点が一意である場合に`{relationId, sourceId, targetId, reasons}`を返す。それ以外はnull。Storeは`setOverlay(overlay)`を公開し、`setSheet(kind,target)`は同APIへの一方向adapterとする。

- [ ] **Step 1: REDを追加する。** 既存`_run_node`で次を実行し、不明ID・不一致端点・旧reasonリンク・他kindへの変更によるキー削除もassertする。

```javascript
const repository = {
  hasWork: id => ['A','B'].includes(id),
  getRelation: id => id==='R' ? {relationId:'R',sourceId:'A',targetId:'B',reasons:[]} : null,
};
return {
  valid:window.marvelResolveSheetOverlay({kind:'reason',relationId:'R'},repository),
  invalid:window.marvelResolveSheetOverlay({kind:'reason',relationId:'R',sourceId:'B'},repository),
  detail:window.marvelResolveSheetOverlay({kind:'detail',workId:'missing'},repository),
};
// valid={kind:'reason',relationId:'R',sourceId:'A',targetId:'B'}
// invalid=detail={kind:'closed'}
```

- [ ] **Step 2: focused testを実行して、新API未実装による失敗を確認する。**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_ui_architecture_contract tests.library_v5.test_mobile_shell_contract -v
```

- [ ] **Step 3: 最小実装。** Storeの保存値をoverlayに移し、既存購読者へは`sheet=overlay.kind`、detail時だけ`sheetWork=workId`を返す。reason/settingsの呼出箇所はoverlay全体を使う。`readMobileUrlState`/writerは上表のcodecへ委譲し、`mobileUi` snapshotにはoverlayを保存する。独立したSheet storeは作らない。

```javascript
function sheetCompatibility(overlay) {
  return {sheet:overlay.kind, sheetWork:overlay.kind==='detail'?overlay.workId:null};
}
// publishの同値判定はkindだけでなくworkId/relationId/sourceId/targetId/sectionを比較。
// getStateはoverlayのcopyと互換投影を返し、呼出元による内部state変更を防ぐ。
```

- [ ] **Step 4: GREENとdiff監査。** focused testsを再実行する。`sheet=detail&sheetWork=...`の既存リンク、未知query、hashを往復して保存を確認し、canonical/export差分が空であることを確認する。
- [ ] **Step 5: コミット。** 上記3ファイルだけをstageし、`git commit -m "refactor: unify sheet overlay state and URL adapters"`。

### Task 2: detail/reason/settingsの実内容を同じrendererへ集める

**Files:** `index.html`, `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/test_mobile_ux_contract.py`。

**Interfaces:** `renderSheetContent(overlay)`が`#sheetHostBody`だけを更新する。`sheetWorkDetailHtml(workId)`は既存`mobileWorkDetailHtml`とPCの`marvelRenderFocusedDetail`の情報を統合する。`sheetReasonHtml(relation)`はTask 1 repositoryの結果を描画する。`sheetSettingsHtml(section)`は既存panel/tier/combine/legendの状態を読む。

- [ ] **Step 1: RED。** source契約でreasonが`relation_id`/`source_work_id`/`target_work_id`を使うこと、detailが`nm`/`WORK_DETAILS`/公式ソースを使うことを確認する。settingsの公開tier集合が正確に2件であることをassertする。現在の「情報を表示します」だけのreason/settingsでは失敗させる。

```python
def test_sheet_reason_uses_existing_relation_evidence(self):
    body = function_body(self.source, "sheetReasonHtml")
    for token in ("relationId", "sourceId", "targetId", "reasons", "notes"):
        self.assertIn(token, body)
    self.assertNotIn("ancestors(", body)
    self.assertNotIn("chronology", body)
```

- [ ] **Step 2: RED確認。** `& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_mobile_ux_contract -v`。
- [ ] **Step 3: 最小実装。** detailには邦題・英題・公開情報・あらすじ・map role・既存前後候補・公式ソース・明示ゴール操作・チャート移動を残す。reasonにはcanonical relationと対応する既存notes/verificationを表示する。`relation_id`のないderived reasonは既存接続一覧へ残し、架空のrelation IDを割り当てない。

```javascript
function sheetReasonHtml(relation) {
  return `<article data-sheet-relation="${esc(relation.relationId)}">
    <h3>${esc(nm[relation.sourceId].title)} → ${esc(nm[relation.targetId].title)}</h3>
    <ul>${relation.reasons.map(row=>`<li>${esc(row.notes||row.reason_kind)}
      <span>${esc(row.verification_statuses||'未確認')}</span></li>`).join('')}</ul>
  </article>`;
}
// relation IDはdata属性/監査用。利用者向け本文に実装用IDの羅列を追加しない。
```

detail内A→Bはoverlayのみ更新して`overlay-target-change`をreplaceする。ゴールの追加/解除は`marvelUiCommands.addGoal/removeGoal`を使い、sheet対象・inspectionから勝手にgoalを作らない。チャート移動は既存navigation APIへの明示操作として分離する。settingsは`data-mobile-target`を持つ表示選択、公開tier、既存OR/AND/PATH操作、凡例を同じhostへ描画する。

- [ ] **Step 4: GREENと監査。** focused testsを実行。HTML値を`esc`でescapeし、登録のない説明や根拠を補作していないこと、既存source URLだけを使うことをdiffで確認する。
- [ ] **Step 5: コミット。** `git commit -m "feat: render shared sheet detail reasons and settings"`（対象3ファイルを明示stage）。

### Task 3: 唯一のSheet DOMとPC docked表示へ移行する

**Files:** `index.html`, `tests/library_v5/test_ui_architecture_contract.py`, `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/test_mobile_ux_contract.py`。

**Interfaces:** `window.marvelSheetHost={open(overlay),close(options),render(),getSnapshot()}`。getSnapshotは`{overlay,effective,presentation}`のcopy。`openMobileSheet`/`closeMobileSheet`/`openMobileAreaMenu`/`closeMobileAreaMenu`はこのhostへ委譲する互換入口に限定する。

- [ ] **Step 1: RED。** facadeの既存effective-content契約を実DOMへ接続するため、単一`sheetHost`、旧host不存在、docked属性分離をassertする。

```python
def test_sheet_has_one_dom_owner(self):
    self.assertEqual(self.source.count('id="sheetHost"'), 1)
    self.assertEqual(self.source.count('id="sheetHostBody"'), 1)
    self.assertNotIn('id="mobileAreaSheet"', self.source)
    self.assertNotIn('id="mobileSheet"', self.source)
```

- [ ] **Step 2: RED確認。** Tasks 1–2のfocused 3モジュールを実行し、旧hostが残るため失敗することを確認する。
- [ ] **Step 3: 最小DOM移行。** body直下にmobile用portal slot、PC右ペインにdocked slotを設け、同じ`#sheetHost`要素をmoveする。cloneしない。`#detail`は単一host内のdetail articleとして維持し、既存browser selectorの意味を残す。

```html
<section id="sheetHost" data-presentation="docked" hidden>
  <div id="sheetHostBackdrop" aria-hidden="true"></div>
  <div id="sheetHostPanel" aria-labelledby="sheetHostTitle" tabindex="-1">
    <header><h2 id="sheetHostTitle" tabindex="-1">作品情報</h2>
      <button id="sheetHostClose" type="button">閉じる</button></header>
    <div id="sheetHostBody"></div>
  </div>
</section>
```

`marvelEffectiveSheetContent({...marvelUiCommands.readSelection(),overlay},presentation)`を唯一の表示判定にする。旧`mobileAreaOpen`/旧focus trap/旧backdrop handlerと旧2シートDOMを撤去する。`mobileAreaButton`の`aria-controls`を`sheetHostPanel`へ変更し、settings/display表示中だけexpandedにする。

PCの`marvelRenderFocusedDetail`、`resetPanels`、selection更新中の`detail.innerHTML/textContent`書込みはhostへのrender要求に移す。`rg -n 'detail\.(innerHTML|textContent)' index.html`で全書込みを点検し、旧goal redrawが明示reason/settingsを上書きしないことを確認する。接続一覧/作品一覧/予習ワークスペースの独立機能は残すが、別detail ownerは残さない。docked closeはeffective contentの由来に応じてoverlay closeか`clearInspection`を選ぶ。

- [ ] **Step 4: GREENと監査。** PC inspection A→settings→closeでAへ戻り、inspection由来detail closeではgoalsを保持することを確認。既存sourceテストの「mobileAppShell内にmobileSheet」やarea専用focus owner期待は、削除ではなく新host単一所有契約へ置き換える。
- [ ] **Step 5: コミット。** `git commit -m "refactor: mount one sheet host for desktop and mobile"`。

### Task 4: modal pointer/focus/inert/scroll lifecycleを実装する

**Files:** `index.html`, `tests/library_v5/test_mobile_ux_contract.py`, `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/browser_mobile_shell_audit.mjs`。

**Interfaces:** `enterSheetModal()`、`leaveSheetModal({restoreFocus})`、`restoreSheetFocus(origin)`。一度のopenからcloseまで起点と背景scrollを保持し、detail A→Bで起点を上書きしない。

- [ ] **Step 1: RED。** 実操作のcaseを追加する。backdrop→backdropだけ閉じ、panel→backdrop、backdrop→panel、pointercancelでは開いたまま。close後もgoals/inspection/cameraは同じ。modalのTab/Shift+Tabが内部を循環し、dockedでは外へ移れることをassertする。
- [ ] **Step 2: RED確認。** 下記browser auditを実行し、旧click方式・inert/scroll lock不在で新caseが失敗することを記録する。

```powershell
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT='1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
```

- [ ] **Step 3: 最小実装。** pointer IDと開始targetを保持する。通常clickでbackdrop dismissしない。

```javascript
let backdropPointerId=null;
backdrop.addEventListener('pointerdown',event=>{
  backdropPointerId=event.target===backdrop?event.pointerId:null;
  event.stopPropagation();
});
backdrop.addEventListener('pointerup',event=>{
  const close=event.target===backdrop&&backdropPointerId===event.pointerId;
  backdropPointerId=null;event.preventDefault();event.stopPropagation();
  if(close)window.marvelSheetHost.close();
});
backdrop.addEventListener('pointercancel',()=>{backdropPointerId=null;});
// panel起点のpointerdownでも記録をclearする。document上のpointerupで
// backdrop以外へのreleaseをclearする。close後のclickも背後chartへ伝播させない。
```

modalのみpanelへ`role=dialog`/`aria-modal=true`を付与し、backdropを有効化する。portalを除くbody内のUI rootへinertを設定し、元のinert値を保存してclose時に復元する。bodyを固定する場合は元のstyleとscroll位置を保存し、Sheet bodyだけが縦scrollを所有する。ロック中のdocument scroll snapshotは元の背景座標を読む。Sheet body scrollはPR #83のdocument capture listenerから除外する。

scroll lock解除/`scrollTo`/focus復帰は既存scroll restore depthの抑制期間内で行い、遅延scroll eventでpopstate先へreplaceしない。pending callbackへ世代番号を付け、close直後の再openで古いfocus/scroll処理が新状態を上書きしないようにする。focus復帰は接続済みの元button→同workのcard内操作→現在surface見出しの順。fallback見出しへ`tabindex=-1`を付け、`preventScroll:true`でfocusする。

dockedでは`role=region`、aria-modalなし、backdrop hidden、inertなし、body lockなし、Tab trapなし。modal↔dockedで同じoverlay/DOM/対象を維持し、副作用だけを解除/付与する。Escapeは一箇所で処理し、hidden hostはキーを奪わない。

- [ ] **Step 4: GREENとChrome/CDP監査。** Step 2を再実行し、non-zero背景scroll、Sheet内部scroll、Back/Forward後のhistory log 0、再open競合、消えた起点のfallbackを確認する。
- [ ] **Step 5: コミット。** `git commit -m "fix: enforce single sheet modal input and focus lifecycle"`。

### Task 5: 表示選択と履歴closeを統合し、44pxを満たす

**Files:** `index.html`, `tests/library_v5/test_mobile_shell_contract.py`, `tests/library_v5/test_mobile_ux_contract.py`, `tests/library_v5/browser_mobile_shell_audit.mjs`。

**Interfaces:** `commitSheetDisplay(target)`は設定内の明示選択確定。`close`（dismiss）とは別操作とする。`openMobileAreaMenu()`は`open({kind:'settings',section:'display'})`へ委譲。

- [ ] **Step 1: RED。** `closed→detail A→detail B`はpush 1回＋replace、Bからcloseは親entryへBack。直接detailリンクcloseはreplace。detail→reason→closeは親detailを復元。display選択確定後に選んだpanelが残ること、hash/未知query/背景goalsが変わらないことをbrowser assertionsへ追加する。さらに`site-proposal→settings→completeへ変更→dismiss`後も`complete`を保持すること、設定を閉じただけで`prepTier`を親snapshotへ巻き戻さないことをassertする。
- [ ] **Step 2: RED確認。** focused testsとmobile browser auditを実行し、履歴追加数・対象復元・実測解除buttonの不足を記録する。
- [ ] **Step 3: 最小実装。** open時に`entryId`/`parentEntryId`/`sheetOwner`と起点を記録。dismissで`history.back()`するのは現在entryが自分のapp overlay entryで、記録済みparentEntryIdも一致する場合だけ。直接リンク・不明な親はclosedへreplace。連打のBackはpending guardで1回にする。popstateは対象entry全体をguard内hydrateし、URLを書き直さない。

```javascript
// 現在entryとopen時記録の両方を照合する。
const canGoBack = owner==='app' && navigation.entryId===openedEntryId &&
  navigation.parentEntryId===openedParentEntryId && !!openedParentEntryId && !backPending;
// detail A→Bはoverlayだけ変更。surface/goals/inspection/current goalは保存。
```

表示選択確定は「設定を閉じて選んだ表示へ移る」一つのcommandとして処理する。通常dismissの`history.back()`を使うと親panelが復元されるため、同一surfaceのpanel選択はcurrent entryをclosed＋選択panelへreplaceし、surfaceを変える`watch`選択は既存surface-transitionとしてpushする。`activatePanel`の副次writerをtransactionで抑止し、command完了後に1回だけ書く。単なる設定open/closeではsurfaceを変えない。tier/combine変更は設定を開いたまま既存APIで適用し、意図的な設定確定として扱う。設定をdismissで閉じても変更後のtier/combineを保持し、Back/Forwardによる設定履歴の復元は別契約として監査する。

`.mobile-plan-goal-remove`の38pxを`min-width:44px;min-height:44px`へ変更。Sheetのbutton/select/summary/リンク操作も可視hit areaが44×44以上になるCSSにし、detail/plan双方の解除操作を測る。長い作品名で横overflowを作らない。

- [ ] **Step 4: GREENと監査。** 390×844で実測hit area、表示選択後のpanel、`site-proposal→complete→dismiss`後のtier保持、Back/Forward、直接URL、親detail復帰、未知query/hash保存を確認。全閉じ方でgoals/inspection/current goalを予期せず変更していないことを比較する。
- [ ] **Step 5: コミット。** `git commit -m "feat: unify display settings navigation and sheet history"`。

### Task 6: Chrome/CDP監査を単一Sheetへ更新する

**Files:** `tests/library_v5/browser_mobile_shell_audit.mjs`, `tests/library_v5/test_browser_mobile_shell_audit.py`, `tests/library_v5/browser_chronology_audit.mjs`, 必要時のPC browser selector。

**Interfaces:** 既存reportの`sheet`へ`singleOwner`, `realContents`, `pointerSequences`, `modalFocus`, `dockedFocus`, `scrollLock`, `focusReturn`, `urlRoundTrip`, `responsiveIdentity`, `touchTargets`を追加する。各値は未実行時falseとし、全項目trueが合格条件。

- [ ] **Step 1: RED。** Python report validatorに追加フィールドの必須/true検証を追加し、欠落とfalseのfixtureが拒否されるテストを作る。既存`audit-relation`架空IDのopen成功期待は、export内の実`relation_id`を選ぶ試験と未知ID closed試験へ置き換える。

```python
def test_wrapper_rejects_unexecuted_sheet_case(self):
    report = _successful_report()
    report["sheet"]["pointerSequences"] = False
    with self.assertRaisesRegex(AssertionError, "pointerSequences"):
        _validate_report(report)
```

- [ ] **Step 2: RED確認。** `& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit -v`。まだreport項目未実装の失敗を確認する。
- [ ] **Step 3: 最小監査実装。** 既存CDP/static server/Chrome retryを再利用する。open・close・設定・理由は可視buttonへのpointer/keyboardで操作し、window内部関数を呼んだだけで操作成功にしない。履歴観測とfixture選択にはpageEvaluateを使ってよい。

| 実操作シナリオ | 必須観測 |
| --- | --- |
| 390×844で表示→detail→reason→settings | 可視modal 1、host identity不変、実内容、背後surface/goals保持 |
| detail A→B、Back/Forward、直接URL | 対象・entry・history書込み数、invalid relation closed |
| pointerの4組合せ＋cancel | backdrop両端だけclose、chart selectionへ伝播0 |
| Tab/Shift+Tab/Escape | modal trap、close、元button/card/見出しfocus復帰 |
| non-zero背景scroll→open→Sheet scroll→close | 背景固定、Sheetだけscroll、位置復帰、popstate書込み0 |
| PC inspection A→reason/settings→dismiss | 明示overlay優先、close後inspection detail、goals不変 |
| dockedでTabと背景操作 | aria-modal/backdrop/inert/scroll lockなし、外へfocus可能 |
| 760→761→980→981→390 | hostをcloneせずpresentation切替、overlayと対象を保持 |
| 844×390とkeyboardによる高さ変化 | 現行shellとSheet判定の一致。Phase 5の将来規則達成とは報告しない |
| detail open/target change/close | render/fitView/SVG/Canvas cache再生成の増分0、camera不変 |
| 全ての追加操作とplan解除 | 可視hit area 44×44以上、文字被り/横overflowなし |

旧`#mobileSheet*`/`#mobileAreaSheet` selectorsを新hostへ更新し、既存search・plan・panel/tier/scroll・selectionシナリオを残す。chronology runnerのarea selectorも更新する。PC `#detail`は単一host内で維持し、もしselector更新が必要なら期待する作品名・点灯集合を変更しない。

- [ ] **Step 4: GREENとChrome監査。** Python wrapperと実mobile auditを再実行する。追加caseがreportに全て存在しtrue、既存`failures=[]`であることを確認する。semantic assertionをretry対象にしない。
- [ ] **Step 5: コミット。** `git commit -m "test: audit shared sheet lifecycle across presentations"`。

### Task 7: full verificationとPR引渡しを行う

**Files:** 実装diff全体、必要な実行記録のみ。canonical/review変更禁止。

- [ ] **Step 1: diffと退行契約を確認する。**

```powershell
git diff --check
git diff origin/main --stat
git diff origin/main -- data/library data/content_audit/reviews.csv
rg -n 'mobileAreaOpen|mobileAreaReturnFocus|id="mobileAreaSheet"|id="mobileSheet"' index.html
```

canonical/review差分と旧2シート所有者は0。既存sourceテストの更新箇所は旧DOM前提の置換であり、ゴール/点灯/履歴の失敗を消していないことを別のread-only reviewerに確認する。

- [ ] **Step 2: full suiteとbuild。**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw 'Bundled Python runtime missing' }
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

unit PASS、audit/content-audit/review-integrity issues 0、FK rows 0、SQLite integrity ok、既存story paths再現を確認する。テスト数は実行時の値を記録し、古い件数を達成目標にしない。

- [ ] **Step 3: 全Chrome/CDP監査。** Chromeが未検出なら実在を確認した絶対パスを`MARVEL_CHROME_BIN`へ設定する。以下はrepo rootから実行する。

```powershell
$env:MARVEL_BROWSER_AUDIT='1'
& $MarvelPython -m unittest tests.library_v5.test_browser_selection_audit.BrowserSelectionAuditTests.test_headless_dom_matches_python_oracle_for_both_public_tiers -v
$env:MARVEL_BROWSER_INTERACTION_AUDIT='1'
& $MarvelPython -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_headless_interactions_preserve_selection_contract -v
$env:MARVEL_BROWSER_CHRONOLOGY_AUDIT='1'
& $MarvelPython -m unittest tests.library_v5.test_browser_chronology_audit.BrowserChronologyAuditTests.test_headless_chronology_contract -v
$env:MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT='1'
& $MarvelPython -m unittest tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_headless_publication_order_contract -v
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT='1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
```

131作品×公開2tierのexact-set mismatch 0、PC操作・chronology・publication-order・mobile/Sheet failures 0を要求する。timeoutならログで環境失敗とsemantic失敗を分ける。検証を弱めない。必要時は既存CI全6jobを最終実行面にする。

- [ ] **Step 4: 生成物と監査記録を確認する。** buildによるcanonical変更0とdeterminismをCIで確認する。生成物を掃除する場合は`git status`で特定し、実装前からあったファイルを保護する。recursive削除前に各absolute pathがworktree配下の既知generated pathであることを検証する。`.codex-remote-attachments/`を削除しない。
- [ ] **Step 5: 引渡しとコミット。** 実装結果、RED/GREEN、全監査、URL追加2キー、現行モバイルタップ維持、Phase 4/5/6の残境界を計画の実行記録へ記載し、`git commit -m "docs: record single sheet verification boundary"`。通常feature branch/PR経路を使い、AGENTS.mdのstanding authorizationが有効な範囲で進める。main直接commit・force pushは禁止。mergeする場合はreview/CIを通し、main HEADとPages/public behaviorを別途確認してhandoff/roadmapへ本番基準を記録する。

## Planning Evidence and Handoff

本計画の作成ではコード・canonical CSV・review ledgerを変更していない。調査HEADと記録済みorigin/mainはともに`db6e4879b4174824487d69e0a969d64d2f4401e0`。計画用worktreeのfetchは`FETCH_HEAD: Permission denied`で実行できなかったため、実装者はfresh fetchを再確認すること。計画作成時のfocused検証は`test_ui_architecture_contract`、`test_mobile_shell_contract`、`test_mobile_ux_contract`の77 tests PASS。これは現行baselineの確認であり、上記Phase 3の実装完了やChrome監査完了を意味しない。
