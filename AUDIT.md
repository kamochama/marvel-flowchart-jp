# マーベル作品相関図 日本版 — PUBLIC v5.17.8 監査

監査日: 2026-08-24  
基準版: PUBLIC v5.15.13  
候補版: PUBLIC v5.17.8 prewarmed world overlay

## 結果

**5ビュー公開ナビゲーション: PASS（静的回帰）**  
**② RELEASE_META 131 / 131: PASS**  
**② 歴史表示: 7時代セクション / 7歴史マーカー / 最大SVG横幅1320: PASS（コード契約）**  
**関係地図（v5.15.13）バイト不変: PASS**  
**作品131 / 有向接続199 / 人物リンク155 / 詳細131: PASS**  
**inline JavaScript 16本 構文エラー0: PASS**  
**ゴール高速経路に refreshSelection(false) / rebuildMobileCanvas 再導入なし: PASS（静的回帰）**  
**固定6ファイルZIP構成: PASS**

v5.17.2では公開順専用メタデータを維持したまま、②の見せ方を再設計した。全期間を1本の巨大な横長タイムラインへ置く方式を廃止し、歴史時代ごとにX軸をリセットしたセクションを縦方向へ連結する。時代名は公式区分ではなく、企業・制作体制・配信構造の転換点を一次資料優先で整理した編集上の歴史区分である。

歴史マーカーは、2005年Marvel自社製作資金、2009年DisneyによるMarvel取得、2013年Marvel/Netflix大型TV展開、2015年Sony×Marvel Studios協業、2019年Disneyによる21st Century Fox取得、2019年Disney+開始、2021年Marvel Studios初のDisney+シリーズを採用。

この実行環境ではChromium headlessがDBus/zygote周辺でタイムアウトするため、v5.17.2のfreshな実ブラウザ画像検証は完走していない。v5.17.0で確認済みのPixel 6相当高速経路実測値は継承資料として保持するが、v5.17.2のfresh実測とは扱わない。

## 主要フロー

- 主要フローを63作品から76作品へ拡張。
- 20世紀FOX版X-MEN／ウルヴァリン／デッドプール13作品を `FOX X-MEN UNIVERSE` として統合。
- X-MEN群の表示接続は既存199有向接続からのみ抽出し、表示都合の新規接続は追加していない。
- `ニュー・ミュータント` は主要フロー内に表示するが、直接接続0の独立作品として維持。
- グループを `MCU / INFINITY SAGA`、`MCU / MULTIVERSE SAGA`、`DISNEY+ / TV`、`FOX X-MEN UNIVERSE`、`ANIMATION / SPECIAL` の5区分に整理。
- 各グループは大きい見出し、1行説明、強調した枠を持ち、全体表示でも領域を判別しやすくした。
- PC SVGとスマホCanvasで同じ76作品を描画することを確認。

## 作品詳細

- 131 / 131作品に `synopsis_ja`（あらすじ）と `map_role_ja`（相関図では）を登録。
- あらすじは作品ごとの短い独自要約とし、結末・重大な正体・主要な退場などを避けた予告編／公式紹介レベルに統一。
- 未公開8作品は公式発表範囲だけを扱い、未発表部分を推測で補完しない。
- 詳細データの空欄、危険なHTML文字列、機械的な重複を検査。
- 詳細欄の順序は `作品名 → あらすじ → 相関図では → ゴール操作 → 前後候補 → 詳細情報`。
- PC右パネルでは従来の詳細表示を維持し、スマホでは同じ `synopsis_ja` / `map_role_ja` を予習プラン内に展開する。

## 操作体系

- PC左クリック: 関連ラインを一時表示し、右側の作品詳細も同時更新する。ゴール集合は変更しない。
- スマホタップ: v5.14系のゴール選択経路へ戻し、選択作品をゴールとして前史・後続の接続を点灯する。再タップで解除、別作品タップで切り替える。
- スマホ検索結果選択: 同じゴール選択経路へ入り、検索からでも接続表示へ直行する。
- スマホ作品詳細: チャート上の詳細シート操作を隠し、予習プラン各行の `詳細を見る` であらすじ・相関図上の役割をインライン展開する。
- PC右クリック: 対象作品だけをゴールへ追加 / 解除するショートカット。
- 詳細欄: `🎯 ゴールに追加` / `ゴールから外す` を正規操作として表示。
- 既存ゴールがある状態で別作品を詳細表示してもゴール集合を保持し、`ゴール表示に戻る` でOR / AND / PATH表示を復元。
- 表示優先順位を `特集プレビュー → 詳細フォーカス → ゴール表示 → 全点灯` とし、一時表示終了後は直下の状態へ復帰。
- 特集 `ゴールに追加` ボタンも新しいゴール専用APIへ接続し、詳細表示と混同しないことを確認。

