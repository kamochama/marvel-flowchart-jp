# Marvel Library — 公開順表示契約レビュー

実施日: 2026-09-03

対象リポジトリ: `kamochama/marvel-flowchart-jp`

対象ブランチ: `codex/publication-order-display-contract`

実装範囲: `5e159c4236ee03ede4c5175519bff468ff6beb1e..c5e24393904aec6ae50511813b61a300c2a572f1`

参照計画・仕様: `docs/superpowers/plans/2026-09-02-marvel-library-publication-order-display.md`、`docs/superpowers/specs/2026-09-02-marvel-library-chronology-publication-order-contract.md` §5

## 判定

公開順表示契約は、静的契約、全ライブラリテスト、通常 build、実 Chrome/CDP の PC／mobile 監査を通過したため、この branch のローカル検証結果として **PASS** とする。公開順は関係グラフではなく、公開日・精度・TBD を読む日付軸／作品カードの focus view である。canonical CSV、SQLite の canonical input／persistent export、`data/content_audit/reviews.csv` は変更していない。

これは production integration の判定ではない。remote CI、完全な branch review、`main` への merge、GitHub Pages 公開は未承認であり、通常の明示的 approval gate に残す。

## 表示契約と実装境界

- 全 `131` 作品を `g.release-node[data-release-work-id]` として一度ずつ描画し、重複なし。公開順 SVG は `data-relationship-edges="off"` を持ち、`g.edge=0`、`g.chronology-edge=0` である。公開順には隣接カード矢印や relation／chronology 線を生成しない。
- 公開順で使うのはカード、公開日、日付精度、時代・lane の表示だけである。関係地図の `backEdges`／`forwardEdges`／`contextEdges`／`pathEdges` を公開順 Canvas の合成線へ渡さない。
- exact date、month only、year only、undated/TBD を区別し、月・年から実在しない日を補わない。canonical export は `day=127 / month=2 / year=0 / none=2` であり、year-only は既存作品をブラウザ内だけで年精度へ変換する明示的 runtime fixture である（canonical release/status data は不変）。
- dated card のレイアウト sort key と表示ラベルを分離し、同日順は canonical stable sort index、最後に `work_id` で決定する。TBD は確定日付軸から分離した `Upcoming / date TBD` lane に置く。
- 選択対象の `work_id` と詳細 focus は overview／chronology と共有する。PC の release card focus と detail focus は同じ作品を指し、overview に戻ると relation highlight を通常再構築する。release 自身は共有 selection を受けても relation highlight を漏らさない。
- mobile Canvas でも同じ release no-line 境界を守る。実 390×844 viewport の全ケースで `nodeBoxes=131`、`overlaySyntheticDrawn=0` であり、relation／chronology の合成線は 0 本である。

## 実 Chrome/CDP 監査

実行した direct runner:

```powershell
node tests/library_v5/browser_publication_order_audit.mjs --root . --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe' --timeout-ms 8000
```

実測 report:

- `summary`: `cards=131`, `cases=21`, `failures=0`, `syntheticEdges=0`
- structural: `duplicate_ids=false`, `edge_count=0`, `chronology_edge_count=0`
- geometry: `viewBox="0 0 1320 6302"`, `lineCount=43`, 選択前後・往復の geometry failures `[]`
- precision: exact-day `iron-man-2008` は `2008.05.02`、month-only `daredevil-born-again-s3-tba` は `2027.03`、year-only runtime fixture は `2027`、TBD `blade-mcu-tba-tba` は `公開日未定`。月／年ケースで日を発明していない。
- TBD metadata: `sortKey=9999-99-99`、`lane=upcoming-tbd`、`isTbd=true`
- stable tie-break: TBD の `blade-mcu-tba-tba` → `wonder-man-s2-tba` は expected と actual が一致し、`failures=[]`
- round-trip: `release_to_overview=true`、`overview_to_release=true`、`release_to_chronology=true`、`chronology_to_release=true`。中間 chronology は `74` edges、`9` highlights、focus/detail は `iron-man-2008`。
- mobile: viewport `[390,844]`、全状態の `nodeBoxes=131`、`syntheticEdges=0`

