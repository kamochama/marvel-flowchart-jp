# Marvel Library v5 relation evidence promotion wave011 review

## 判定

公式一次ソースが既存の直接続編・シーズン継続関係を支持する5件だけを `legacy_seed -> source_verified` に昇格した。ChatGPTの独立レビューと読み取り監査を照合し、公式文言がフランチャイズ制作継続に留まる候補は無理に昇格しなかった。

## 昇格した関係

| relation_id | 根拠 | 境界 |
| --- | --- | --- |
| `work-relation-venom-2018-venom-let-there-be-carnage-2021-sequel` | Sony公式リリースがLet There Be CarnageをVenomの続編と明記 | release/status・multiverseは追加しない |
| `work-relation-ant-man-and-the-wasp-2018-ant-man-and-the-wasp-quantumania-2023-sequel` | Marvel公式記事がQuantumaniaをAnt-Man sagaの第三作と説明 | 公開日・別の因果関係は追加しない |
| `work-relation-spider-man-2002-spider-man-2-2004-sequel` | Sony公式作品ページがSpider-Man 2をシリーズ最新作として説明しTobey Maguireの復帰を記載 | Raimi系列の既存関係だけを支持 |
| `work-relation-luke-cage-s1-2016-luke-cage-s2-2018-sequel` | Marvel公式Season 2発表がLuke Cageの帰還と継続するHarlem storyを説明 | DefendersやMCU正史へ拡張しない |
| `work-relation-your-friendly-neighborhood-spider-man-s1-2025-your-friendly-neighborhood-spider-man-s2-2026-sequel` | Disney公式記事がSeason 1後のfuture storylinesとSeason 2以降の旅を説明 | release/statusの別factは変更しない |

## 保留

- `work-relation-x-men-days-of-future-past-2014-x-men-apocalypse-2016-sequel`: “following” は制作・フランチャイズ継続の意味にも読め、物語上の続編を直接支持しない。
- `work-relation-spider-man-2-2004-spider-man-3-2007-sequel`: 今回の一次ソース監査範囲では直接根拠を追加していない。

両方とも `legacy_seed` のまま保持し、共通キャスト・公開順・シリーズ名から補完していない。

## 変更範囲

- 既存5 relation row は `verification_status` のみ変更。
- `sources.csv` 5行、`evidence.csv` 5行、`reviews.csv` 5行を追加。
- relation tuple、relation ID、graph topology、release/status、events/transitionsは不変。

## 検証

- focused wave011 test: 2/2 PASS。
- deterministic build: exit 0、audit issues 0、content-audit issues 0、131 nodes / 355 edges / 562 reasons、story paths 83/83。
- generated DB: 164 work relations、186 evidence、160 reviews、96 sources。
- `git diff --check`: PASS。
- PR CIでは既存のselection / interaction / chronology / publication-order / mobile-shell required checksを実行する。
