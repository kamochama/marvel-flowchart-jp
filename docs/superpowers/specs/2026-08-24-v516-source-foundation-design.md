# PUBLIC v5.16.0 Source Foundation Design

## 目的

PUBLIC v5.15.0 で成立した機能・データ・操作を一切変えず、今後の v5.17 以降を安全に開発できる正本ソース構造へ移行する。

v5.15.0 の現行ビルドは、凍結した PUBLIC v5.14.1 HTML を `src/baseline/` から再構成し、`scripts/build_public.py` が文字列置換と `src/v515/` の CSS / JavaScript / JSON 注入を行って単一 `index.html` を生成する。この方式は v5.15.0 の再現性には有効だが、版ごとの後付けパッチを増やし続ける構造にはしない。

v5.16.0 は機能追加版ではなく、**現在のアプリそのものを編集可能な正本へ昇格する移行版**とする。

## 設計原則

1. **意味を変えない。** v5.15.0 の作品・接続・人物リンク・探索・予習・詳細・特集・共有・PC/スマホ操作を回帰基準とする。
2. **一方向ビルドにする。** 正本ソースから公開 `index.html` を生成し、既存の公開 HTML を入力として継ぎ足さない。
3. **データと表示コードを分ける。** 作品関係データ、表示設定、UI/ランタイムを独立して変更・検査できるようにする。
4. **新しいフロントエンド基盤を導入しない。** npm、SPA フレームワーク、常時必要な外部ビルドサービスは追加しない。GitHub Pages で単一 HTML を配布する現在の性質を維持する。
5. **履歴を捨てない。** `src/baseline/` と `src/v515/` は v5.14.1 / v5.15.0 の再現・回帰用資料として残し、v5.16.0 の通常ビルド入力から外す。
6. **移行は parity gate を通してから切り替える。** 新旧ビルドの意味的一致を機械検証できるまで本番生成経路を変更しない。
7. **正本を二重化しない。** v5.16.0 切替後、作品・接続・人物リンク・詳細・特集設定の値は新しい `src/data/` / `src/config/` にだけ保持し、`shell.html` や runtime へ同じ値を手作業で複製しない。

## 目標ソース構造

v5.16.0 の正本は次の責務に分離する。

```text
src/
  app/
    shell.html
    styles/
      manifest.json
      *.css
    runtime/
      manifest.json
      *.js
  data/
    works.json
    edges.json
    people-links.json
    work-details/
      manifest.json
      part-*.json
  config/
    overview-groups.json
    group-labels.json
    featured-route.json
  baseline/                 # v5.14.1 再現専用
  v515/                     # v5.15.0 回帰専用
scripts/
  build_public.py
```

`styles/manifest.json` と `runtime/manifest.json` が組み込み順を唯一決定する。JavaScript の既存グローバル依存を無理に ES modules 化せず、現行の実行順を保持したまま責務単位へ抽出する。

### `src/app`

表示・操作を担当する。作品や接続の事実そのものを JavaScript 本体へ重複埋め込みしない。

- ページ骨格
- PC / スマホ UI
- SVG / Canvas 描画
- 検索
- 詳細フォーカス
- OR / AND / PATH
- 予習プラン
- 視聴済み状態
- 特集プレビュー
- Shared Room クライアント

`src/app/shell.html` は静的なページ骨格だけを持ち、作品131件等の可変データ配列を正本として保持しない。

### `src/data`

相関図の意味を担当する。

- `works.json`: 作品メタデータ 131件
- `edges.json`: 有向接続 199件
- `people-links.json`: 人物リンク 155件
- `work-details/`: 131作品分の `synopsis_ja` と `map_role_ja`

v5.16.0 ではこれらの内容を変更しない。ID、接続向き、importance、strength、表示文言等に移行都合の修正を混ぜない。

### `src/config`

相関関係そのものではなく、公開表示の編成を担当する。

- `overview-groups.json`: 主要フローのグループと所属
- `group-labels.json`: グループの見出し・説明
- `featured-route.json`: 現在の `FEATURED_ROUTE` 相当

