# Marvel Library v5 派生・HTML投影監査（2026-09-03）

## 対象

`db_views.py` / `db_rollup.py` / `flowchart_export.py` の出力を、独立監査器と既存のブラウザ監査で確認した。正本の意味をHTMLの既存線から逆算していない。

## parity結果

- SQLite → `work_pair_reasons.csv` → `flowchart.json`: 361 pair / 569 reasonで一致
- `flowchart.json`: 131 node、361 edge、569 reason、edge pair重複0
- 全edgeのreason IDは同一pairのreasonへ解決し、reason orphan 0
- active work relation 161件は全て一つの明示的relation reasonへ投影
- active appearanceの共有pair 402件は全て一つのshared_entity reasonへ投影
- release/status/chronology/prewatch factはsemantic graphへ混入0
- transition reasonが独立base pairを作った件数0

## ブラウザ確認

公開tierは`site-proposal`と`complete`の2つだけである。既存Chrome/CDP監査の実測は次の通り。

- 131作品 × 2 tierのDOM選択集合: mismatch 0
- PC操作代表6ケース（再クリック解除、背景解除、ドラッグ後維持、パネル切替など）: 6/6成功
- chronology監査: 74 edge、重複0、display-only誤点灯0、SVG/Canvas parity成功
- publication-order監査: 131 card、失敗0、synthetic edge 0

これらは「現在のJSONと独立selection oracleの一致」を保証する。JSON自体に必要な意味接続が存在するかは、別途canonical意味監査で扱う。

## 表示境界

- 全semantic edgeは初期表示対象であり、選択は既存edgeのクラス変更だけを行う。
- `site-proposal`はincoming weak fan-inを前史として自動採用しない。明示的作品関係の前史は保持する。
- `complete`はincoming/outgoingを再帰探索するが、event/transitionの意味を時系列へ変換しない。
- chronologyは独立fixture層、publication-orderは日付軸であり、どちらもsemantic edgeを新規生成しない。
- 旧prewatch互換199線は表示政策の互換ビューで、semantic graphの根拠にはしない。

## 既知の意味上の保留

JSON/DOM parityが0でも、legacy_seedのsemantic妥当性までは証明しない。variant個体の同一entity統合や、個別公式ソース未登録の関係は、根拠追加バッチの対象として保留する。UIの選択分類を変更してこれらを隠すことはしない。
