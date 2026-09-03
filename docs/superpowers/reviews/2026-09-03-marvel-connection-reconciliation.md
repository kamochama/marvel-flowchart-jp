# Marvel Library v5 接続監査・所見統合（2026-09-03）

## 三つの監査の一致

1. **canonical意味層**: R/A/E/Cを独立にたどると、現行正本から導出されるpairの欠落は0。legacy_seedの関係・出演を「根拠済み」とは扱わず、variantや個別ソースが必要なものを保留した。
2. **派生層**: SQLite、CSV、JSONのpair/reason parityは完全一致。relation/appearance/transitionの方向を導出器が取り違えた構造的失敗は0。
3. **UI層**: 現行JSONに対する131作品×2 tierのDOM監査、PC操作監査、chronology/publication監査は成功。選択はedge追加・削除ではなく既存edgeの再描画に限定される。

## 処置の境界

| 処置 | 対象 | 今回の動作 |
| --- | --- | --- |
| retain | source_verifiedで同一pair・方向・根拠が揃う15理由 | 現状維持 |
| needs-source | legacy explicit_relation 154、legacy shared_entity 400 | 線は保持、公式根拠付き昇格待ち |
| defer | transition未materialize 3、chronology未登録1、degree 0作品8 | 推測追加しない |
| canonical-fix | 構造fail | 0件 |
| derivation-fix | export mismatch / orphan / unsupported transition | 0件 |
| explicit-conflict | 現行接続の明示的衝突 | 0件 |
| presentation-only | publication/chronology/prewatchの表示政策 | semantic edgeと分離 |

## 修正バッチの提案

今回の監査ではcanonical CSVやHTMLを変更しない。次の変更はそれぞれ別の承認・REDテスト・evidence/reviewを持つ。

- variant audit: Logan/WolverineとLokiの個体境界を一次根拠で確認し、必要なら`variant_of`を追加する。
- source promotion: 高優先のexplicit relation/appearanceを、作品固有公式URL→evidence→reviewの順で昇格する。
- semantic policy: No Way Home等の遷移incomingをsite-proposalで`context`として見せるか、前史として見せるかを仕様化する。

いずれも「線が足りない」という理由だけで連続作品・同一タイトル・同じ俳優から一括生成しない。
