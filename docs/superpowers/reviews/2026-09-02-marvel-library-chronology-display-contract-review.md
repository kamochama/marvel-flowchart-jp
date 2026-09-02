# Marvel Library chronology display contract レビュー

日付: 2026-09-03

対象リポジトリ: `kamochama/marvel-flowchart-jp`

対象ブランチ: `codex/chronology-publication-order-contract`

実装対象の最終コミット: `5ff75514dccb4c2d4cae3e483c09f3ad995cfae5` (`test: add chronology browser audit contract`)

実装範囲: `10726ac..5ff7551`（Task 1–4）。Task 5 はこのレビュー、ハンドオフ、ロードマップの文書化だけを行う。

## 判定

chronology display contract は、ローカルの静的契約・ランタイム回帰・実 Chrome/CDP 監査を通過したため **PASS** とする。今回の境界は表示層の edge identity／selection materialization に限定され、chronology の表示線を relation fact や canonical chronology assertion として登録していない。

## 表示層の契約

- 各 chronology 線は `data-chronology-edge-id` に安定した表示 ID を持つ。`source`／`target` は互換性と隣接探索の端点として残すが、分類結果・SVG materialization・Canvas overlay のキーは edge ID である。同一端点の複数線も別 ID のまま保持する。
- `sequence-<source>-<target>-<lane>-<column>`、`branch-<source>-<target>-<row>`、crossing／merge の明示 ID を使い、`order` だけから ID を推測しない。
- `displayOnly:true` と `traversable:false` を表示専用の組合せとして固定し、`displayOnly && traversable` は生成時に拒否する。表示専用の Morbius sequence 2 本と Deadpool→Logan branch 1 本（計 3 本）は表示されるが、隣接・分類・点灯対象へ入らない。
- chronology display lines は work relation ではない。共有 continuity、表示順、crossing の depiction だけから新しい work-to-work relation を作らない。

## 公開5モード＋内部 previous1 の edge-ID semantics

`classifyChronologySelection` は adjacency の構築にだけ `source`／`target` を使い、結果を `Map<edge_id, category>` として返す。公開5モードに加え、公開scope UIを持たない内部unit-only `previous1` 契約がある。

- `complete`: traversable な chronology adjacency を全て辿る。
- `site-proposal`: `tierNodeIds` を incoming／back traversal にだけ適用する。
- `previous1`: goal への direct incoming のみを許可する。現行 export には公開scope controlがないため、実ブラウザでは `coverage_gaps` に `available=false, coverage=internal-unit-only` として報告し、内部の scope state は呼び出していない。
- `or`: 各 goal の edge-ID map を union する。
- `and`: 各 goal の edge ID を intersection する。
- `path`: 渡された `pathEdges` を、render boundary で materialize 済みの traversable chronology edge ID に対して絞り込む。classifier 内で新しい chronology search／BFS は行わない。

全モードで display-only ID は map に入らず、`traversable:false` の線は点灯しない。

## PATH render-boundary materialization と SVG/Canvas parity

`materializeChronologyPathEdgeIds` は、既存の PATH 入力に含まれる pair key または chronology edge ID を、既に描画された traversable edge ID へ明示的に写像する。これは表示境界での no-search materialization であり、暗黙の BFS や別の chronology 探索ではない。SVG の `renderChronologySelectionState` と Canvas の mobile resource map の両方で同じ edge ID を用いるため、PATH の点灯を classifier の pair-key fallback に戻さない。

SVG は `data-chronology-edge-id`、Canvas は `overlayChronologyEdgeId` と `overlayChronologyDisplayOnly`／`overlayChronologyTraversable` を保持する。`mobileOverlayChronologyEdgeClassMap` は SVG と同じ edge-ID keyed map を返し、同一 selection state の materialized ID set と category を一致させる。

## 実 Chrome/CDP browser audit

