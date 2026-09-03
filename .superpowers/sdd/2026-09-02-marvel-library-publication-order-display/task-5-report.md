# Task 5 report: 公開順の独立ブラウザ監査

実施日: 2026-09-03

## 実装

- `tests/library_v5/browser_publication_order_audit.mjs` を追加した。Node 標準機能だけで一時 HTTP server と Chrome CDP を起動し、PC 公開順 SVG と 390×844 mobile Canvas を実ブラウザ監査する。
- PC では `g.release-node[data-release-work-id]` の 131作品 exact set と重複なし、`g.edge` / `g.chronology-edge` が 0、カード `path d`、`viewBox`、年軸、時代・lane frame、line count の選択前後不変を確認する。day / month / year / TBD の代表選択、DOM precision / sort key / TBD marker / partial-date label、同一 sort key + lane の stable order、release → overview → release と release → chronology → release の detail focus と表示層分離も監査する。
- 現行 export は `day=127 / month=2 / none=2 / year=0` のため、year-only ケースだけは browser 内の `RELEASE_META` に既存月精度作品を年精度へ変換する明示的 runtime fixture を置き、公開 `window.ensureStageAViewInitialized('release')` 境界で実 view を再生成した。ケース後はページを再読込して元データへ戻す。canonical file は変更していない。
- mobile では CDP `Input.dispatchTouchEvent` だけで dated / TBD の選択、再タップ解除、選択中の背景解除、選択を維持する drag を実行する。各状態で `marvelCanvasAudit().active === true`、panel `release`、`nodeBoxes=131`、goal work ID、`overlaySyntheticDrawn=0` を確認し、viewport を最後に解除する。
- JSON report に `summary`、`cases`、`failures` のほか、`focus`、`geometry`、`line_free`、`precision`、`tbd`、`tie_break`、`round_trip`、`mobile` を含めた。failure または synthetic edge があれば runner は非0終了する。
- Python wrapper は JSON 未出力・不正 JSON・case 内 `overlaySyntheticDrawn != 0`・summary `syntheticEdges != 0` を明示的に拒否し、Node stdout を UTF-8 として読む。成功時に `cards=131, failures=0, syntheticEdges=0` を出力する。
- `.github/workflows/library-v5-ci.yml` に `browser-publication-order-audit` job を chronology audit 後として追加した。fixture build 後、`MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT=1` の専用 unittest を1回だけ実行し、同じ Chrome audit を二重実行しない。

## RED

wrapper / CI / real-touch 契約を先に追加して実行した。

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -B -m unittest tests.library_v5.test_browser_publication_order_audit -v
```

結果: `Ran 13 tests`、`FAILED (failures=2, errors=3, skipped=1)`。CI の direct runner 二重実行、mobile lifecycle の mouse dispatch、JSON validator / summary formatter 未実装をそれぞれ検出した。

既存 runner の Chrome 実行も行い、最初は `cards=131, cases=12, failures=2, syntheticEdges=0` だった。release → overview 切替直後の requestAnimationFrame 前に snapshot を確定し、focus と relation highlight を未描画として報告していた。

修正途中では次の具体的な統合失敗も再現・切り分けた。

- year fixture 再生成: IIFE 内部の `buildReleaseView` を直接参照して `ReferenceError`。公開 `ensureStageAViewInitialized` 境界へ変更した。
- touch lifecycle: drag 後の one-shot guard が直後の re-tap を消費。独立操作順を re-tap → background → drag に変更した。
- touch drag: goal bar の layout shift 後、開始点 `y=115.6875` が Canvas 上端 `y=186.6875` より外側だった。選択カードの再計算済み実 hit point を drag start にした。
- Windows wrapper: Node の日本語 JSON を既定 CP932 で読んで `UnicodeDecodeError`。`encoding='utf-8'` を指定した。

## GREEN / verification

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_browser_publication_order_audit -v
```

結果: `Ran 13 tests in 0.130s`、`OK (skipped=1)`。skip は opt-in Chrome test のみ。

```powershell
node --check tests/library_v5/browser_publication_order_audit.mjs
node tests/library_v5/browser_publication_order_audit.mjs --help
```

結果: いずれも exit 0。help は `geometry` と `synthetic` 契約を表示した。

```powershell
node tests/library_v5/browser_publication_order_audit.mjs --root . --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe' --timeout-ms 8000
```

結果: exit 0、`cards=131, cases=12, failures=0, syntheticEdges=0`。PC 4ケースと mobile 8 lifecycle state を完走した。

```powershell
$env:MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT = '1'
$env:MARVEL_CHROME_BIN = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
& $MarvelPython -B -m unittest tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_headless_publication_order_contract -v
```

結果: `cards=131, failures=0, syntheticEdges=0`、`Ran 1 test in 30.229s`、`OK`。

```powershell
& $MarvelPython -B -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -B -m scripts.library_v5.build --repo-root .
git diff --check
```

結果: full suite は `Ran 421 tests in 23.146s`、`OK (skipped=4)`。build は audit issue 0、content-audit issue 0、131 nodes / 361 edges / 569 reasons、SQLite 出力成功。既知の untracked generated audit/DB outputs は絶対パスが worktree 内であることを確認して除去した。`git diff --check` は問題なし。