これにより v5.17 以降の UI 改善や、その時点の注目作への特集差し替えをランタイム本体から分離する。

## ビルド方式

`scripts/build_public.py` は v5.16.0 では次の一方向処理にする。

1. `src/app/shell.html` を読む。
2. `src/data/` と `src/config/` を schema / 参照整合性検証する。
3. JSON から決定的な公開 payload を生成する。
4. `styles/manifest.json` の順で CSS を組み込む。
5. overview SVG 等、生成が必要な部分を既存 Python 生成器で生成する。
6. `runtime/manifest.json` の順で JavaScript を組み込む。
7. `PUBLIC v5.16.0` の単一 `index.html` を出力する。

ビルドはネットワークアクセス不要・入力固定・決定的とする。同一コミットから同一バイト列を生成できることを要求する。

通常ビルド経路で `src/baseline/` または `src/v515/` を参照した場合はテスト失敗とする。これらを読むことが許されるのは、明示的な legacy / compatibility 回帰テストだけである。

## 移行戦略

### Phase 1 — v5.15.0 の正確な抽出

現在 GitHub Actions が生成している PUBLIC v5.15.0 を基準に、ページ骨格、スタイル、ランタイム、データ、設定を新しい責務境界へ抽出する。

回帰 oracle は main commit `d88bfecd4df7d2ccc70a4efd5b2f90614398722e` の成功した公開 run `32651303970` と、既存 v5.15.0 監査ハッシュとする。

この時点では現行 `build_public.py` を本番経路として残す。

### Phase 2 — 独立した互換ビルド

新しい正本から PUBLIC v5.15.0 相当を生成する compatibility build を用意する。

静的出力は可能な限りバイト単位で比較する。生成順・整形による差が残る箇所は、DOM構造、埋め込みデータ、公開関数、イベント配線、意味ハッシュを比較する。

compatibility build は移行確認専用であり、v5.16.0 切替後の通常 Pages 配布には使わない。

### Phase 3 — parity gate

新旧ビルドの両方に既存回帰試験を実行し、下記の不変条件が一致することを確認する。差分が1つでもある間は通常ビルドを切り替えない。

### Phase 4 — v5.16.0 へ切り替え

新正本ビルドを通常の `scripts/build_public.py` にし、公開版表記を v5.16.0 へ更新する。

旧 `src/baseline/` / `src/v515/` は回帰・復旧用として保持するが、新通常ビルドの依存関係には含めない。

## 必須回帰条件

v5.16.0 は少なくとも以下を PUBLIC v5.15.0 と一致させる。

- 作品: **131**
- 有向接続: **199**
- 人物リンク: **155**
- 主要フロー: **76作品**
- 主要フローグループ: **5区分**
- 作品詳細: **131 / 131**
- OR: **8,515組** — FNV-1a 64 `9c38afad0f8ac3fe`
- AND: **8,515組** — FNV-1a 64 `ad48d8c46ae1bd61`
- PATH: **8,515組** — FNV-1a 64 `8b9847fcda5cdf96`
- 単一ゴール予習: **393パターン** — FNV-1a 64 `a3c6f1c12199a903`
- `ニュー・ミュータント`: 表示上の架空直接接続を追加しない
- 左クリック / タップ: 詳細フォーカスであり、ゴール集合を変更しない
- 検索結果選択: 詳細フォーカスであり、ゴール集合を変更しない
- PC右クリック: ゴール追加 / 解除
- 詳細 CTA: ゴール追加 / 解除
- 複数ゴール OR / AND / PATH
- 視聴済みチェックと未視聴時間計算
- 特集プレビューと特集からのゴール追加
- Shared Room ダイアログと既存クライアント契約
- スマホ overview Canvas: 76作品
- スマホ: 1本指パン / 2本指ズーム / タップ詳細
- PC / スマホ: page script errors 0

既存 v5.15.0 の意味ハッシュを回帰 oracle としてそのまま固定し、v5.16.0 で値を取り直して基準を緩めない。

## テスト設計

### 1. Source-boundary tests

