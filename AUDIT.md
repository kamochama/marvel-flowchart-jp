## v5.20.5 世界線・時系列 — 強い系列線の復帰

- ユーザーから「本来線で繋がりそうなやつらが繋がっていない」との指摘を受け、v5.20.4 の枝線削減が強すぎた可能性を再評価した。
- 方針として、**意味の弱い補助枝線は抑えたまま、意味の強い“同系列”の接続だけ戻す** ことにした。
- 以下を再接続:
  - `Captain America: The Winter Soldier → Civil War → Black Widow → The Falcon and the Winter Soldier → Brave New World → Thunderbolts/New Avengers`
  - `I Am Groot S1 → I Am Groot S2`
  - `Thor: The Dark World → Thor: Ragnarok → Thor: Love and Thunder`
- これにより、スマホで見たときの「本来つながりそうなのに切れている」違和感を減らすことを狙う。
- JavaScript 16 / 16 PASS。データ本体は不変。

## v5.20.4 世界線・時系列 — 孤立枝線の整理

- ユーザースクリーンショットにより、スマホ表示で **接続先のない縦線に見える補助枝線** を確認した。
- 原因は、カード被り回避のために gutter 側へ逃がした汎用 `branchBetweenRows` が、視覚的には孤立して見えること。
- 対策として、MCU の汎用枝線 3 本（shared→cosmic / shared→magic / shared→ground）と、SSU の汎用枝線 1 本を削除した。
- 残す縦接続には `.chronology-junction` を追加し、接続の開始・終了に小さなジョイント点を表示。
- これにより、意味の弱い補助枝線は減らし、意味の強い分岐だけを明示する構成に寄せた。
- JavaScript 16 / 16 PASS。データ本体は不変。

## v5.20.3 世界線・時系列 — 入れ子枠廃止 + ミニナビ

- ユーザー提供スマホスクリーンショットで、内側の系列枠が互いに重なり、ナビポップオーバーがチャート中央を大きく覆う状態を確認。
- **世界線のみ `worldFrame()` の外周ボックス**として表示し、内側の物語系列は `laneHeader()` による「色付きピル + 上辺レール」へ変更。
- MCU の内側 `groupBox()` は廃止し、`初期アベンジャーズ系 / 宇宙・マーベルズ系 / 魔術・マルチバース系 / 街・地上サイド / ワカンダ・量子・新世代` をレーン見出し化。
- Spider-Man / SSU / FOX のサブ系列も同様にレーン見出し化し、ネストした四辺枠をなくした。
- 枠内ナビを `.chronology-nav-popover.is-mini` へ変更。最大幅 280px（スマホ 250px）、横一列スクロール、スマホではタイトル行非表示。
- `fitChronologyGroup()` は `g.chronology-group[...]` 限定から `g[data-chronology-group-key]` へ変更し、新しい世界線外枠の `枠全体` に対応。
- TDD: `test_v5203_lane_headers_nav.py` RED→GREEN、`test_v5203_fit_selector.py` RED→GREEN。
- データ本体は不変（NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103）。
- Chromium headless による自動スクリーンショットは現環境でタイムアウトしたため、fresh実ブラウザ視認は未完了。静的回帰・JS構文・データ不変で検証。

## v5.20.2 世界線・時系列 — スクリーンショット監査反映

- ユーザー提供スクリーンショットにより、**系列枠ヘッダーが1行目カードへ重なる** 実例を確認した。
- `groupBox()` を修正し、見出し矩形の高さに応じた `topClearance = Math.max(insetY, headH + 12)` を導入。
- これにより、枠見出しがカード行そのものに重なりにくい配置へ変更した。
- 系列枠の内側サブ説明は多くを撤去し、スマホでは `.chronology-lane-sub`, `.chronology-group-sub`, `.chronology-track-label` を非表示化。
- データ本体は不変（NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103）。
- inline JavaScript 16 / 16 PASS。スクショ監査は反映済みだが、実機再確認はユーザー確認待ち。

## v5.20.1 世界線・時系列 — 文字重なり / 線被り整理

- v5.20.0 の多段レイアウトを継承し、**文字の重なり** と **接続線のカード被り** を主対象に調整した。
- カード寸法と列間隔をやや拡大し、`stepX` を広げて横方向の窮屈さを緩和。
- `rowY` を全面的に下方再配置し、段間隔を拡大。
- `branchBetweenRows` は `xForCol(col)+cardW/2` から **`xForCol(col)-16`** へ変更し、カード中央を縦貫しないようにした。
- MCU の段ラベルや説明文字を削減し、長いサブ見出しも短縮して干渉を減らした。
- drawSequence の描画順を、**線→カード** に変更し、横接続線がカードの上に載りにくいようにした。
- データ本体は不変（NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103）。
- inline JavaScript 16 / 16 PASS。実ブラウザでの最終視認監査は未実施。