## データ・意味回帰（v5.14.1 比較）

- 作品: 131 — 一致
- 有向接続: 199 — 一致
- 人物リンク: 155 — 一致
- OR: 8,515組 — 完全一致（FNV-1a 64: `9c38afad0f8ac3fe`）
- AND: 8,515組 — 完全一致（FNV-1a 64: `ad48d8c46ae1bd61`）
- PATH: 8,515組 — 完全一致（FNV-1a 64: `8b9847fcda5cdf96`）
- 単一ゴール予習: 393パターン — 完全一致（FNV-1a 64: `a3c6f1c12199a903`）

## 操作スモーク

- PC左クリック詳細表示 / ゴール非変更: PASS
- スマホタップ → 旧ゴール選択関数へ委譲: PASS（コード契約）
- 予習プラン各作品のインライン詳細UI: PASS（コード契約）
- スマホのチャート詳細ボタン非表示: PASS（CSS契約）
- PC横詳細パネル維持: PASS（コード契約）
- PC右クリックゴール追加 / 解除: PASS
- 複数ゴールへの追加が置換ではなく加算: PASS
- 詳細欄CTAによる追加 / 解除: PASS
- 詳細フォーカスからゴール表示復帰: PASS
- 特集プレビュー → 詳細フォーカス復帰: PASS
- 特集 `ゴールに追加`: PASS
- 最後のゴール全解除 → 全点灯: PASS
- スマホCanvas overview 76作品: PASS
- Shared Room ダイアログ: PASS
- 全inline JavaScript構文検査: PASS
- 実機ブラウザ最終確認: Pixel 6で要確認

## ソース・ビルド

- GitHub管理用にPUBLIC v5.14.1の基準HTMLをUTF-8境界で14分割し、manifestでSHA-256を固定。
- `--baseline-only` 再構成はv5.14.1と1バイト単位で一致（SHA-256 `1d3d57aaba730740f8aad78351806fc3cdbbd8d07cc91a5f82bed6ab10a2fdad`）。
- v5.15.0の詳細データ・スタイル・ランタイム・主要フロー生成は小さいソースとして分離し、ビルド時に単体 `index.html` を生成。
- 現在の公開運用は `main` ルート直下の固定6ファイルをGitHub Pagesから直接公開する方式。旧GitHub Actionsビルドは公開経路として使用しない。

## 配布条件

GitHub Pages用ZIPはルート直下6ファイル固定:

- `index.html`
- `README.md`
- `AUDIT.md`
- `AUDIT.json`
- `preview.png`
- `.nojekyll`

READMEは一般利用者向けの短い説明のみとし、内部実装・監査数値は `AUDIT.md / AUDIT.json` に分離する。


## v5.15.5 追加監査

- チャート `最低限 / おすすめ / 完全版` と予習プランの双方向同期: PASS
- 既定値「おすすめ」の一致: PASS
- SVGラベル内の可視 `\n` 76件を複数行表示へ変換: PASS


## v5.15.5 追加監査

- スマホ右上「操作」撤去: PASS
- チャート上の左寄せつながりプルダウン: PASS
- 予習プラン側プルダウンとの共通状態同期: PASS
- 既定値「おすすめ」: PASS


## v5.15.5 接続基準回帰修正

- 原因: `directedPartAll()` の再帰探索が `importanceMode` を無視し、strong / very strong 接続を全モードで再帰していた。
- 修正: 再帰条件に `importanceAllowed(e)` を追加。
- 完全版の既存挙動維持: PASS
- 最低限 / おすすめが探索段階から絞られること: PASS
- 代表回帰モデル（Avengers: Endgame）: 最低限 8 / おすすめ 46 / 完全版 48


## v5.15.6 地図型概要チャート

- 概要チャート76作品: 維持
- 概要チャート77接続: 維持
- 各作品のホームエリア重複: 0
- 7エリア＋中央合流帯: PASS
- 全131作品 / 199接続 / 155人物リンク / 131詳細: v5.15.5と完全一致
- inline JavaScript 16本の構文検査: PASS
- 今回は配置のみの試作。接続線の簡略化・束ね方は未変更。


