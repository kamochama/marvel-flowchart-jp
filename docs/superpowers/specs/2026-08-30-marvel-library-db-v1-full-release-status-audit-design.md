# Marvel Library DB v1 全作品 release/status evidence audit 設計

## 目的

現在の131作品について、正規化済み releases.csv と production_status_assertions.csv の全行を監査対象として棚卸しする。公式一次ソースまたは明示的に適格な補助ソースが個別 fact を直接支持する場合だけ legacy_seed -> source_verified を行い、根拠が不足する行は理由付きで legacy_seed のまま残す。

この作業は、既存のDB-derived graphやHTML表示を変更せずに、release/status metadataの provenance を完成させるための後続監査である。

## 適用範囲

- 対象表: data/library/releases.csv（138行）と data/library/production_status_assertions.csv（131行）。
- 現在の未昇格行: release 132行、production-status 127行（2026-08-30 main baseline）。
- 永続監査: data/library/evidence.csv、data/content_audit/reviews.csv、各バッチの data/content_audit/applied/*.json。
- 全作品を最終的な監査対象とするが、昇格単位は小さなbounded batch（原則1–5 facts、同一ソースで直接検証できるもの）に分割する。
- 同じcanonical CSVを複数エージェントが同時編集しない。読み取り専用監査は並列化し、書き込みと統合はprimary agentが直列に行う。

## 意味論上の境界

- source_verified には対応する evidence.csv 行と reviews.csv の明示的な legacy_seed -> source_verified 遷移が必須。
- source登録だけ、作品一覧への掲載だけ、または別factを支持する証拠だけでは昇格しない。
- announced と released を混同しない。将来日程や日付が過去になったことだけから公開済み・製作完了を推論しない。
- asserted_at はstatus snapshotの観測日であり、歴史的な製作マイルストーンを意味しない。
- JP行の日付がISO形式でない場合は空欄を維持し、日本公開日・territory・配信先を推測しない。
- release/status factsからwork relation、event、transition、appearance、portrayal、character identity、Earth番号を派生させない。
- evidence不足・ソース間不一致・地域境界不明の行は、明示した理由とともに legacy_seed のまま保留する。

## 監査フロー

1. 全seed行をfact ID、work、source候補、地域、日付精度、status、既存evidence/reviewの有無でインベントリ化する。
2. 読み取り専用サブエージェントをsource群ごとに分担し、各行を promote、defer、conflict のいずれかへ分類する。
3. promote 群ごとにREDテストを先に追加し、対象factが未昇格であること、必要なevidence/review ID、グラフ非変更を固定する。
4. 最小変更として対象CSV、evidence、review、applied record、累積回帰テストだけを更新する。
5. bundled Pythonでfocused test、全unit test、ordinary build、strict CSV shape、determinism、FK/integrity、graph compatibilityを確認する。
6. branch差分をレビューし、PRを通常経路でmainへ統合する。統合後にmainのfact counts、review integrity、派生graph fingerprintを再確認する。
7. defer と conflict は監査記録へ集約し、根拠が得られるまでcanonical statusを変更しない。

## 完了条件

- 131作品の全release/status factについて、昇格・保留・不一致の disposition が監査記録にある。
- 昇格行はすべて直接証拠、レビュー遷移、適用記録、回帰テストを持つ。
- 保留行は理由と再監査条件が明記される。
- audit issue、review integrity issue、FK violationが0で、SQLite integrityが ok。
- 既存graphの work_edges_all=361、work_pair_reasons=569、prewatch 199、story paths 83/83 を、変更が必要な別承認semantic workなしに維持する。
- 全バッチ完了後に引き継ぎ・ロードマップ・監査記録のbaselineを更新する。

## 非目標

- release/status metadataからのグラフ再設計。
- credits、aliases、memberships、possessions、multiverse decompositionの追加。
- index.html のUI変更、デザイン刷新、操作デバッグ。
- 根拠のない一括verified化や日本公開日の補完。