## v5.20.0 世界線・時系列 — 世界線の大枠 + 物語系列の多段表示

- ③「世界線・時系列」のレイアウト思想を変更。
- **大枠 = 世界線（ユニバース） / その中の段 = 直接つながる物語系列** として整理した。
- MCU は中央の1本線から、`共有イベントの背骨 / Captain America系 / Cosmic / Magic / Street / Ground / 補助系列` へ多段化した。
- Spider-Man系列は `Raimi / Amazing / MCU Spider-Man` を別段で表示し、`No Way Home` 付近で交差。
- 同じ世界線でも直接つながりの薄い作品は別段へ逃がす構成とし、**横幅を短縮して高さで吸収**する方向へ調整。
- 既存の上部ジャンプバーと、枠内ナビ（ポップオーバー）は維持。
- `NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は不変。
- inline JavaScript 16 / 16 PASS。fresh実ブラウザでの全端末最終監査は未実施。

# マーベル作品相関図 日本版 — PUBLIC v5.20.0 監査

監査日: 2026-08-25  
基準版: PUBLIC v5.15.13  
候補版: PUBLIC v5.18.7 chronology no dangling line stubs

## 結果

**5ビュー公開ナビゲーション: PASS（静的回帰）**  
**② RELEASE_META 131 / 131: PASS**  
**② 歴史表示: 7時代セクション / 7歴史マーカー / 最大SVG横幅1320: PASS（コード契約）**  
**関係地図データ・文字座標・既存矢印幾何: PASS（v5.17.9の44作品＋v5.17.10の大枠11作品のみ外枠局所変更）**  
**作品131 / 有向接続199 / 人物リンク155 / 詳細131: PASS**  
**inline JavaScript 16本 構文エラー0: PASS**  
**ゴール高速経路に refreshSelection(false) / rebuildMobileCanvas 再導入なし: PASS（静的回帰）**  
**固定6ファイルZIP構成: PASS**  
**③ 世界線・時系列 Stage C: 5 continuity / 103 metadata / 左分類追従 + 作品名内枠 PASS（静的回帰）**

v5.17.2では公開順専用メタデータを維持したまま、②の見せ方を再設計した。全期間を1本の巨大な横長タイムラインへ置く方式を廃止し、歴史時代ごとにX軸をリセットしたセクションを縦方向へ連結する。時代名は公式区分ではなく、企業・制作体制・配信構造の転換点を一次資料優先で整理した編集上の歴史区分である。

歴史マーカーは、2005年Marvel自社製作資金、2009年DisneyによるMarvel取得、2013年Marvel/Netflix大型TV展開、2015年Sony×Marvel Studios協業、2019年Disneyによる21st Century Fox取得、2019年Disney+開始、2021年Marvel Studios初のDisney+シリーズを採用。

この実行環境ではChromium headlessがDBus/zygote周辺でタイムアウトするため、v5.17.2のfreshな実ブラウザ画像検証は完走していない。v5.17.0で確認済みのPixel 6相当高速経路実測値は継承資料として保持するが、v5.17.2のfresh実測とは扱わない。


## v5.18.2 世界線・時系列 — 左分類追従 / 作品名内枠

- chronology用のHTMLオーバーレイ `chronology-sticky-labels` を追加。
- `Raimi / Amazing / MCU 本流 / SSU / FOX X-MEN` の分類名は横パンに追従せず画面左へ固定し、縦パン・ズーム時はworld Y座標から画面位置へ再計算して同期。
- PC transform座標と、スマホ viewBox / Canvas座標の両経路で `syncChronologyStickyLabels` を呼ぶ。
- 作品カード内の作品名部分へ `chronology-title-box` を追加。外側カード・時系列順・分岐線は変更しない。
- 回帰テスト: 3 / 3 PASS。inline JavaScript: 16 / 16 PASS。
- NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103 は不変。
- freshブラウザ画像検証: NOT COMPLETED（現サンドボックス制約）。

## v5.18.4 世界線・時系列 — 作品カードを①関係地図型へ統一

- 根本原因: ③の `chronologyCard()` が①の作品カードを再利用せず、`分類チップ + 内側タイトル枠 + 確度注記` という独自UIを生成していたため、ユーザー意図の「関係地図と同じ作品枠」になっていなかった。
- 修正: ③の作品を `濃色背景 + continuity色の外枠 + 中央揃え作品名 + 下段公開時期` の単一カードへ変更。
- 内側タイトル枠・カード内分類チップ・カード内確度注記を撤去。
- ambiguous / unknown / partial はカード全体の破線、time-crossing / multiverse / pivot はカード外枠色の差で補助表現を維持。
- 左端分類は v5.18.3 の枠なし追従ラベルを維持。
- chronologyカード寸法: 190 x 64、横ステップ208。中央MCU本流・上下レーン・右向き分岐方針は不変。
- 回帰テスト `test_v5184_chronology_card_style.py`: PASS。
- inline JavaScript 16 / 16: PASS。
- `NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103`: 件数・ハッシュ不変。

## v5.19.3 世界線・時系列 — 枠内ナビ

- 主要な `chronology-group` に枠内ナビを追加。大枠の見出し帯または `ナビ` ボタンから、その系列の節目をその場で呼び出せる。
- `CHRONOLOGY_FRAME_NAV` を追加し、Spider-Man / SSU / FOX X-MEN / 初期アベンジャーズ / Guardians / 魔術・マルチバース / ワカンダ・量子・マーベルズの節目を定義。
- `openChronologyNav(key, x, y)` で `chronology-nav-popover` を図内に表示。
- `fitChronologyGroup(key)` を追加。`枠全体` では対象枠を基準にカメラを調整する。
- 作品ジャンプは既存 `jumpChronologyTo(id)` を再利用し、現在ズームを維持。
- モバイルCanvasに `chronologyNavBoxes` / `mobileCanvasChronologyNavHitTest()` を追加し、SVGが非表示の高速描画時も枠内ナビをタップ可能にした。
- モバイルのヒット判定は `exact hit -> padded hit` の2段階にし、ズームアウト時に隣接ヘッダーのタップ余白が重なって別パレットが開く問題を防止。
- Chromium mobile emulation (412x915, touch/canvas enabled) で、Canvas上の枠見出しタップ → パレット表示 → 節目ジャンプ → ポップオーバー閉鎖を実ブラウザ確認。Captain Americaへのジャンプ前後で camera width 1500 を維持することを確認。
- 変更は③のナビUI・カメラ操作・モバイルヒット判定のみ。`NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は不変。