- 通常ビルドが `src/baseline/` を入力として読まない。
- 通常ビルドが `src/v515/` を入力として読まない。
- version-specific な巨大文字列置換で機能を注入しない。
- CSS / JavaScript の読み込み順は manifest だけで決まる。
- `src/data` / `src/config` の重複 ID、欠落 ID、壊れた参照を検出する。
- `shell.html` / runtime に作品・接続・特集設定の第二正本を作らない。

### 2. v5.15 compatibility tests

移行中、新正本から生成した互換版と現 v5.15.0 を比較する。抽出漏れ・注入順違い・イベント配線漏れを検出する橋渡しテストとする。

### 3. Semantic regression tests

既存の OR / AND / PATH / 予習 / overview / 詳細 / interaction smoke を、新ビルド出力に対してそのまま通す。

### 4. Deterministic build test

同一 checkout で公開ビルドを2回行い、生成 `index.html` の SHA-256 が一致することを検査する。

### 5. Release contract tests

公開 ZIP / Pages artifact は従来どおりルート直下6ファイル固定とする。

- `index.html`
- `README.md`
- `AUDIT.md`
- `AUDIT.json`
- `preview.png`
- `.nojekyll`

GitHub Pages Direct Deploy の仕組みは変更しない。

## 失敗時の扱い

- parity gate 不一致は「許容差分」として流さず、原因を特定する。
- UI上の改善に見える差分でも v5.16.0 には混ぜない。v5.17.0 候補として分離する。
- データ上の誤りを発見しても v5.16.0 の構造移行と同じコミットで直さない。v5.18.0 の接続監査へ送る。
- Shared Room の問題を発見しても Worker 契約を v5.16.0 で変更しない。v5.19.0 候補として記録する。

## ロールバック

v5.16.0 は1本の機能ブランチ / PR で main へ統合する。公開後に回帰が見つかった場合、v5.16.0 PR を revert すれば PUBLIC v5.15.0 の生成経路へ戻れることを保つ。

v5.15.0 の最後に検証済みとなった GitHub Actions 公開 artifact と回帰ハッシュを復旧基準として保持する。

## v5.16.0 では行わないこと

- 作品の追加・削除
- 199有向接続の追加・削除・意味変更
- 人物リンクの変更
- あらすじや `map_role_ja` の内容改訂
- スマホの新エリアナビ UI
- 特集ルートの内容変更
- 接続根拠の全面監査
- Shared Room Worker の仕様変更
- GitHub Pages / Actions 配布方式の再設計
- npm / React / Vue 等の新規導入

## 次版への接続

v5.16.0 完了後は、新正本構造の上で次の順序を想定する。

1. **v5.17.0 — スマホ主要フロー2.0**: 5大エリアへの軽量ジャンプ / 現在地把握を改善。
2. **v5.18.0 — 接続根拠の完全監査**: 199有向接続の根拠・出典・種別を説明可能なデータへ整理。
3. **v5.19.0 — Shared Room安定版**: 再接続、参加・退出、共有リンク、複数人同期を本格監査。
4. **以降 — 公開情報更新**: `featured-route.json` を中心に、Doomsday / Secret Wars などその時点の注目作へ安全に更新。

## 完了条件

v5.16.0 は以下をすべて満たした時だけリリース可能とする。

1. 通常ビルドが `src/app` / `src/data` / `src/config` だけを正本として `index.html` を生成する。
2. `src/baseline/` と `src/v515/` が通常ビルド依存から外れている。
3. v5.15.0 の全意味回帰条件と固定ハッシュが一致する。
4. deterministic build test が PASS する。
5. PC / スマホ interaction smoke が全て PASS する。
6. GitHub Actions の build / verify / Pages deploy が成功する。
7. 配布 artifact が固定6ファイルだけを含む。
8. `AUDIT.md` / `AUDIT.json` が v5.16.0 の構造移行と回帰結果を記録する。
9. v5.16.0 に機能・データ変更が混入していないことを PR diff で確認する。
10. main へ統合後、commit status `marvel-pages` が success であることを確認する。
