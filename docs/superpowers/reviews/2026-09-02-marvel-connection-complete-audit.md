# Marvel Library v5 全作品接続完全監査（2026-09-02）

## 監査範囲とスナップショット

- 対象 checkout: `06d4f17340730cfddbcf6e753f4c98e2e5d18987`
- 作品: 131
- 派生作品ペア: 361
- 作品ペア理由: 569（`shared_entity` 402、`explicit_relation` 161、`multiverse_transition` 6）
- 旧互換 prewatch: 199
- 参照元: `data/library/*.csv`, `data/derived/work_edges_all.csv`, `data/derived/work_pair_reasons.csv`, `data/derived/flowchart.json`, `index.html`

canonical CSV、SQLite view、派生CSV、JSONを独立突合した。reason/edge ID重複、self-loop、orphan reason、FK不整合、directed cycleは0件。SQL→CSV→JSONは 361/569 で完全一致し、release/status factがedge reasonへ混入した形跡も0件である。

## 意味監査の処置

reason単位の処置は次のとおり。

| 処置 | 件数 | 意味 |
|---|---:|---|
| retain | 15 | source-verifiedで方向・意味とも支持される |
| needs-source | 526 | 意味は候補だがcanonical factがlegacy_seed |
| defer | 11 | legacy TV・旧作品帰還・Doomsday等で個別根拠待ち |
| over-broad | 17 | variant個体を同一entityとしてfan-out |
| wrong-direction | 0 | 明確な逆向きなし |
| duplicate | 0 | 独立理由の重複なし |
| missing-candidate | 0 | 現行canonical factからの導出欠落なし |

edge単位では、少なくとも1つのretain reasonを持つ11、needs-source 323、defer 11、純粋なover-broad 16である。edge retainは「全reasonがverified」という意味ではない。

retainの主な関係は、Inhumans→Multiverse of Madness、Logan→Deadpool & Wolverine、Loki S2→Deadpool & Wolverine、Spider-Man旧作/ヴェノム→No Way Home、Homecoming→Morbius、No Way Home→Multiverse of Madness/Morbius、First Steps→Doomsday、Thunderbolts→First Stepsである。

### 最優先の過剰接続

`entity-x-680db112c0`（Logan/Wolverine）が variant分解されていないため、Deadpool & Wolverineへの次の7 reasonが over-broad。

- Logan、The Wolverine、X-Men、X-Men: Days of Future Past、X-Men Origins: Wolverine、X-Men: The Last Stand、X2 → Deadpool & Wolverine

Logan→Deadpool & Wolverineのedgeは独立したsource-verified story_linkがあるためedge自体はretain可能だが、shared_entity reasonはvariant監査後に置換する。

`entity-x-55e230260e`（Loki）が本来のLokiとTV分岐個体を統合しているため、Thor、The Avengers、Thor: The Dark World、Thor: Ragnarok、Avengers: Infinity War → Loki S1/S2（各2、計10 reason）が over-broad。Loki S1→S2は同一TV分岐内の候補としてneeds-source。

### 要出典の大部分

shared_entity 402 reasonのうち、source-verified appearanceによるretainは2件のみ。その他はappearanceがlegacy_seed/unknownであり、同じ俳優やcontinuityを根拠にしたものではないものの、作品間の予習・物語接続へ昇格する証拠がない。explicit_relationも149 active rowがlegacy_seedのため、個別URL/evidence/reviewなしにverified扱いしない。

## 方向・世界線・イベント

release順と異なる6 relation（短編→Thor、映画事件→Agents of S.H.I.E.L.D.、Cloak & Dagger→Runaways）は、意味方向を保持したlegacy relationであり、誤向きとは断定しない。ただしrelease chronologyとstory/事件波及を同じ矢印意味として表示しない。

`portrayals.csv`や同じ俳優だけでedgeを作る処理はなく、`derive_edges.py`はportrayalsを破棄してappearance entityだけを利用する。continuity membershipだけのbase reasonも0件。イベント9件はsource-verifiedで、transition reasonを作らない3イベント（Monicaの到着、Earth-838到着、WadeのTVA移送）は相手側の独立作品factがないため意図的deferであり、missing-candidateではない。

work arrowとcontinuity transitionの方向は別概念である。Thunderbolts→First Stepsは「含有作品→参照先」の表示で、continuity方向はEarth-828→Earth-616。Let There Be Carnage→No Way Homeは同一edgeに到着と帰還の複数transitionがある。

## 作品被覆

無向degree 0は次の8作品。

`blade-mcu-tba-tba`, `kraven-the-hunter-2024`, `madame-web-2024`, `moon-knight-2022`, `the-new-mutants-2020`, `werewolf-by-night-2022`, `wonder-man-s1-2026`, `wonder-man-s2-tba`

低接続（degree <= 3）は74作品、最大連結成分は109作品、全連結成分は14。孤立やbridge/articulationは追加接続の推測根拠ではなく、source追加または「未接続」の説明候補として扱う。

## prewatch・公式ルート・完全版

`data/prewatch_edges.csv` 199本は旧`connections.csv`から再生成する互換ビューで、semantic graphへ混入していない。semantic edgeとの重複は182、prewatch-onlyは17。これらを公式根拠と表示しない。

公式予習JSONはsource-verifiedだが、route隣接pairだけでなくroute内の順序付きgraph edgeをハイライトするため、Black Widow→Hawkeye、Black Widow→Thunderbolts、Falcon→Thunderboltsが公式隣接のように見える表示過剰がある。サイト提案ルートはeditorial/view-onlyであり、5 route 44隣接中graph存在28、非存在16。完全版もcanonical edgeを新規生成しないが、Doomsdayへのlegacy relationをverified story接続と誤認させない。

## 静的SVGとJSONの不一致（P1）

静的SVGには旧prewatch-only線が残り、`edgeRecordFromSvgGroup()`が理由なしの線を黙って表示する。semantic SVG 372 occurrenceのうち368が現在JSONの`strength`/`render_class`と不一致（JSONはweak 353、strong 3、very strong 5に対し、SVGは旧strong/medium等）。該当実装は `index.html` の 5911–5935、6022–6030、6326–6343、9002–9031 付近である。

優先修正は、(1) 旧prewatch-only線を除去またはview-only明示、(2) SVG初期化時にJSONのstrength/render_classを同期、(3) 未知線を検証でfail/non-edge化、である。DBへ線を追加する修正ではない。

## 修正順序とRED契約

1. 上記SVG/JSON同期とstale線の回帰テストを追加する。
2. Wolverine variant、Loki TV variantを別entityへ分解する設計と、既存edgeの置換・保持fixtureを作る。
3. 高fan-outのlegacy appearance/work_relationを個別公式URL→evidence→reviewで昇格またはdeferする。
4. 公式/サイト提案/完全版をview-only provenanceとして明示し、semantic edgeの証拠と混同しないテストを固定する。
5. 0接続作品については、根拠のない補完をせず、追加sourceが得られた場合だけ別バッチで候補化する。

この監査段階ではcanonical CSV、evidence/reviews、派生graphを変更していない。上記処置に基づく修正は、各項目ごとにRED→最小修正→全テスト・build・artifact突合を行う。
