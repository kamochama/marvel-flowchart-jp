# Marvel Library v5 接続意味監査（2026-09-03）

## 監査方針

接続を一つの「線」として扱わず、次の意味層を分離した。

- `R`: canonical `work_relations.csv` の明示的な作品関係
- `A`: canonical `appearances.csv` の同一entity出演から導かれる参照
- `E`: event / occurrence / transition と参加者の第一級事実
- `C`: chronology assertion（現在は未登録）
- `P`: CSV → JSON → HTMLへの表示投影

共有continuity、同じ俳優、タイトル類似、公開日だけでは新しいsemantic edgeを作らない。transitionも独立に支えられた既存pairだけを補強し、イベント含有を作品間の時系列と解釈しない。

## 全理由の処置

| domain | 完全保持 | 根拠待ち | 未 materialize | 構造fail |
| --- | ---: | ---: | ---: | ---: |
| R | 7 | 154 | 0 | 0 |
| A | 2 | 400 | 0 | 0 |
| E | 6 | 0 | 3 | 0 |
| C | 0 | 0 | 1 | 0 |
| P | 0 | 0 | 8 | 0 |
| 合計 | 15 | 554 | 12 | 0 |

「完全保持」は、事実とその evidence/reviewが確認でき、導出方向も正しいことを意味する。`R`の154件と`A`の400件は線自体を削除しないが、legacy_seed由来のため、公式根拠付きの視聴前史・後続としては未確定である。

### 完全保持として確認できた事実

- 明示的関係7件: No Way Home→Multiverse of Madness、First Steps→Doomsday、Thunderbolts→First Steps、Loki S2→Deadpool & Wolverine、No Way Home→Morbius、Inhumans→Multiverse of Madness、Logan→Deadpool & Wolverine。
- source-verified shared appearance 2件: Homecoming↔MorbiusのAdrian Toomes、Let There Be Carnage↔No Way HomeのEddie Brock。
- source-verified transition 6件: 既存pairを補強する遷移。残り3件（Monica、Earth-838、WadeのTVA）は相手側作品pairを発明せず未 materialize。

### 根拠待ちの意味

`explicit_relation` 154件は、方向と候補関係はcanonical rowに残るが、個別公式URL→evidence→reviewが未登録のlegacy_seedである。`shared_entity` 400件も同様に、出演行がlegacy_seed/unknownであり、参照線の存在は確認できても、semantic predecessorへの自動昇格はしない。これはスパイダーマン2→3、Amazing Spider-Man 1→2などの線を消す判定ではなく、根拠レベルを区別する判定である。

### variant・過剰fan-outの保留

Logan/Wolverine（`entity-x-680db112c0`）とLoki（`entity-x-55e230260e`）は、legacy appearanceの同一entity統合により複数作品へfan-outする既知のvariant監査候補である。現段階ではvariantを推測してcanonical entityを分割しない。別バッチで個体根拠と`variant_of`境界を追加し、対象edgeだけをREDテスト付きで置換する。

## 欠落候補の扱い

独立監査で、canonical事実から導出されるはずのpairの欠落は0件だった。これは「canonical factsが全作品の理想的接続を網羅している」という意味ではない。degree 0や低degreeは追加ソース監査の候補であり、タイトルやシリーズ名から勝手に関係を追加しない。

特に、旧Spider-Man作品→No Way Homeの遷移線はcomplete表示の文脈線として残るが、site-proposalでincoming weak fan-inを前史として逆伝播させない現行方針と整合する。これを変える場合は、`context`として表示するか、時系列の前史にするかを先に仕様化し、別のREDテストを置く。

## 結論

現行の「線が足りない」問題について、Spider-Man 2→3およびAmazing Spider-Man 1→2はcanonical relation・JSON・選択oracle・Chrome監査の全てで存在する。今回の完全監査で見つかった本質的な残作業は、線の自動生成欠落ではなく、legacy接続をどこまで公式根拠付きsemantic edgeへ昇格するか、ならびにvariant fan-outを個体別に精査することである。
