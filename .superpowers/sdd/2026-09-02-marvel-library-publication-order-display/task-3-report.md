# Task 3 report: 共有選択状態と公開順カードのフォーカス

実施日: 2026-09-03

## 実装

- `renderSelectionState` に release panel 専用分岐を追加した。共有 `selectedIds` と `window.marvelDetailFocusId` に対応するカードだけを `focus` / `current-goal` / `goal-node` / `detail-focus` として再描画し、release SVG の `dim` と関係線・時系列線のハイライトを適用しない。
- `renderFocusHighlight` に同じ release-specific 方針を追加し、カード詳細 focus を右詳細パネルへ復元する。release のカードは日付軸のため、関係グラフの context や edge state を描画しない。
- クリックおよび PC のコンテキストメニューで `data-release-work-id` を優先して解決し、overview と同じ共有選択/detail focus 経路を利用する。`selectedIds` の release 専用変異は追加していない。
- `activatePanel` の既存の `refreshSelection(false)` / `window.marvelRenderDetailFocus(window.marvelDetailFocusId)` 復元経路を維持し、release → overview の往復で通常の関係ハイライトに戻る契約をテストした。
- canonical CSV、SQLite、persistent review ledger、および Task 4 の mobile guard は変更していない。

## RED

テストを先に追加し、実装前に次を実行した。

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -B -m unittest tests.library_v5.test_flowchart_selection_contract -v
```

結果: `Ran 41 tests`、新規の release selection/detail-focus 経路と release renderer 往復契約の `2 failures`。失敗は期待どおり、`data-release-work-id` を使うクリック経路および release 専用 renderer 分岐が未実装であることを示した。

## GREEN

実装後、以下を実行した。

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_flowchart_selection_contract -v
```

結果: `Ran 41 tests ... OK`。

関係・時系列を含む既存ブラウザ interaction 契約も確認した。

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_browser_interaction_audit -v
```

結果: `Ran 46 tests ... OK (skipped=1)`（通常実行では opt-in Chrome audit のみ skip）。Chrome を有効化した実ブラウザ監査も実行し、`test_headless_interactions_preserve_selection_contract`: `Ran 1 test ... OK`（6/6 cases、release round-trip を含む）だった。

## Diff / concerns

- `git diff --check`: 問題なし。
- 変更ファイルは `index.html` と `tests/library_v5/test_flowchart_selection_contract.py` のみ（この report は未追跡作成後に commit 対象へ追加）。
- canonical CSV、SQLite、review ledger の diff は 0。
- concern: Task 5 の公開順専用 browser audit（dated / month-only / year-only / TBD のカード直接クリックを含む）は未実装・未実行であり、後続タスクのスコープに残る。
