# Marvel Library v5 relation evidence promotion wave010 review

## 判定

Codexの3分割読み取り監査と、通常のChatGPT（Chatモード、GitHub接続）の独立読み取り監査を突き合わせた。公式一次ソースが既存の関係意味を直接支持する11件だけを `legacy_seed -> source_verified` に昇格した。`X-Men: Days of Future Past -> X-Men: Apocalypse` は、公式ページが前作の成功と制作継続を述べるに留まり、物語上の続編関係を直接支持しないため `legacy_seed` のまま保留した。

## 昇格した関係

| relation_id | 根拠の要点 | 境界 |
| --- | --- | --- |
| `work-relation-avengers-age-of-ultron-2015-captain-america-civil-war-2016-aftermath` | Marvel Phase Three guide がソコヴィアでのUltron戦の民間被害をCivil Warの帰結として説明 | 正確な時系列や広い因果関係は追加しない |
| `work-relation-thor-ragnarok-2017-avengers-infinity-war-2018-crossover` | MarvelのLoki回顧がRagnarokからInfinity Warまでの同一Lokiの物語を記述 | 全登場人物・variant・timelineは拡張しない |
| `work-relation-captain-america-civil-war-2016-ant-man-and-the-wasp-2018-aftermath` | Marvel作品ページがCivil WarのaftermathとScottの選択の帰結を明記 | 正確な経過時間や他人物の継続は追加しない |
| `work-relation-ms-marvel-2022-the-marvels-2023-story-link` | Disney公式記事がMs. MarvelのKamalaの生活・背景をThe Marvelsへ持ち込むと説明 | シリーズ全体を直接前提とはしない |
| `work-relation-what-if-s2-2023-what-if-s3-2024-sequel` | Marvel Animation panel がSeason 2に続くSeason 3を発表 | release/statusは別fact |
| `work-relation-iron-man-3-2013-all-hail-the-king-2014-sequel` | Disney+公式概要がIron Man 3後のTrevor Slatteryを直接記述 | feature-film sequelや追加identityは主張しない |
| `work-relation-the-avengers-2012-item-47-2012-sequel` | Disney+公式概要がBattle of New York後のS.H.I.E.L.D.回収を記述 | 正確な日数や宣伝上の続編ラベルは追加しない |
| `work-relation-jessica-jones-s1-2015-jessica-jones-s2-2018-sequel` | Marvel公式発表が同一シリーズのSeason 2とSeason 1を明記 | 他Netflix作品への接続は追加しない |
| `work-relation-jessica-jones-s2-2018-jessica-jones-s3-2019-sequel` | Marvel公式発表がSeason 2に続く第三シーズンを明記 | release/statusは別fact |
| `work-relation-iron-fist-s1-2017-iron-fist-s2-2018-sequel` | Marvel公式発表が同一シリーズのsecond seasonを明記 | Defenders等の新規relationは追加しない |
| `work-relation-cloak-dagger-20182019-runaways-20172019-crossover` | Marvel公式記事がRunaways Season 3での公式crossoverを明記 | `uncertain_legacy_tv`、MCU/Earthは変更しない |

## 保留

- `work-relation-x-men-days-of-future-past-2014-x-men-apocalypse-2016-sequel`: 20th Century Studios公式ページの “following” は監督・フランチャイズの制作継続を示すだけで、作品内ストーリーの継続を直接示さない。共通監督・キャストや公開順から補わない。

## 変更範囲

- 既存11 relation row は `verification_status` のみ変更。
- 新規の公式 `sources.csv` 11行、primary `evidence.csv` 11行、`reviews.csv` の `verified_source` 遷移11行を追加。
- relation ID、方向、relation kind、scope、directness、continuity scope、certainty、notes、work pair、線数は不変。

## 検証

- focused wave010 test: 2/2 PASS。
- bundled library-v5 suite: 457 PASS, 4 environment-gated skips。
- deterministic build: audit issues 0、content-audit issues 0、131 nodes / 355 edges / 562 reasons、story paths 83/83。
- independent connectivity audit: structural failures 0、projection mismatches 0、reason orphans 0、unsupported transition edges 0。
- real Chrome/CDP audits: selection PASS、interaction PASS、chronology PASS、publication-order PASS（131 cards、failures 0、syntheticEdges 0）。

## ソース

- Marvel: Phase Three guide, Loki retrospective, Ant-Man and the Wasp page, What If...? animation panel, Jessica Jones S2/S3 announcements, Iron Fist S2 announcement, Runaways/Cloak & Dagger crossover article。
- Disney+/The Walt Disney Company: All Hail the King synopsis, Item 47 synopsis, The Marvels / Ms. Marvel interview。