## Concerns

- canonical export に year precision の作品がないため、year-only browser coverage は明示的 runtime fixture である。fixture の由来と値は JSON report の `precision.year-only.syntheticFixture` に残す。
- runner の JSON は全カード path・軸・frame snapshot を保持するため約 166 KB。CI は wrapper が capture し、通常ログには3値の summary だけを出す。
- canonical CSV、SQLite、persistent review ledger、`index.html` は変更していない。新規 npm dependency もない。

## Fix round 1: chronology を中間に挟む panel round-trip

独立差分確認で、初回実装の panel round-trip が release → overview → release のみで、計画が要求する chronology 中間経路を実行していないことを確認した。

### RED

```powershell
& $MarvelPython -B -m unittest tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_runner_round_trip_crosses_real_chronology_panel -v
```

結果: `Ran 1 test`、`FAIL`。runner の desktop audit 範囲に `chronology-middle-round-trip` と chronology tab click が存在せず失敗した。

### GREEN

- exact-day release card を選択した状態から `.tab[data-target="chronology"]` を実クリックし、lazy panel ready、実 `g.chronology-edge` が 1本以上、同じ work ID の detail focus / node focus を待機する。
- `.tab[data-target="release"]` を実クリックして戻り、detail focus、カード集合、全 `path d`、`viewBox`、年軸、時代・lane frame、line count の不変と、release 側 `g.edge=0` / `g.chronology-edge=0` / highlight 0 を再確認する。
- JSON `round_trip` に `release_to_chronology`、`chronology_to_release`、chronology snapshot を記録する。

実 Chrome runner の結果: `cards=131, cases=13, failures=0, syntheticEdges=0`。chronology snapshot は `ready=true`、`chronologyEdges=74`、`chronologyHighlights=9`、focus/detail は `iron-man-2008` だった。

fix round 後の確定検証は次のとおり。

- static wrapper tests: `Ran 14 tests`、`OK (skipped=1)`。skip は opt-in Chrome test のみ。
- CI-equivalent real Chrome wrapper: `cards=131, failures=0, syntheticEdges=0`、`Ran 1 test in 25.415s`、`OK`。
- library-v5 full suite: `Ran 422 tests in 29.810s`、`OK (skipped=4)`。
- build: audit issue 0、content-audit issue 0、131 nodes / 361 edges / 569 reasons、SQLite 出力成功。既知の untracked generated outputs は worktree 内の対象を確認して除去した。
- `node --check`、runner `--help`、`git diff --check`: すべて exit 0。

## Fix round 2: mobile precision parity と排他的 focus

最終レビューで、mobile が dated / TBD の2代表だけで month-only / year-only を実入力監査していないこと、および PC focus/shared selection の検証が包含判定だったことを確認した。

### RED

```powershell
& $MarvelPython -B -m unittest `
  tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_runner_requires_exclusive_desktop_focus_and_no_goal_mutation `
  tests.library_v5.test_browser_publication_order_audit.BrowserPublicationOrderAuditTests.test_runner_mobile_covers_every_publication_precision_with_year_fixture -v
```

結果: `Ran 2 tests`、`FAILED (failures=2)`。runner に排他的な `focus=[id]` / desktop `selected=[]` 契約と mobile year fixture / 4 precision case がないため失敗した。

### GREEN

- PC release card の実クリック後と overview / chronology round-trip 後を、sorted `focus === [id]`、shared `selected === []`、detail focus `=== id` で待機・検証する。PC左クリックは詳細閲覧であり、ゴール集合を変更しない契約を明示した。
- mobile は exact-day / month-only / year-only / TBD の4代表すべてで、実 touch による select / re-tap / background / drag-end の4状態、合計16状態を監査する。選択状態は shared `selected === [id]` と `goals === [id]`、解除状態は `selected === []`、全状態で `nodeBoxes=131` と `overlaySyntheticDrawn=0` を要求する。
- canonical に year precision がないため、mobile year-only でも `RELEASE_META` をページ内だけで年精度へ変換し、公開 `window.ensureStageAViewInitialized('release')` で release view を再生成する。続けて公開 `activatePanel` で390×844 Canvasを再初期化し、backing card の precision / label と Canvas 131 nodeBoxes を待ってから touch lifecycle を行う。次ケースのページ再読込で元データへ戻す。

fix round 後の確定検証は次のとおり。

- static wrapper tests: `Ran 16 tests in 0.158s`、`OK (skipped=1)`。
- CI-equivalent real Chrome wrapper: `cards=131, failures=0, syntheticEdges=0`、最終再実行は `Ran 1 test in 26.311s`、`OK`。live wrapper は PC 4 precision の排他的 focus/shared state と mobile 4 precision × 4 lifecycle の exact case set/state を検証した。
- library-v5 full suite: `Ran 424 tests in 28.626s`、`OK (skipped=4)`。
- build: audit issue 0、content-audit issue 0、131 nodes / 361 edges / 569 reasons、SQLite 出力成功。既知の untracked generated outputs は worktree 内の対象を確認して除去した。
- `node --check`: exit 0。
