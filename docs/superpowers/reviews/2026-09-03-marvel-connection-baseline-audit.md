# Marvel Library v5 接続完全監査・現行ベースライン（2026-09-03）

## 判定対象

- 監査ブランチ: `codex/connection-complete-audit`
- 監査時点: `1ce27283dada1d4bd8058db6ae32584a1ef397b1`（`main` `30ffbbf9de9624b644f8c267d1543347a273948c` を取り込み済み）
- canonical CSV SHA-256（監査時点）: `e96f71b10b71e22441428a994e964eca7533c7686c57cf9a400ec57e38e435d9`
- 正本: `data/library/*.csv`、監査台帳: `data/content_audit/reviews.csv`
- 派生: `data/derived/work_edges_all.csv`、`work_pair_reasons.csv`、`flowchart.json`

## 件数と完全在庫

独立実装 `scripts/library_v5/connectivity_audit.py` が、製品導出コードや選択JSをimportせずに全件を再計数した。

| 対象 | 件数 |
| --- | ---: |
| 作品 | 131 |
| active work relation | 161 |
| active appearance | 169 |
| multiverse transition | 9 |
| chronology assertion | 0 |
| 派生作品ペア | 361 |
| 派生理由 | 569 |
| shared_entity理由 | 402 |
| explicit_relation理由 | 161 |
| multiverse_transition理由 | 6 |
| prewatch互換線 | 199 |

監査レポートには131作品の`work_inventory`と361ペアの`edge_inventory`を必ず含める。各作品は一度だけ、各ペアはsource/targetの順序付きで一度だけ記録し、理由ID・理由種別・support fact ID・verification status・処置を追跡できる。

## 構造監査

- 構造的失敗: 0
- directed relation cycle: 0
- export pair mismatch: 0
- reason orphan: 0
- transitionが独立base pairなしに新規ペアを作った件数: 0
- normalized release/status/chronology/prewatch reasonのsemantic graph混入: 0
- SQLite build: 成功、audit issue 0、content-audit issue 0、FK check 0、integrity `ok`

従って、現在確認できる問題は「導出器が既存正本を落とす／逆向きにする」という機械的欠陥ではない。正本にまだ根拠がない接続の扱いは、次の意味監査で保留として分離した。

## 作品被覆

無向degree 0は次の8作品である。孤立をタイトルや同一フランチャイズだけで補完してはならない。

`blade-mcu-tba-tba`, `kraven-the-hunter-2024`, `madame-web-2024`, `moon-knight-2022`, `the-new-mutants-2020`, `werewolf-by-night-2022`, `wonder-man-s1-2026`, `wonder-man-s2-tba`

degree `<= 3` は74作品、無向連結成分は14、最大成分は109作品だった。これは欠落の証明ではなく、個別ソース監査の優先キューである。

## 再現コマンド

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -B -m scripts.library_v5.connectivity_audit --root . --json $env:TEMP\marvel-connectivity-audit.json
& $MarvelPython -B -m unittest tests.library_v5.test_connectivity_audit tests.library_v5.test_connectivity_projection_contract -v
```

JSONは監査時の一時成果物であり、canonical CSVやpersistent review ledgerではない。
