# Task 4 report: モバイル公開順の合成関係線を禁止

実施日: 2026-09-03

## 実装

- `mobileOverlaySyntheticSpecs` の既存 guard を再利用した。active SVG の `cs.svg?.dataset?.relationshipEdges` と panel id を境界で確認し、`release` または `relationshipEdges === "off"` の場合は合成 relation spec を空配列にする。
- chronology の明示的な `overlayChronologyEdgePrimitives` 描画経路は変更していない。したがって chronology overlay の点灯契約を無効化せず、relation 合成線だけを禁止する。
- browser interaction audit の snapshot に `window.marvelCanvasAudit().overlaySyntheticDrawn` を追加し、release round-trip の選択後に `overlaySyntheticDrawn === 0` を待機条件として検証する。
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

## Concerns

- 既存の mobile guard が要件を満たしていたため `index.html` の guard は重複変更していない。Task 5 の独立した公開順 PC／モバイル audit は未実装・未実行で、引き続き後続タスクの範囲である。
- `git fetch origin` は linked worktree の `.git/worktrees/publication-order-display-contract/FETCH_HEAD` に対する `Permission denied` で失敗した。ローカル HEAD `d955ea0` と `origin/main` `5e159c4` を確認し、チェックアウトの上書きや reset は行っていない。
