# Task 4 report: モバイル公開順の合成関係線を禁止

実施日: 2026-09-03

## 実装

- `mobileOverlaySyntheticSpecs` の既存 guard を再利用した。active SVG の `cs.svg?.dataset?.relationshipEdges` と panel id を境界で確認し、`release` または `relationshipEdges === "off"` の場合は合成 relation spec を空配列にする。
- chronology の明示的な `overlayChronologyEdgePrimitives` 描画経路は変更していない。したがって chronology overlay の点灯契約を無効化せず、relation 合成線だけを禁止する。
- browser interaction audit の snapshot に `window.marvelCanvasAudit().overlaySyntheticDrawn` と公開選択状態を追加し、release round-trip は実 viewport 390px の mobile Canvas 経路で `active === true` / `panel === "release"` を先に確認してから、選択後に `overlaySyntheticDrawn === 0` を待機する。mobile 検証後は desktop viewport に戻して既存の release → overview 往復も実行する。
- canonical CSV、SQLite、persistent review ledger は変更していない。

## RED

wrapper 契約テストを先に追加し、実装前に次を実行した。

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -B -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_runner_proves_release_has_no_mobile_synthetic_overlay -v
```

結果: `Ran 1 test`、`FAIL`。audit runner に `overlaySyntheticDrawn` がなく、期待どおり新しい release no-synthetic 契約を観測できなかった。

## GREEN

次の focused suite は `Ran 48 tests`、`OK (skipped=1)` だった。skip は opt-in Chrome test を環境変数なしで実行したためである。

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_browser_interaction_audit tests.library_v5.test_runtime_selection_classifier -v
```

Chrome opt-in の実 interaction audit も次で確認し、`Ran 1 test ... OK`（runner 内の `summary: {cases: 6, failures: 0}`）だった。

```powershell
$env:MARVEL_BROWSER_INTERACTION_AUDIT = '1'
& $MarvelPython -B -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_headless_interactions_preserve_selection_contract -v
Remove-Item Env:MARVEL_BROWSER_INTERACTION_AUDIT
```

`git diff --check` は問題なし。

## Fix round 1（レビュー対応）

### RED

レビュー指摘を再現するため、release の実選択を mobile Canvas 経路で証明する静的契約を追加してから focused test を実行した。段階的な RED では、runner に実 viewport override と Canvas 初期化確認がなく、さらに部分実装時点では release wrapper の表示位置への `scrollIntoView` がなく、いずれも契約テストが失敗した。

### GREEN

- `Emulation.setDeviceMetricsOverride` で 390×844 / `mobile: true` を設定し、mobile area menu から release を選択する。
- `marvelCanvasAudit()` の `active === true` と `panel === "release"` を確認した後、release wrapper を表示領域へスクロールし、Canvas の実座標へ CDP mouse event を送る。
- mobile 側は Canvas の高速選択で SVG `.focus` が遅延するため、公開 `marvelSelectionAudit().selected` と `overlaySyntheticDrawn === 0` を待機する。viewport を解除してページを再読込し、元の desktop `selectRepresentative → release → overview` sequence を保持した。

次の結果を得た。

```powershell
& node tests/library_v5/browser_interaction_audit.mjs --root . --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe' --timeout-ms 12000
```

結果: runner `summary: {"cases":6,"failures":0}`。

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_browser_interaction_audit tests.library_v5.test_runtime_selection_classifier -v
```

結果: `Ran 48 tests`、`OK (skipped=1)`。

```powershell
$env:MARVEL_BROWSER_INTERACTION_AUDIT = '1'
& $MarvelPython -B -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_headless_interactions_preserve_selection_contract -v
Remove-Item Env:MARVEL_BROWSER_INTERACTION_AUDIT
```

結果: `Ran 1 test in 70.427s`、`OK`。

`git diff --check` は問題なし。変更ファイルは audit runner、audit contract test、本文書のみで、`index.html` は既存 guard が要件を満たすため重複変更していない。

## Concerns

- 既存の mobile guard が要件を満たしていたため `index.html` の guard は重複変更していない。Task 5 の独立した公開順 PC／モバイル audit は未実装・未実行で、引き続き後続タスクの範囲である。
- `git fetch origin` は linked worktree の `.git/worktrees/publication-order-display-contract/FETCH_HEAD` に対する `Permission denied` で失敗した。ローカル HEAD `d955ea0` と `origin/main` `5e159c4` を確認し、チェックアウトの上書きや reset は行っていない。