## v5.19.2 モバイルCanvas — SVG rect 対応

- 不具合: PCのSVGでは見える③のシリーズ大枠が、スマホのCanvas高速描画では表示されなかった。
- 根本原因: `rebuildMobileCanvas()` のプリミティブ収集が `path,polygon,polyline,text` のみで、`rect` を除外していた。
- 修正: プリミティブ収集へ `rect` を追加し、`canvasPrimitive()` に通常矩形 / `rx` 角丸矩形の Path2D 変換を追加。
- これにより `chronology-group-box / chronology-group-head / chronology-lane-bg` 等がモバイルCanvasにも反映される。
- 回帰テスト: selector / rect branch / width-height / rounded path の 4項目 PASS。
- inline JavaScript 16 / 16 PASS。
- `NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は不変。
- fresh実機視認確認はユーザー端末での確認待ち。

## v5.19.1 世界線・時系列 — 関係地図寄りの見出し付き大枠

- `chronology-group-box` を **太い枠線** に変更し、さらに `chronology-group-head` を追加して、関係地図の大枠に近い「見出し付きグループ枠」とした。
- 旧版の「薄い背景があるだけで枠が分かりにくい」問題を改善するため、**系列名を載せた色付きヘッダー**を各枠の左上に表示。
- Spider-Man / SSU / FOX X-MEN は大枠を維持しつつ、系列名が一目で読める視認性を強化。
- MCU側は細かいシリーズ枠を整理し、`初期アベンジャーズ系 / ガーディアンズ系 / 魔術・マルチバース系 / ワカンダ・量子・マーベルズ` の4枠へ集約。
- 変更は chronology の背景グループ枠の見た目と MCU枠ラベル構成のみ。`NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は不変。
- inline JavaScript 16 / 16 PASS。fresh実ブラウザ視認チェックは現サンドボックスでは未実施。

## v5.19.0 世界線・時系列 — シリーズまとまり枠

