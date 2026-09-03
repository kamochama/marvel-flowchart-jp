# Task 5 report: 公開順の独立ブラウザ監査

実施日: 2026-09-03

## 実装

- `tests/library_v5/browser_publication_order_audit.mjs` を追加した。Node 標準機能だけで一時 HTTP server と Chrome CDP を起動し、PC 公開順 SVG と 390×844 mobile Canvas を実ブラウザ監査する。
- PC では `g.release-node[data-release-work-id]` の 131作品 exact set と重複なし、`g.edge` / `g.chronology-edge` が 0、カード `path d`、`viewBox`、年軸、時代・lane frame、line count の選択前後不変を確認する。day / month / year / TBD の代表選択、DOM precision / sort key / TBD marker / partial-date label、同一 sort key + lane の stable order、release → overview → release の detail focus と relation highlight の表示層分離も監査する。
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
- runner の JSON は全カード path・軸・frame snapshot を保持するため約 147 KB。CI は wrapper が capture し、通常ログには3値の summary だけを出す。
- canonical CSV、SQLite、persistent review ledger、`index.html` は変更していない。新規 npm dependency もない。
