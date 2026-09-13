# Marvel Library v5 relation evidence promotion wave011 plan

## 目的

既存の `work_relations.csv` にある直接の続編・シーズン継続関係のうち、公式一次ソースが既存の関係意味を直接支持する小波だけを、`legacy_seed` から `source_verified` に昇格する。作品・関係の方向や意味論、release/status、multiverse の事実は変更しない。

## 対象

次の5件を対象とする。

| relation_id | source | 境界 |
| --- | --- | --- |
| `work-relation-venom-2018-venom-let-there-be-carnage-2021-sequel` | Sony公式プレスリリース | 続編関係のみ。公開日・世界線は追加しない |
| `work-relation-ant-man-and-the-wasp-2018-ant-man-and-the-wasp-quantumania-2023-sequel` | Marvel公式記事 | Ant-Man sagaの第三作という直接支持のみ |
| `work-relation-spider-man-2002-spider-man-2-2004-sequel` | Sony公式作品ページ | Raimi系列の既存続編関係のみ |
| `work-relation-luke-cage-s1-2016-luke-cage-s2-2018-sequel` | Marvel公式Season 2発表 | シーズン継続のみ。Defenders等へ拡張しない |
| `work-relation-your-friendly-neighborhood-spider-man-s1-2025-your-friendly-neighborhood-spider-man-s2-2026-sequel` | The Walt Disney Company公式記事 | シーズン継続のみ。release/statusの矛盾は解消しない |

各行について、専用 `sources.csv`、primary `evidence.csv`、`legacy_seed -> source_verified` の `reviews.csv` を1行ずつ追加する。既存の relation ID、方向、kind、scope、directness、continuity scope、certainty、notes は保持する。

## 保留

- `work-relation-x-men-days-of-future-past-2014-x-men-apocalypse-2016-sequel`: 公式ページの “following” だけでは物語上の続編を直接支持しないため保留。
- `work-relation-spider-man-2-2004-spider-man-3-2007-sequel`: 今回は既存ソースの直接性を追加検証せず保留。

保留行は削除・書換え・推測による昇格を行わない。

## 実装と検証

1. 先に専用テストをREDで追加し、5件の関係 tuple、source URL、fact単位evidence、review遷移、保留行、355 edges / 562 reasonsを固定する。
2. canonical CSVへ最小変更を加え、buildでSQLiteとderived graphを再生成する。
3. focused test、bundled全unit test、deterministic build、`git diff --check`、content-audit/relation inventoryを実行する。
4. 差分はcanonicalの5 relation status、sources/evidence/reviews各5行、テスト、計画・レビュー文書と生成物に限定する。
5. PRのCIでselection / interaction / chronology / publication-order / mobile-shellを含む既存required checksを再実行し、GREEN後に通常のPR経由で統合する。

## 完了条件

- 5件のみが根拠付きで `source_verified`。
- 2件の保留行は `legacy_seed` のまま。
- audit issue、content-audit issue、FK、SQLite integrityが0/ok。
- 131 nodes / 355 edges / 562 reasons、story paths 83/83を維持。
- release/status、events、transitions、appearance/identityのCSVに差分がない。