- ③「世界線・時系列」に、`chronology-group-box` を用いた**半透明の大きい系列枠**を追加。
- 遠目でも位置を把握しやすくするため、枠線よりも **大きいラベル文字**を優先したデザインを採用。
- 追加した大枠: `Spider-Man系列 / SSU / FOX X-MEN`。
- 追加したサブ枠: `Raimi / Amazing / MCU Spider-Man / Venom本線 / 独立作品 / 旧系列 / 改変後系列 / 位置づけ慎重`。
- MCU本流にも `キャプテン・アメリカ系 / アイアンマン系 / ソー系 / ガーディアンズ系 / アントマン系 / ドクター・ストレンジ系 / ワカンダ系 / キャプテン・マーベル系` の**ざっくりした系列枠**を追加。
- 変更は chronology 描画の背景要素のみ。`NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は不変。
- inline JavaScript 16 / 16 PASS。fresh実ブラウザ視認チェックは現サンドボックスでは未実施。

## v5.18.9 モバイル viewport 変化時のカメラ保持

- 不具合: スマホでページ外側をスクロールすると、ブラウザUIの表示変化により `resize` が発火し、`fitView(activeWrap())` によってチャートが極小化していた。
- 修正: `refreshActiveWrapViewportPreservingCamera()` を追加し、モバイルの `resize / media-query change / orientationchange` では **fitViewではなく現在カメラのまま再描画**するよう変更。
- `window.addEventListener('resize', ...)` の自動fitを、モバイル時は camera-preserving refresh に差し替え。
- モバイルUIブロックの `mq change` / `orientationchange` でも同様に camera-preserving refresh を使用。
- 変更はビューポート変化時の挙動のみ。NODES / EDGES / CHAR_LINKS / WORK_DETAILS / CHRONOLOGY_META は不変。
- inline JavaScript 16 / 16 PASS。

## v5.18.8 世界線・時系列 — 主要シリーズジャンプ

- ③「世界線・時系列」に `chronology-jump-bar` を追加。
- ジャンプ先は分類ではなく、**主要シリーズの最初の作品カード**に設定。
- `jumpChronologyTo(id)` を追加し、現在のズーム倍率を維持したまま対象カードを画面内の見やすい位置へ移動。
- desktop / mobile viewBox の両方で動作するよう、既存の `ensureViewState` / `ensureMobileViewBoxState` を再利用。
- ジャンプ後は `flashSearchFocus(id)` で対象カードを短時間強調表示。
- 変更は③のUIとカメラ移動のみ。`NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は不変。
- inline JavaScript 16 / 16 PASS。

## v5.18.7 世界線・時系列 — 始点・終点の空中線除去

- 根本原因: `axisLine(...)` が各レーンの先頭カードより14px左、末尾カードより18px右まで装飾線を延長していた。
- `MCU / SSU / SSU独立段 / FOX旧系列 / FOX改変後 / FOX位置慎重` の装飾用axisを撤去。
- `renderLinear()` / `renderMcuCore()` が生成する**実在カード間の線だけ**を残した。
- `No Way Home → MCU本流へ` は空中の短線終端を廃止し、`CHRONOLOGY_META` 上でNWH直後に位置する実在MCUカードの左端へ着地。
- dangling-line回帰: 2 / 2 PASS。Spider-Man統合 + タイトル回帰: 9 / 9 PASS。カードスタイル回帰: PASS。
- inline JavaScript: 16 / 16 PASS。
- `NODES / EDGES / CHAR_LINKS / WORK_DETAILS / CHRONOLOGY_META` SHA-256 は v5.18.6 と全一致。
- fresh実ブラウザ画像検証はサンドボックス制約により未完了。

## v5.18.6 世界線・時系列 — Spider-Man系列統合

- `Raimi / Amazing / MCU Spider-Man` を **Spider-Man系列1帯・3段**へ再構成。
- `spider-man-homecoming-2017 / spider-man-far-from-home-2019 / spider-man-no-way-home-2021` は中央MCU本流の描画対象から抽出し、重複カードを作らない。
- `No Way Home` は `data-chronology-junction` を持つ単一ジャンクションとして表示。Raimi / Amazing の最終カードから `chronology-spider-merge` で右向きに収束する。
- MCU Spider-Manは `Civil War` 付近から上段へ分岐。`No Way Home` 後は特定作品への架空の直接接続を作らず、`chronology-spider-return` の構造線でMCU本流位置へ戻す。
- 左端追従分類は `Raimi / Amazing` の2つを廃止し、`Spider-Man` 1つへ統合。
- SSUは別レーン維持。Venom / Morbius / Madame Web / Kraven をSpider-Man本線へ強制統合しない。
- TDD: Spider-Man構造 5 / 5 PASS。作品名幅フィット 4 / 4 PASS。inline JavaScript 16 / 16 PASS。
- v5.18.5比較: NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103 は全ハッシュ一致。
- fresh実ブラウザ画像検証は現サンドボックス制約により未完了。