## v5.15.7 全131作品ホームマップ

- 主要76作品のSVGノード断片: v5.15.6とバイト単位で一致
- 追加作品: 55
- 全体地図の作品数: 131
- 主要接続: 77（v5.15.6から維持）
- 補助作品に触れる追加接続: 67
- 全体地図上の接続グループ合計: 144
- 7ホームエリア: 維持
- 追加ノード重複: 0
- 作品データ131 / 有向接続199 / 人物リンク155 / 詳細131: v5.15.6と完全一致
- 主要作品の地図座標・サイズ: 変更なし
- 補助作品は小型カード化し、OPTIONAL / APPENDIX / LEGACY-SUPPLEMENTは破線・低強度表示


## v5.15.8 エリア跨ぎ線の束ね

- 全体地図ノード: 131
- 全体地図接続グループ: 144
- 束ね対象: 39接続 / 7エリア対
- 非束ね接続: 105（ジオメトリ維持）
- 主要76作品ノード: v5.15.7 と完全一致
- NODES 131 / EDGES 199 / CHAR_LINKS 155: v5.15.7 と完全一致
- inline JavaScript 16本: 構文エラー 0
- SVGテキストの可視 `\n`: 0
- ルーティング: 地区間の空きスペースを共通レーンとして使う直角型 collector routing


## v5.15.10 ゴール解除の軽量化

- モバイル1件解除: Canvas即時再描画 → full refreshを2 requestAnimationFrame後へ遅延
- モバイル全解除: overlay即時消去 → full refreshを遅延
- 選択変更ごとの `tagEdgeImportance()`: 削除
- 選択変更ごとの `enhanceEdgeTooltips()`: 削除（初期化時1回）
- `applyWatchedDimming()` の重複呼び出し: 削除
- v5.15.8 全体地図SVG: 完全一致
- NODES / EDGES / CHAR_LINKS / WORK_DETAILS: v5.15.8と完全一致


## v5.15.10 ゴール横スクロール安定化

- ゴール欄の全 innerHTML 再生成: 廃止（初期骨格生成のみ）
- ゴールチップ: ID単位の差分更新
- 横スクロール位置 scrollLeft: 維持
- pointer / 慣性scroll中の重い refreshSelection: 延期
- ゴール追加・解除直後のゴール欄: 即時更新
- v5.15.9の地図SVG・作品/接続/人物/詳細データ: 完全一致

## v5.15.11 既存ゴール選択の軽量化 / 新規ゴール左寄せ

- 原因: `focusGoal(id)` がゴール集合不変でも `refreshSelection(false)` を同期実行していた。
- モバイル既存ゴール選択: `selected` と current-goal 表示のみ更新し、`refreshSelection()` / `computeSelectionState()` を呼ばない。
- Canvas: 既存の `selectionStateCache` を再利用してオーバーレイのみ再描画。
- ゴール欄: 表示順のみ newest-first。`selectedIds` の挿入順は維持。
- 新規チップ追加時: `scrollLeft=0` で左端に表示。
- TDD回帰テスト: `tests/test_v51511_goal_focus.py` RED → GREEN。

## v5.15.12 スマホ新規ゴール追加のフリーズ対策

- 原因: モバイルでゴール追加直後に `queueMobileFullSelectionRefresh()` が90ms後の `refreshSelection(false)` を予約していた。これが選択UI/SVG側の重い後追い更新の起点になっていた。
- 修正: モバイル新規ゴール追加経路から遅延フル更新を廃止。選択状態計算・ゴールバー差分更新・Canvas選択オーバーレイ描画のみで追加処理を終了する。
- 予習プラン: ゴール追加時には再生成せず dirty とし、「予習プランを見る」で `updatePreparationPlan()` とPATH説明を1回だけ更新する。
- Pixel 6相当 412×915 headless Chromium最終確認: v5.15.11 は追加後に `refreshSelection=1`、v5.15.12 は500ms後も `refreshSelection=0 / rebuildMobileCanvas=0`。
- v5.15.12 の3ゴール連続追加では各同期処理は約8〜13ms、追加中 `refreshSelection=0 / rebuildMobileCanvas=0 / updatePreparationPlan=0`。予習プラン表示時のみ `updatePreparationPlan=1`。
- ブラウザ pageerror: 0。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131はv5.15.11とバイト一致。埋め込みSVG 7枚も完全一致。
- inline JavaScript 16本: 構文エラー0。

