# Phase 6 旧表示層の所有権ベース撤去 — Design Spec

**Date:** 2026-09-12  
**Status:** Proposed after ordinary ChatGPT repository review  
**Scope:** Viewer-only presentation cleanup after Phase 5 shell stabilization

## Decision

採用するのは、旧層を名前ではなく「表示所有権」と「実到達可能性」で判定する保守的段階撤去である。`#right`、検索同期、`legacyDetail`を見た目が古いという理由だけで削除しない。各削除クラスタのRED契約を先に追加し、共有状態・描画・意味論に依存しないことを確認できたCSS、DOM fragment、handlerだけを撤去する。

大規模な`index.html`分割はPhase 6の後へ延期する。互換層は一律に温存せず、実際に到達可能なadapterだけを`ACTIVE_ADAPTER`として理由付きで残す。

## Goals

- モバイルの表示所有者を`#mobileAppShell`、`#mobileViewHost`、`#mobileBottomNav`、`#sheetHost`に限定する。
- compact/desktopでは`main`／`#right`のPC表示、作品一覧、Links/PATH、docked SheetHostを維持する。
- inspection/detail/reason/settingsのsheet内容はSheetHostを正本にし、`#detail`はgoal summary用途を越えて競合しないことを固定する。
- 旧bottom-sheet transform、重複overlay、到達不能handlerの再導入をテストで防ぐ。
- 選択、ゴール順序、current goal、予習tier、camera、active panel、history、filter意味論、graph/dataを変更しない。

## Non-goals

- `index.html`の大規模分割、モジュール化、ビルド方式変更。
- `official_prewatch_routes`、作品・人物・関係ID、canonical CSV、review ledger、graph/worldline/chronology意味論の変更。
- 共有Canvas/SVG renderer、選択・ゴール・予習計算、SheetHost facadeの再設計。
- DOM非依存filter predicateの抽出。検索adapterの撤去は別フェーズとする。

## Ownership map

| Surface | 正本／保持範囲 | Phase 6の扱い |
|---|---|---|
| Mobile app | `#mobileAppShell`, `#mobileViewHost`, `#mobileBottomNav`, `#sheetHost`, `mobileUiStore` | mobile presentation ownerとして保持 |
| Compact/Desktop | `main`, `#left`, `#right`, PC tabs/list/PATH、docked `#sheetHost` | 現役UIとして保持 |
| Sheet state | `overlay`, `inspection`, `syncSheetPresentation()`, SheetHost facade | canonical ownerとして保持 |
| Goal summary | `#detail`のgoal summary mirror | goal summaryの範囲だけ保持。sheet内容との二重所有は禁止 |
| Search semantics | `pass()`、`NODES.filter(pass)`、`#q/#branch/#character/#status`へのprojection | 現行adapterとして保持し、削除候補から除外 |
| Old mobile sheet | `body.mobile-details-open #right`、`#right`のbottom-sheet transform | 不在を再導入防止契約で固定。存在しないため削除対象にしない |

## Removal unit

削除単位は、同じownerに属するCSS、DOM fragment、event handlerをまとめたクラスタとする。1クラスタにつき1つのRED理由を置き、削除前後で次を比較する。

1. mobile/compact/desktopのactive presentation root数とvisibility。
2. SheetHost／overlay／backdropの数、owner、focus、scroll lock。
3. `inspection`、goals、selected IDs、camera、active panel、tier、history writes、chart rebuild/fitViewの差分。
4. `#detail`、`#right`、legacy mirrorへのMutationとcomputed styleの差分。

## RED contracts

最初の契約は`#right`所有権である。代表的な契約名は`test_phase6_right_is_desktop_only_presentation_root`とし、390×844、844×390、760pxでは`#right`がmobile presentation ownerにならず、761/980/981pxではPC側の現役機能を維持することを固定する。

次に`legacyDetail`を監査する。`#detail`はgoal summaryに限定し、inspection/detail/reason/settingsの実内容はSheetHostだけが表示する。detail A → reason/settings → close → A、chart → search → plan、Back/Forward、desktop → mobile → desktopを実操作で確認する。

静的契約では、削除対象クラスタが初期化、shell sync、history hydration、surface mount、orientation切替のいずれからも参照されないこと、`official_prewatch_routes`やcanonical dataがdiff対象に入らないことを確認する。既存の`body.mobile-details-open #right`および`transform:translateY(...)`不在契約は維持する。

## Error and rollback boundary

各クラスタの変更は独立commit／PRにできる粒度で行う。REDまたは実ブラウザ監査が失敗した場合、そのクラスタだけを戻し、他のクラスタやcanonical inputsを変更しない。失敗を「環境問題」と扱う前に、JSON report、DOM owner、history/camera/goal差分を保存して原因を分類する。

## Verification

Phase 5の基準を回帰ゲートとして再利用する。bundled Python full suite、deterministic build、selection、interaction、chronology、publication-order、mobile-shellの実Chrome監査を全て通す。Phase 6専用監査ではactive root数、SheetHost/overlay数、legacy root Mutation、history write delta、chart rebuild/fitView deltaを追加し、Pages deploymentと公開HTTP 200も確認する。

完了条件は「`legacy`文字列が減った」ではない。「表示所有者が一意で、到達不能コードが撤去され、残ったadapterがACTIVE_ADAPTERとして必要理由を説明でき、既存の表示・状態・意味論が同一」であることを満たすこととする。

## Intentional debt after Phase 6

- 巨大な単一`index.html`は分割せず残す。
- DOM-backed検索adapterと`#q/#branch/#character/#status`projectionは、DOM非依存predicate抽出まで残す。
- `.mobile-sheet-*`の混在命名、`#right`のPC sidebar＋docked SheetHostという二役、到達可能な古い`matchMedia`adapterは、理由を記録したACTIVE_ADAPTERとして残す。

これらは未分類のdead codeではなく、次の独立設計境界で扱う技術的負債である。