## v5.18.5 世界線・時系列 — 作品名オーバーフロー修正

- 原因: `chronologyTitleLines()` が固定21文字基準で、CJK / ASCII / 記号の実表示幅差を考慮していなかった。
- 修正: `chronologyTextUnits()` + `chronologyTitleLayout()` を追加し、190pxカードの内幅170pxに対して表示幅ベースで最大2行へ分割。
- 作品名フォントは①関係地図に合わせて `10.5px` へ統一。公開時期は `8.5px`。
- 旧 `.slice(0,24)` によるタイトル切り捨てを撤去。
- CHRONOLOGY_META対象103作品を実関数で全件監査: **overflow 0 / content mismatch 0**。
- inline JavaScript: **16 / 16 PASS**。
- NODES / EDGES / CHAR_LINKS / WORK_DETAILS / CHRONOLOGY_META は内容不変。

## v5.18.3 世界線・時系列 — sticky分類ラベル干渉調整

- 作品カードの見た目を優先し、作品名を載せる `chronology-title-box` の輪郭を少し強めた。
- 左端のsticky分類ラベルは、ボックス表示から **細い色バー＋文字のみ** の軽い表示へ変更。
- sticky分類ラベル領域の幅を `176px` → `112px`、ラベル本体を `156px` → `92px` に縮小。
- 枠・背景・影を除去し、作品カードと競合しにくい視覚優先度へ変更。
- inline JavaScript 16 / 16 PASS。
- `NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 / CHRONOLOGY_META 103` は内容不変。

## v5.18.1 世界線・時系列 — 中央MCU本流レイアウト

- ③「世界線・時系列」のSVG構成を、**中央MCU本流 + 上下の横レーン**へ再設計。
- continuityの表示方針は `左→右` に統一。別世界線は本流から枝分かれし、接続先が右側に来るよう固定。
- レーン配置: 上段 `Raimi / Amazing`、中央 `MCU`、下段 `SSU / FOX X-MEN`。
- FOX X-MENは `Days of Future Past` を分岐点として、`旧系列 → 改変後系列 → 位置づけ慎重作品` を段分け表示。
- SSUは `Venom本線` と `独立作品` を別段表示。
- `CHRONOLOGY_META`: 103作品の件数・内容は維持。SHA-256: `39a63b7253b286f32a52b3eaf7ce3f9e07ad80b17e890fde51a6e896d7db3420`。
- `NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131` は不変。各SHA-256も v5.18.0 と一致。
- `buildChronologyView` と chronology 初期カメラのみ再設計。関係地図・公開順・予習プラン・共有機能には変更なし。
- inline JavaScript 16 / 16 構文検査: PASS。
- fresh Chromium画像検証: **NOT COMPLETED**。現サンドボックスでは file / localhost 描画確認が安定しないため、静的監査のみを成功扱いとする。

## v5.18.0 世界線・時系列 — Stage C

