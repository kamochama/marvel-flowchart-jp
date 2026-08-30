# Marvel data master — v4 foundation / prewatch tiers (v5 provisional UI policy)

更新日: 2026-08-30

GitHubで管理する正本データです。Excelは通常生成しません。

## v4 の中心変更

`connections.csv` に **prewatch_tier** を追加しました。

- `minimum` = 最低限
- `recommended` = おすすめ
- `complete` = 完全版
- `none` = 予習対象外

従来の `importance=core/recommended/reference` と `prewatch_tier` は監査・互換性のために保持します。現行v5公開UIの仮ルールは `importance` と明示的な予習ルート由来を使います。

## 探索規則

- 最低限: ゴールへ直接入る中核接続のみ（再帰なし）
- おすすめ: 公式予習リストを優先し、公式予習リストが未登録なら監査済み編集ルートを代替表示。中核の前史を補完
- 完全版: 中核・推奨を再帰探索し、ゴールへ直接入る参照接続も追加（参照を踏み台にしない）

これは現行公開UIの仮運用です。公式の作品別予習リストは根拠URLと監査レビューが登録されたものだけを「公式」と表示し、未登録の作品は編集ルートまたは接続表由来であることを明示します。

公式ルートの登録本体は `prewatch_official_routes.json`、探索規則の詳細は `prewatch_policy.json` です。公式ルートはビルド時に静的 `flowchart.json` の表示ポリシーへ取り込まれます。

## 大事な分離

- `story_groups.csv` / `story_members.csv`: 同じ世界線・系列に置くための分類
- `story_paths.csv`: ③で連続線を描く83 edgeのwhitelist
- `connections.csv`: 一般の作品関係199 edge＋予習tier
- `entity_returns.csv`: キャラクター帰還proxyの根拠

**同じ系列にいること、時系列で線を引くこと、予習で必要なことは3つとも別概念です。**

## v4重点再監査

- `No Way Home -> Brand New Day`: minimum。Sony公式が4年後の同一Peterの新章と明記。
- `WandaVision / Agatha -> VisionQuest`: minimum。Marvel公式が3作のtrilogyと明記。
- `Age of Ultron -> VisionQuest`: recommended。Ultron/Vision起点の理解用。
- `Fantastic Four: First Steps -> Doomsday`: minimum。Kevin Feigeがdirectly leads intoと明言。
- `Thunderbolts* -> Doomsday`: minimumへ昇格。Marvel Japanが参戦決定・重要なターニングポイントと案内。
- `Doomsday -> Secret Wars`: minimum。公式案内上のAvengers 2部作。
- Doomsdayの13作品レンタル企画由来edge: complete。公式関連作だが直接前提にはしない。
- `She-Hulk -> Brand New Day`: recommendedへ。公開後Sony公式でHulkが大きく関与。
- `Thunderbolts* -> Brand New Day`: recommendedへ。公開後脚本家取材でYelenaの主要参加を確認。

## 構造

- 作品: 131
- 接続: 199
- 時系列メタ: 103
- ③連続線: 83
- prewatch tier: minimum 93 / recommended 72 / complete 34 / none 0
