# Marvel Library 予習範囲・ルート表記 同期レビュー

## 判定

既存のHTML変更（`9dc56c0`）に合わせた当時の公開READMEと監査記録の同期結果である。後続の3モード分離（`2026-08-30-marvel-library-prewatch-three-modes.md`）により、予習プランの2択契約は現在の根拠ではない。

旧レビュー `2026-08-30-marvel-library-html-design-operation-debug.md` にある三段階UIの記述と本レビューは履歴として保持する。現在の挙動を説明する根拠には、後続レビューと `tests/library_v5/test_watch_scroll_navigation.py` を使用する。

## 現行UI契約

- チャートの `関連全体` は従来の有向探索を維持する。
- `1つ前のみ` は選択作品への incoming edge（直接前史）だけを点灯し、outgoing edge（後続）を追加しない。
- 予習プランの `おすすめ` は、登録済み公式予習ルートを優先し、未登録時はサイト提案ルート／接続表由来であることを示す。
- `完全版` は中核・推奨の前史を再帰的に追跡し、参照接続は直接コンテキストとして扱う。
- 旧 `minimum` 値は共有状態の後方互換読み込み用に内部へ残すが、公開HTMLの選択肢には出さず、読み込み時は `recommended` へ正規化する。
- 公式予習ルートのハイライト、視聴済みチェック、予習プランからチャートへ戻る導線は変更していない。

## データ境界

今回の変更は表示ラベルと選択範囲のUI制御だけであり、正規CSV、永続レビュー台帳、DBの接続意味論、作品ペア、公式ルートの出典URLは変更していない。`data/derived/flowchart.json` はDBマニフェストの現在の論理フィンガープリントに合わせて再生成された派生物である。

## 検証

- README現行セクションの用語チェック：旧公開選択肢・旧編集ルート表記なし。
- `tests.library_v5.test_watch_scroll_navigation`：17 / 17 PASS。
- bundled Python full suite：322 tests、`OK`。
- ordinary build：終了コード0、`audit_issue_count=0`、`content_audit.issue_count=0`。
- DB/互換性観測値：`works=131`、`releases=138`、`production_status_assertions=131`、`work_edges_all=361`、`work_pair_reasons=569`、`prewatch_edges=199`、`story_paths=83/83`。
- ビルド後の既知の監査・DB一時生成物と `__pycache__` は削除し、カノニカルCSVと `reviews.csv` は保持した。

このレビューは機能ブランチ上の記録であり、`main` へのマージ、push、GitHub Pages公開を意味しない。