Node runner `tests/library_v5/browser_chronology_audit.mjs` をローカル静的サーバー上で実行し、実際の Chrome pointer event と条件待機だけで公開挙動を観測した。production selection function の直接呼び出し、overview／release の `g.edge` 集合の監査、固定 sleep は使用していない。

結果:

- `summary`: `cases=6`, `failures=0`, `coverage_gaps=1`
- structural: chronology edge `74`、duplicate IDs `[]`、display-only highlighted `[]`
- non-traversable IDs: `sequence-morbius-2022-madame-web-2024-ssu-10`、`sequence-madame-web-2024-kraven-the-hunter-2024-ssu-11`、`branch-deadpool-2016-logan-2017-fox-ambiguous`
- 5 public mode checks: `complete`、`site-proposal`、`or`、`and`、`path` は `ok=true`。`previous1` は成功skipではなく `coverage_gaps` に `available=false, coverage=internal-unit-only` として記録し、理由は「この export に public control がないため」、内部 scope state は呼び出していない。
- SVG/Canvas parity: Canvas available、materialized ID set／category の failures `[]`（74 IDs）
- round-trip: `overview_to_chronology=true`、`chronology_to_overview=true`

Python wrapper の実 Chrome case も `Ran 1 test ... OK` で終了した。通常の full suite では browser opt-in を要求する 3 テストだけが環境ゲートで skip される。

## Full local verification

AGENTS.md 指定の bundled runtime で、以下の exact command を実行した。

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

結果:

- full unittest: `Ran 393 tests in 21.614s`, `OK (skipped=3)`
- build: exit code `0`、`audit_ok=true`、`audit_issue_count=0`、`content_audit.issue_count=0`
- SQLite: foreign-key check `0` rows、`integrity_check=ok`
- compatibility: `work_edges_all=361`、`work_pair_reasons=569`、`prewatch_edges=199`、story paths `83/83`
- export: `131` nodes、`361` edges、`569` reasons、`42` character groups
- DB observations: `events/event_occurrences/multiverse_transitions/transition_participants = 9/9/9/10`、`chronology_assertions=0`
- `git diff --check` は clean。`git diff -- data/library data/content_audit` は empty で、canonical CSV、`data/content_audit/reviews.csv`、SQLite の canonical／persistent inputs に差分はない。

build が作成した `data/content_audit/CONTENT_AUDIT.md`、`data/content_audit/queue.csv`、`data/derived/LIBRARY_AUDIT.md`、`data/derived/audit.json`、`data/derived/db/`、`data/derived/library_manifest.json` と Python `__pycache__` は既知の transient output として扱う。canonical CSV と persistent review ledger は削除・復元の対象にしない。

## Canonical／semantic boundary

この実装で chronology の canonical assertion、relation fact、event／transition fact、release/status fact、SQLite canonical input、persistent review ledger は追加・変更していない。chronology 線は表示用の layout/materialization であり、既存の canonical graph policy から新しい pair や reason を生成しない。

公開順表示はこの chronology plan の対象外である。未実施の別計画 `docs/superpowers/plans/2026-09-02-marvel-library-publication-order-display.md` は release-order の日付軸／line-free viewer 契約を扱うため、今回の chronology edge identity や6モード実装と混ぜて開始しない。

## Freshness／merge gate

開始時に `git fetch origin` を実行したが、`.git/FETCH_HEAD` に対して `Permission denied`（`error: cannot open '.git/FETCH_HEAD': Permission denied`）で失敗した。この freshness failure は環境制約として記録し、reset、overwrite、force update は行っていない。現在の実装 HEAD は `5ff75514dccb4c2d4cae3e483c09f3ad995cfae5` である。

本レビューとハンドオフ／ロードマップの変更は docs-only commit として残し、push、PR merge、`main` への統合、GitHub Pages 公開は行わない。次の gate は、全ブランチ差分のレビュー、必要な remote CI／公開 artifact 確認、およびユーザーの明示的な merge／publish 承認である。