- `CHRONOLOGY_LANES`: **5レーン**。`MCU / Raimi / Amazing / SSU / FOX X-MEN`。
- `CHRONOLOGY_META`: **103作品**。lane内訳: `{'amazing': 2, 'fox-xmen': 13, 'mcu-main': 79, 'raimi': 3, 'ssu': 6}`。
- track内訳: `{'ambiguous': 2, 'main': 64, 'multiverse': 4, 'original': 5, 'pivot': 1, 'revised': 2, 'revised-side': 2, 'shared-origin': 1, 'standalone': 3, 'time-crossing': 4, 'unplaced': 12, 'venom-line': 3}`。certainty内訳: `{'ambiguous': 7, 'confirmed': 84, 'partial': 9, 'unknown': 3}`。
- `CHRONOLOGY_META` canonical SHA-256: `d8de9c4b0b7338764865abbb5c81cb9fa430f5d78a2ce90bd500d35ff93915f6`。
- MCUの既確認範囲はDisney+公式「MCUコンプリート 時系列順」（2025-03-31）を基準にする。現在のDisney+ Marvelページにも「MCU映画 時系列順」「MCUコンプリート 時系列順」コレクションが存在することを再確認した。
- `Loki` は `time-crossing`、`What If...?` は `multiverse` として通常線から区別。
- `The Fantastic Four: First Steps` はMarvel公式が別宇宙の1960年代風世界として説明するため `multiverse` 扱い。ただし本データではEarth番号を保存しない。
- FOX X-MENは `Days of Future Past` を `pivot` として、旧系列と改変後系列を別段表示。`LOGAN` / `The New Mutants` は `ambiguous` とし、枝へ強制接続しない。
- `Brand New Day` / `Doomsday` / `Secret Wars` は `unknown + unplaced`。公開日が確認済みでも作品内時系列を推測しない。
- Earth番号フィールド: **0**。`inUniverseDate` フィールド: **0**。
- 長いcontinuityは `chronology-row-turn` で折返し行を接続。FOXは `chronology-fox-original` / `chronology-fox-revised` の別経路。
- 検索対象へ `chronology` を追加。lazy buildを維持し、初期ロード時にStage C SVGを生成しない。
- Stage C TDD回帰: **10 / 10 PASS**。inline JavaScript: **16 / 16 PASS**。
- fresh Chromium画像検証: **NOT COMPLETED**。このサンドボックスでは `file://` と `http://127.0.0.1` が `ERR_BLOCKED_BY_ADMINISTRATOR` で遮断されたため、成功したとは扱わない。
- 関係地図の NODES / EDGES / CHAR_LINKS / WORK_DETAILS はv5.17.10と内容完全一致。関係地図のモバイル点灯経路・カード外枠補正には変更なし。

一次資料:
- Disney+ Japan: `https://www.disneyplus.com/ja-jp/explore/articles/mcu-series`
- Disney+ Marvel browse: `https://www.disneyplus.com/ja-jp/browse/page-60f4707d-19bb-4c0c-9390-ab269137be50`
- Marvel: `https://www.marvel.com/movies/the-fantastic-four-first-steps`


## v5.17.10 関係地図 — 小枠×大枠の2次元クリアランス補正

- v5.17.9の同一行監査では拾えなかった、別行の大枠と小枠が斜め方向に接触する組を2次元矩形距離で再監査。
- 10px未満だった小枠×大枠は16組。調整対象は大きい枠11作品のみ。小枠側はv5.17.9から変更していない。
- 大枠は接触している片側だけを内側へ寄せる。上下方向は2〜14px、例外的に `What If...? S1` の左側のみ24px調整。
- 小枠×大枠の最小2次元クリアランス: `0px` → `10px`。
- 既存edge 144グループの path / polygon 幾何SHA-256: `3f35b3636a59ea848e24d941c8992bee990dc21d6043f2007a38b88b487c7f04` — 不変。
- node text / tspan 座標SHA-256: `e2720b2b3e3c724d2486e99da8f87b07454de9fe5a059e3ed207d99df605f65e` — 不変。
- 関係地図overview断片SHA-256: `163db2db36d4fc97af48dc85328b10951071b901d6e0ad0b0c3a7aefa4ccb4eb`。
- NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 は不変。
- SVG直接レンダリングで `Wonder Man × Jessica Jones`、`What If...? × Blade`、`Moon Knight × Blade(MCU)` を目視確認。

## v5.17.9 関係地図 — 過密カード局所調整

- 同一エリア・同一行でカード間隔が8px未満だった32組を機械抽出し、関係する44作品だけを対象にした。
- 対象カードの外枠のみ左右6px・上下2px内側へ寄せ、カード中心・文字座標は変更していない。
- 最小水平ギャップは `-2px` から `10px` へ改善。
- 既存edge 144グループの path / polygon 幾何SHA-256: `3f35b3636a59ea848e24d941c8992bee990dc21d6043f2007a38b88b487c7f04` — v5.17.8と一致。
- node text / tspan 座標SHA-256: `e2720b2b3e3c724d2486e99da8f87b07454de9fe5a059e3ed207d99df605f65e` — v5.17.8と一致。
- 関係地図overview断片SHA-256は局所外枠変更により `eb2ce15fdfa5fd25f001b1c8a5c56e39fa8845410f9006aceaf9efacd60a1318` へ更新。
- NODES 131 / EDGES 199 / CHAR_LINKS 155 / WORK_DETAILS 131 は不変。
- v5.17.8 prewarmed world overlay、予習チェック後の点灯復元、スマホ高速ゴール追加・解除の回帰テストを維持。
- SVG直接レンダリングで Street / Marvel TV、Spider-Man周辺、MCU本流の対象箇所を目視確認。

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