## v5.15.13 スマホゴール削除のフリーズ対策

- 原因: モバイル1件削除と「すべて解除」にだけ `queueMobileFullSelectionRefresh()` が残り、90ms後の `refreshSelection(false)` → SVG変更 → Canvas再構築を起こしていた。
- 修正: 1件削除・全解除とも遅延フル更新を廃止。選択状態／ゴールバー／Canvasオーバーレイだけ即時更新し、予習プラン・PATH説明は dirty として表示時に更新する。
- Pixel 6相当 412×915 headless Chromium比較: v5.15.12 は1件削除後500ms以内に `refreshSelection=1 / rebuildMobileCanvas=1`、v5.15.13 は `0 / 0`。
- v5.15.13 1件削除同期処理: 約7ms。全解除同期処理: 約4ms。ブラウザ pageerror: 0。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131、埋め込みSVGはv5.15.12から変更なし。

## v5.16.0 Stage A — 5ビューシェル

- PC公開タブ: `① 関係地図 / ② 公開順 / ③ 世界線・時系列 / ④ この作品を見るなら / ⑤ 人物・組織` の5つだけを表示。
- スマホ公開ビュー選択: `関係地図 / 公開順 / 世界線・時系列 / この作品を見るなら / 人物・組織` の5つ。横並びのPCタブはスマホでは非表示。
- `mcu / road / legacy / doomsday` パネル: HTML内には保持し、公開ナビゲーション対象からのみ除外。
- `release / chronology`: `data-lazy-initialized=0` から初回表示時だけ軽量初期化する Stage A プレースホルダー。SVGはまだ生成しない。
- `watch`: 旧グラフパネルではなく既存の `watchWorkspace`（予習・視聴プラン）へ統一して遷移。チャート内の `↓ 予習・視聴プラン` も同じ経路へ統一。
- 関係地図の `<div id="overview">` 断片 SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf` — v5.15.13と完全一致。
- データ SHA-256: NODES `a50afa68bff756cdacad13127d47f39d45fdb01d24ffda046dc64d7b2f17ab11` / EDGES `78a7af640a070ff82bb5599a6f1535c416ec77f348dc9577072799cd1fe6464c` / CHAR_LINKS `024e6e2e98cd0eeefea7f91729743e50563a599c75662ac0ab12eaf9e8eb3d44` / WORK_DETAILS `639867560b3c6e83d97ac2d34e2a083504c5f067924017ce60aaa6853e63e780` — v5.15.13と一致。
- Stage A回帰テスト: 7件。データ数、overviewハッシュ、PC/スマホ5ビュー、旧パネル非公開化、lazy入口、watch経路、モバイル遅延full refresh再導入防止を検査。
- inline JavaScript: 16本を `node --check` し構文エラー0。
- PC headless Chromium: 5ビュー切替、release/chronology lazy初期化、watchWorkspace遷移、pageerror 0を確認。
- モバイル高速経路: Stage Aではゴール追加・既存ゴール切替・1件削除・全解除のv5.15.13コードを変更していない。`setTimeout(()=>refreshSelection(...` の再導入なし、lazy initializerから `refreshSelection` / `rebuildMobileCanvas` 呼び出しなし。
- Pixel 6相当 412×915の新規実測は今回のサンドボックスでは完走できなかったため、v5.15.13の `500ms後 refreshSelection=0 / rebuildMobileCanvas=0` を「今回再測定済み」とは扱わない。



## v5.17.0 Stage B — 公開順

- `RELEASE_META`: 131 / 131作品。`NODES` とキー集合が完全一致し、既存作品データとは別レイヤーで保持。
- 日付精度: day 127 / month 2 / none 2。未定は `Blade (MCU)`、中止報道反映は `Wonder Man S2`。
- 公開種別: theatrical 74 / streaming 42 / series-start 5 / home-video 5 / special 2 / imax-series-start 1 / undated 2。
- 主順序: 映画は米国劇場公開日、ストリーミングはグローバル配信開始日。日本公開日は主ソートへ混ぜない。
- 部分日付: `2027-03` / `2027-01` のように月精度を保持。内部ソート用の末尾センチネルは表示日へ出さない。
- 2026-08-24再監査: `Your Friendly Neighborhood Spider-Man S2` はD23 2026後の最新報道に合わせ2027年1月へ更新。`Spider-Man: Beyond the Spider-Verse` はSony Group FY2025 Q4/CinemaCon 2026に合わせ2027-06-18へ更新。
- `Wonder Man S2`: 2026-07-31のキャンセル報道を `status=cancelled` としてRELEASE_METAへ保持。相関図の作品ID自体は互換性・関係データ不変条件のため削除しない。
- `Blade (MCU)`: Disneyの公開カレンダーから外れた後も新しい確定日がないため `公開日未定`。推測の2028日付等を割り当てない。
- 生成方式: 初期HTMLの `#release` にはSVGなし。②初回表示時のみ131カードを含むSVGを生成し、スマホではその時点でCanvasキャッシュを作成。
- 公開順SVG: `g.node.release-node` 131 / `g.edge` 0。`data-relationship-edges=off` で既存199接続の矢印を公開順上へ自動追加しない。
- 初回カメラ: PC/スマホとも現在年（監査時2026）の帯を初期表示。Pixel 6相当では年帯先頭を500×500 world-unit cameraで表示し、日付文字を読める縮尺へ調整。
- 検索・ゴール: `release` を検索対象へ追加。ゴール状態は共有し、カード位置は固定のまま既存の関連点灯を適用。
- Pixel 6相当 412×915 headless Chromium: 初期 `release SVG=0 / Canvas=0`、②初回表示 `nodes=131 / edges=0 / Canvas生成 / cacheVersion=1 / nodeBoxes=131`、pageerror 0。
- 同環境で公開順表示中にゴール追加後550ms: `refreshSelection=0 / rebuildMobileCanvas=0`。削除後550msも `0 / 0`。追加時Canvas overlayはactive、キャッシュversionは1のまま。
- 関係地図断片SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf` — v5.15.13 / v5.16.0から不変。
- `RELEASE_META` SHA-256: `6aa30112365ff6cdc810f96d1fb2eab5711deb10c2dbb904f0ce38efc2dce6de`。
- Stage A + Stage B pytest: 16件。全件PASSを最終パッケージ直前に再実行する。

## v5.17.3 関係地図モバイル回帰修正

- 作品 / 有向接続 / 人物リンク / 詳細: **131 / 199 / 155 / 131 — PASS**
- ①関係地図断片 SHA-256: **v5.17.2と完全一致 — PASS**
- inline JavaScript: **16本 / 構文エラー0 — PASS**
- 点灯中パン: 選択オーバーレイの毎フレーム全primitive再描画を廃止。ジェスチャー中は既存オーバーレイをCSS/GPU transformで追従し、終了時に1回再描画。
- 視聴済みチェック: watched-dim由来のCanvasキャッシュ更新時は選択オーバーレイを保持。
- 予習プラン→チャート復帰: 二重requestAnimationFrame後に選択オーバーレイを復元。
- 点灯矢印先端: モバイル選択オーバーレイでカード境界手前に6pxの視覚余白を追加。
- Chromium fresh実ブラウザ計測: **このサンドボックスでは起動がtimeoutしたため未実施**。Pixel 6実機確認が必要。
- 作品間隔の過密箇所: **未変更**。接続経路を壊さないよう次段で局所レイアウト監査する。

## v5.17.4 追加監査 — 点灯矢印ジェスチャーキャッシュ

- 点灯中の移動でviewport外へ出た矢印が移動先で突然再描画される原因を、viewportサイズの点灯Canvasをtransform追従していたことと特定。
- 関係地図全体 3600×2500 に対し LOD 0.35 の選択専用キャッシュを追加。ジェスチャー中は現在のviewBox範囲だけを drawImage で切り出す。
- ジェスチャー中の全プリミティブ再走査: なし。
- 指を離した後の通常解像度点灯レイヤー再描画: 1回。
- 回帰テスト: 6 / 6 PASS。
- inline JavaScript: 16 / 16 構文PASS。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131: 不変。
- 関係地図SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf`（不変）。
- Pixel 6実機での最終体感確認はユーザー確認待ち。


## v5.17.5 追加監査 — ゴール選択の段階点灯キャッシュ

- ゴール選択直後の通常解像度overlayは、現在viewBox＋84px相当の周辺だけをbboxで先に描画。
- 全地図選択キャッシュ LOD 0.35 は同期生成せず、`requestAnimationFrame` で1フレーム約4msの予算に分割。
- 新しい選択状態が来た場合は build token で旧生成をキャンセルし、同じゴールでも選択状態オブジェクトが変われば再生成。
- キャッシュ完成前のジェスチャーは直前overlayのtransform追従をフォールバックに使用し、完成後は全地図キャッシュ切り出しへ移行。
- 回帰テスト: 7 / 7 PASS。
- inline JavaScript: 16 / 16 構文PASS。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131: v5.17.4と完全一致。
- ①関係地図断片 SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf`（不変）。
- Chromium実行: sandboxでは `about:blank` でも20秒timeout。Pixel 6実機の体感確認が最終確認点。

## v5.17.6 追加監査 — 点灯レイヤーの座標系統一

- v5.17.5で全地図キャッシュ完成前だけ使用していたCSS `matrix(...)` transform追従を廃止。
- ゴール選択時に現在viewBoxの上下左右1.6画面分を含むローカル点灯パッチ（LOD 0.35）をワールド座標で生成。
- ジェスチャー中はローカルパッチまたは完成済み全地図キャッシュから、背景Canvasと同一のviewBox→drawImage式で切り出す。
- 全地図キャッシュは従来どおり1フレーム約4ms予算で段階生成。
- 回帰テスト: 5 / 5 PASS。
- inline JavaScript: 16 / 16 構文PASS。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131: v5.17.5と完全一致。
- ①関係地図断片 SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf`（不変）。
- Chromium実行はsandbox制約のため未実施。Pixel 6実機の体感確認が最終確認点。

## v5.17.7 追加監査 — ゴール追加時の同期負荷削減

- v5.17.6で同期生成していた上下左右1.6画面ぶんのローカル点灯パッチを、ゴール追加の同期経路から完全に除外。
- ゴール追加直後は現在viewBox＋84px相当のみを通常解像度overlayへ即時描画。
- ローカル点灯パッチ LOD 0.35 は `requestAnimationFrame`、1フレーム約2.5ms予算で段階生成。部分生成中もワールド座標のpatch canvasを切り出せる。
- ローカルパッチ完成後に全地図点灯キャッシュを約4ms/フレームで段階生成。旧ゴール用の進行中生成は新規選択時にtoken/RAFを破棄。
- 同期経路から `mobileOverlaySyntheticSpecs()` を除外。補助・圧縮矢印は非同期パッチ側から描画。
- Canvas primitive生成時に `overlayNodeId / overlayEdgeKey / overlayIsEdge` を索引化し、点灯判定ごとのDOM `closest()` を廃止。
- v5.17.6のCSS transform非使用・ワールド座標切り出しを維持。
- 回帰テスト: 6 / 6 PASS。
- inline JavaScript: 16 / 16 構文PASS。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131: v5.17.6と完全一致。
- ①関係地図断片 SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf`（不変）。
- Chromium fresh実行はsandbox制約のため未実施。Pixel 6実機のゴール追加体感が最終確認点。


## v5.17.8 追加監査 — 点灯Canvas事前準備＋直接索引描画

- 基準: v5.17.6の「背景と点灯を同じワールド座標で動かす」方式へ戻し、部分パッチ→全地図キャッシュ切替を廃止。
- Canvas primitive生成時に `overlayNodeId / overlayEdgeKey / overlayIsEdge / overlayDynamic` を記録。
- 地図Canvas再構築時に `overlayNodePrimitives / overlayEdgePrimitives / overlayNodeBoxMap / overlayStaticEdgeKeys` を事前生成。
- LOD 0.35 の全地図点灯Canvasをゴール選択前に確保。ゴール追加時の `document.createElement('canvas')` を廃止。
- ゴール追加時の点灯描画は `state.ctx` と選択中のedge setから関連IDだけを取り出し、索引Mapから直接primitiveを取得。`cs.primitives` 全走査なし。
- スワイプ中は事前確保済み全地図点灯Canvasを背景と同じviewBox→drawImage式で切り出す。CSS transform、ローカルパッチ、段階キャッシュ切替なし。
- 視聴済みチェック後のoverlay保持・予習プランからの復元・矢印先端6px余白は維持。
- 回帰テスト: 12 / 12 PASS。
- inline JavaScript: 16 / 16 構文PASS。
- 作品131 / 有向接続199 / 人物リンク155 / 詳細131: v5.17.6と完全一致。
- ①関係地図断片 SHA-256: `e52bac09197e3ff702ae729aebc8bef9d4af1f50e324736c6d79f4355959ccaf`（不変）。
- fresh Chromium実機相当計測はsandbox制約のため未実施。Pixel 6実機で「ゴール追加時の引っ掛かり」と「スワイプ時の浮き感」の両方を最終確認する。