Python wrapper の opt-in 実行も成功した。

```powershell
$env:MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT = '1'
$env:MARVEL_CHROME_BIN = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
& $MarvelPython -B -m unittest tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_headless_publication_order_contract -v
```

出力は `cards=131, failures=0, syntheticEdges=0`、`Ran 1 test in 23.311s`、`OK`（exit `0`）だった。実入力で day／month／year／TBD の PC カード、再タップ解除、背景解除、drag 後の選択維持、mobile の同4精度ケース、overview／chronology の往復を確認した。

## Full local verification

AGENTS.md 指定の bundled runtime と PowerShell call operator (`& $MarvelPython`) で実行した。

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -B -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -B -m scripts.library_v5.build --repo-root .
git diff --check
```

結果:

- full unittest: `Ran 424 tests in 24.857s`, `OK (skipped=4)`, exit `0`。skip は opt-in browser coverage の環境ゲートだけである。
- build: exit `0`、`audit_ok=true`、`audit_issue_count=0`、`content_audit.issue_count=0`。
- SQLite: foreign-key check `0` rows、`integrity_check=ok`。schema `1.2-normalized-releases-status`、logical fingerprint/equivalence `39917ceee6af94e680acebdf7b570142f1a2995646aec1dd344ec3ed395b5b92`。full suite の deterministic fingerprint/build/export tests も GREEN である。
- compatibility: `work_edges_all=361`、`work_pair_reasons=569`、`prewatch_edges=199`、story paths `83/83`
- export: `131` nodes、`361` edges、`569` reasons、`42` character groups
- content audit: issue `0`、review count `105`。DB observations は `events/event_occurrences/multiverse_transitions/transition_participants = 9/9/9/10`、`chronology_assertions=0`。
- `git diff --check`: clean。

build が作成した `data/content_audit/CONTENT_AUDIT.md`、`data/content_audit/queue.csv`、`data/derived/LIBRARY_AUDIT.md`、`data/derived/audit.json`、`data/derived/library_manifest.json`、`data/derived/db/` の manifest／SQLite は、内容を検査した後、worktree 内の既知の transient output として明示パスだけ削除した。canonical CSV、SQLite の canonical／persistent inputs、persistent review ledger は削除・変更していない。

## Branch diff と保護範囲

BASE `5e159c4236ee03ede4c5175519bff468ff6beb1e` から HEAD `c5e24393904aec6ae50511813b61a300c2a572f1` までの全差分は `11 files changed, 1834 insertions(+), 22 deletions(-)` で、対象は viewer (`index.html`)、browser/unit tests、CI workflow、Task 3–5 report のみである。`data/library/**`、`data/content_audit/reviews.csv`、`data/derived/**`、SQLite候補に対する `git diff --quiet` は exit `0` で、canonical data／SQLite export／persistent review ledger の差分はない。Task6で追加するのは本レビュー、handoff、roadmapだけである。

## Freshness と merge gate

通常権限での開始時 `git fetch origin` は linked worktree の `.git/worktrees/publication-order-display-contract/FETCH_HEAD` に対する `Permission denied` だったが、権限付きの再実行で取得に成功した。確認時点の `origin/main` は `5e159c4236ee03ede4c5175519bff468ff6beb1e`（AGENTS.md記載の `04ff92b...` を祖先に含む）であり、HEAD `c5e24393904aec6ae50511813b61a300c2a572f1` はそれを上書きしていない。reset、overwrite、rebase、force update は実施していない。

この Task6 は docs-only handoff commit を作成して停止する。push、PR merge、`main` への統合、Pages 公開は行わない。次の gate は、ユーザーの明示的 approval の下で、完全な branch diff、fresh remote CI、公開 artifact／Pages 動作を確認してから通常の merge／publish 手順へ進むことである。
