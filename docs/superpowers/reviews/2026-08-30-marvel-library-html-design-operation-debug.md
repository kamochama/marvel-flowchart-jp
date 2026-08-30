# Marvel Library HTML design／操作デバッグ監査

## 判定

v5.20.7 の予習プランUIは、今回のデスクトップ／スマホ操作監査で **PASS** とする。公式予習ルートの出典境界、三段階の表示ルール、チャート復帰導線、視聴済み状態の更新に回帰は確認されなかった。今回の監査では正規CSV、永続レビュー台帳、DB由来の接続意味論を変更していない。

対象ブランチは `library-v5-phase2-db6`、監査時点のHEADは `0bdf389e471e1efd6756eee36f9e7c0127c4e0bd` で、対応する `origin/library-v5-phase2-db6` と一致している。

## 回帰契約

`tests/library_v5/test_watch_scroll_navigation.py` が次を固定している。

- 「最低限」はゴールへ直接入る `core` 接続だけで、再帰探索しない。
- 「おすすめ」は登録済み公式予習ルートを優先し、未登録時は編集／接続表由来であることを明示する。
- 「完全版」は中核・推奨を再帰追跡し、参照接続は直接コンテキストに限定する。
- 公式ルートの出典URL、確認日、`source_verified` 境界が静的JSONへ輸出される。
- 公式ルートの既存ノード・既存エッジだけを一時的に緑色で強調し、詳細再描画後も再適用できる。
- 予習プランを開いてもチャートをDOMから隠さず、`↑ チャートへ戻る` の導線を保持する。

## 実画面スモーク結果

ローカル静的サーバー（`127.0.0.1:8765`）で確認した。

### デスクトップ（1280px幅）

- 初期ステータスは「データを読み込みました（131作品）。」。
- `最低限 → おすすめ → 完全版` の切替で、チャート側と予習プラン側のラベルが同期した。
- 『アベンジャーズ／ドゥームズデイ』と『サンダーボルツ*』を複数ゴールにすると、出典表示は `公式＋編集ルート` となり、公式URLと確認日が表示された。
- 「公式予習ルートをチャートで光らせる」を押すと、既存の公式ルートについて `4` エッジ、`3` ルートノードが強調された。新しい作品ペア／グラフエッジは生成されなかった。
- 「↑ チャートへ戻る」で `public-watch-view` と `mobile-watch-in-view` が解除され、チャート表示へ戻った。公式ハイライト状態は維持された。
- 視聴済みチェックは行の `is-watched` 状態と進捗表示を更新し、「このプランだけチェック解除」で元に戻った。

### スマホ（393×873）

- 作品タップでモバイルのゴールバーが作られ、「予習プランを見る」で予習プランへ移動した。
- 予習プランから「↑ チャートへ戻る」でチャートへ復帰し、ゴール選択を保持した。
- 予習プラン表示中もチャート要素をDOMから削除せず、上下スクロールで相互に移動できた。

## フル検証

Bundled Codex Python runtime で次を実行した。

```powershell
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
git diff --check
```

結果:

- `Ran 318 tests ... OK`
- `audit_issue_count=0`
- `content_audit.issue_count=0`
- SQLite foreign-key rows `0`
- `integrity_check=ok`
- `works=131`, `releases=138`, `production_status_assertions=131`
- `work_edges_all=361`, `work_pair_reasons=569`
- flowchart export `nodes=131`, `edges=361`, `reasons=569`
- 生成された一時監査／DB出力を削除後、`git status --short --branch` は clean

## 境界と次の扱い

今回の対象はHTMLのデザイン／操作デバッグのみであり、release/status の未監査行、credits、aliases、memberships、possessions、追加の公式ルート登録は開始していない。ブラウザシナリオは実画面で確認済みだが、現行の回帰テストは静的契約中心で、ヘッドレスDOM操作を自動化するものではない。自動ブラウザ回帰を追加する場合は、別のUI計画とテスト実行環境を定めてから着手する。

この監査はブランチ上の確認記録であり、`main` へのマージやGitHub Pagesへの公開を意味しない。
