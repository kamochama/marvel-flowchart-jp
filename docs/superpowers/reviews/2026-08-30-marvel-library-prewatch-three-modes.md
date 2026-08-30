# Marvel Library 予習プラン3モード分離レビュー

## 判定

予習プランの公開選択肢を、`公式予習ルート`、`サイト提案ルート`、`完全版` の3つへ分離した。公式ルート未登録時のサイト提案への無言フォールバックを廃止し、チャートの接続重要度セレクタも予習プランのモード状態から分離した。

## 現行UI契約

- `公式予習ルート`: `prewatch_official_routes.json` に登録され、出典URL・確認日・`source_verified` を持つルートだけを表示する。未登録のゴールは空の予習候補と未登録メッセージを表示し、サイト提案へ自動切替しない。
- `サイト提案ルート`: 公式ルートを参照せず、監査済みのサイト提案ルートと接続重要度 `core` の前史を表示する。
- `完全版`: 接続データの `core` / `recommended` を再帰的に辿り、ゴールへ直接入る `reference` だけを補助的に加える。公式／サイト提案ルートの出典や順序を混ぜない。
- 旧 `minimum` / `recommended` の共有状態は `site-proposal` として読み込む。新しい共有状態は3モードの値を送受信する。
- チャートの「おすすめ／完全版」は接続重要度の表示設定であり、予習プランの3モードとは独立している。

## データ境界

正規CSV、永続レビュー台帳、release/status facts、接続の意味論は変更していない。`data/prewatch_policy.json`、`data/README.md`、`data/rules.csv`、`data/schema.json` は3モード契約へ同期し、`data/manifest.json` のハッシュを更新した。完全版のroute混入を防ぐため、実行時plannerだけを変更している。

## 回帰テスト

`tests/library_v5/test_watch_scroll_navigation.py` に次を追加した。

- 予習セレクタが `official` / `site-proposal` / `complete` の3値だけを公開すること
- 公式モードがサイト提案へフォールバックしないこと
- サイト提案モードが公式routeを使わないこと
- 完全版がgraph recursionと直接referenceだけを使い、route metadataを混ぜないこと
- 旧共有値の正規化と、チャート接続セレクタの独立性
- サイト提案の経路説明から `reference` 接続を除外すること
- 公式ルートのハイライトを公式モード外で解除すること

## 検証

- watch navigation contract: 25 / 25 PASS
- bundled Python full suite: 334 / 334 PASS
- ordinary build: 終了コード0、`audit_issue_count=0`、`content_audit.issue_count=0`
- 互換性観測値: `prewatch_edges=199`、`story_paths=83/83`
- DB観測値: `works=131`、`releases=138`、`production_status_assertions=131`

このレビューは作業ブランチの変更記録であり、push・PRマージ・GitHub Pages公開を意味しない。
