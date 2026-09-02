# Marvel Library — 時系列・公開順の表示契約

## 1. 目的

本仕様は、関係地図（作品間の意味的な接続）とは異なる二つの表示を、選択点灯の対象として安全に扱うための契約を定める。

対象は次の二つである。

1. **世界線・時系列** — 作品の相対順、系列、分岐を表示する表示トポロジー。
2. **公開順** — 公開日・公開精度・編集上の時代区分を表示する日付軸。

この二つを関係地図の `EDGES` と同一視したり、公開順から作品間の意味的な矢印を自動生成したりしない。

## 2. 現行実装の境界

- 関係地図は `data/derived/flowchart.json` の作品・関係エッジを使う。
- 時系列は `buildChronologyView` が生成する `g.chronology-edge` を使う。現在の配置・線トポロジーは主に `index.html` に実装され、`data/library/chronology_assertions.csv` はヘッダーのみである。
- 公開順は `buildReleaseView` が生成する `g.node.release-node`、年軸、時代・レーンを使う。SVG は `data-relationship-edges="off"` とし、`g.edge` と `g.chronology-edge` を生成しない。
- 選択状態は関係地図と共有するが、表示層ごとに適用する対象を限定する。
- PC の SVG とモバイルの Canvas は同じ意味論を観測できなければならない。Canvas が内部で合成表示を行う場合も、下記の表示層境界を越えてはならない。

## 3. 共通選択原則

### 3.1 作品集合と選択状態

- 作品カードの `work_id` は関係地図・時系列・公開順で安定して一致する。
- 同一作品の再クリック、背景クリック、ドラッグ終了後の選択維持は既存の選択契約を引き継ぐ。
- パネル切替後は現在の選択状態を再描画する。ただし、表示層に存在しない対象を架空の線で補わない。

### 3.2 選択モード

公開5モード（`complete`、`site-proposal`、`OR`、`AND`、`PATH`）の判定は、各表示層が対応する対象に対して同じ状態入力を使う。`previous1` は公開scope UIを持たない内部unit-only classifier 契約であり、公開UIへ追加しない。

- 関係地図の `EDGES` は関係地図の既存契約で分類する。
- 時系列は §4 の `chronology-edge` だけを分類する。
- 公開順は §5 のカード・軸だけを分類する。
- 表示層が対象としていない線を、別層の `backEdges`、`forwardEdges`、`contextEdges`、`pathEdges` から暗黙に描かない。

### 3.3 表示専用要素

`display_only=true` の要素は必ず `traversable=false` とする。この不変条件を満たす要素は、配置・説明のために表示してよいが、次のいずれにも使用しない。

- 前史・後続の点灯
- `PATH` の経路
- `OR`／`AND` の線集合
- 関係理由・作品ペアの導出
- 公式予習ルートなどの事前視聴ルート
- モバイル Canvas の合成線

## 4. 世界線・時系列契約

### 4.1 線の識別とデータ境界

将来時系列トポロジーをデータ化する場合は、関係地図の `work_edges_all` や `work_pair_reasons` に混ぜず、時系列専用の表示入力として次の属性を持つ。

```text
edge_id            固有の安定ID。同じ source/target の複数線を区別する
source_work_id     左側／前側の作品
target_work_id     右側／後側の作品
kind               sequence | branch | merge | crossing など
traversable        選択・経路探索に使うか
display_only       表示専用か（true なら traversable=false）
lane/label/style   配置・説明専用の任意属性
```

`order`、`track`、カードの配置順だけから自動的に線を作らない。一次資料に基づく相対順の意味論を正規化する場合も、別の承認済みデータ監査と evidence/review を必要とする。

現行の `data-chronology-edge-key` は互換のため利用できるが、同一作品対に複数線を許す設計へ拡張する前に `edge_id` へ移行する。SVG の `source->target` と Canvas のキーが衝突しないことをテストで保証する。

`(source_work_id, target_work_id, kind)` の重複は、別の線である理由を明示的に監査できる場合だけ許可する。`edge_id` の一意性と、作品対・種別の重複可否は別の制約として検証する。

### 4.2 点灯規則

- `traversable=true` の線だけが classifier の入力になる。
- `complete` は選択作品から時系列グラフ上の前後方向に到達できる traversable 線を分類する。
- `site-proposal` は既存の tier 入力を使い、前史側は `tierNodeIds` による許可を適用し、後続側は現行の時系列 forward 方針を適用する。
- `previous1` は直接の traversable incoming のみを前史として点灯する。
- `OR` は各選択作品の線集合の和、`AND` は共通集合とする。
- `PATH` は関係地図が提供した `pathEdges` のうち、時系列表示に存在し、かつ traversable な線だけを点灯する。時系列グラフを暗黙に再探索して別経路を作らない。
- 方向カテゴリは `backhl`、`forwardhl`、`bothhl`、`pathhl`、必要な文脈線は `contexthl` とし、SVG と Canvas で同じ分類結果を得る。さらに、SVG に実体化された traversable chronology edge ID 集合と、Canvas overlay に実体化された chronology edge ID 集合を一致させる。display-only metadata も Canvas 側で保持し、別の source/target 正規化で線を落とさない。
- `traversable=false`／`display_only=true` の線は、選択作品の直前・直後に見えていても一切点灯しない。

### 4.3 構造線と表示線

分岐・合流・交差を表す線は、線ごとに traversability を明示する。`track` や `certainty` の値から点灯可否を推論しない。曖昧な位置づけを表すカードや枠は表示できるが、線を追加する根拠にはならない。

traversable な時系列線も、それだけで関係地図の作品ペアや理由を自動生成しない。時系列線はこのビュー上の相対順であり、「なぜこの二作品を見る必要があるか」という関係理由とは別である。理由として表示する場合は、別途 evidence-backed な関係事実が存在しなければならない。

### 4.4 必須監査

実ブラウザ監査では、少なくとも次を確認する。

- 全時系列カードの作品集合と `work_id` が一致する。
- `complete`、`site-proposal`、`OR`、`AND`、`PATH` の代表ケースで、期待する線だけが点灯する。`previous1` は公開controlがない場合、実ブラウザでは内部unit-only coverage gap として明示し、内部state注入による代替監査はしない。
- display-only／non-traversable 線に `hl` 系クラスも Canvas 合成線も付かない。
- 同一 source/target の複数線を追加した fixture で、固有 edge ID が混線しない。
- SVG と Canvas の線キー・分類・点灯集合が一致する。
- パネル往復、再クリック解除、背景解除、ドラッグ後の選択維持で線状態が壊れない。

## 5. 公開順契約

### 5.1 意味論

公開順は作品の公開史を読むための日付軸であり、作品間の因果・前史・後続を示す関係グラフではない。

- 日付は `RELEASE_META` の精度を保持する。
- 日単位・月単位・年のみ・未定／未知を区別する。
- 月単位・年のみ・未定から日を推測しない。レイアウト用の数値アンカーは表示上の位置であり、実日付ではない。
- 同日カードは意味論を持たない安定ソート順（canonical stable sort index）を経由し、作品IDを最終タイブレークとする完全順序を持つ。関係地図や時系列の順序で同日順を決めない。
- 中止・延期・未確定などの状態を、公開済みや別の日付へ暗黙変換しない。
- 日付未定作品は確定日付の軸へ擬似配置せず、`Upcoming / date TBD` などの独立バケットで扱う。

### 5.2 選択表示

公開順で作品を選んだときは、選択対象の `work_id` と詳細パネルを関係地図・時系列と共有し、選択作品のカードを `focus`（PC の詳細フォーカス、モバイルの goal 表示）として示す。関係地図へ戻ったときは、その作品の通常の関係ハイライトを再構築する。公開順画面自身では、既存の選択状態に応じたカードの文脈表示を除き、作品間の線を描かない。

次の要素は生成・点灯してはならない。

- `g.edge`
- `g.chronology-edge`
- 公開順の隣接カードを結ぶ矢印・線
- 関係地図の `backEdges`／`forwardEdges`／`contextEdges` を使った Canvas 合成線

すなわち、`data-relationship-edges="off"` は SVG の宣言だけでなく、モバイル合成描画を含む実行時の禁止契約である。選択前後で、カード集合、カードの `path d`、年軸・時代枠、`viewBox`、線要素数を変更しない。

### 5.3 必須監査

PC とモバイルの実ブラウザ監査で次を確認する。

- 公開順 SVG が全作品カードを一度ずつ持ち、`g.edge` と `g.chronology-edge` がゼロである。
- 代表カードを選択しても、カード・軸・時代枠の幾何シグネチャと作品集合が不変である。
- PC のカードフォーカス、モバイル Canvas の goal 表示が同じ作品を指す。
- モバイルの合成表示で relation／chronology の線が一本も描かれない。
- 再クリック解除、背景解除、ドラッグ後の選択維持、パネル往復が成立する。
- 日付精度、未定バケット、同日タイブレークの静的契約を確認する。

## 6. 実装・監査の段階

この仕様書自体は表示契約のみを定め、実装・canonical CSV・SQLite schema は変更しない。実装時は次の順序で別々に進める。

1. 時系列の RED 契約（固有線キー、non-traversable 除外、公開5モード＋内部unit-only previous1、SVG/Canvas parity）を追加する。
2. 最小実装を行い、時系列の unit／DOM／Canvas 監査を GREEN にする。
3. 公開順の RED 契約（カード選択、幾何不変、モバイル合成線禁止、日付精度）を別ジョブで追加する。
4. 最小実装を行い、公開順の PC／モバイル監査を GREEN にする。
5. 全ライブラリテスト、build、audit、SQLite integrity、既存 131作品選択監査を再実行する。

時系列の canonical 正規化（`chronology_assertions.csv` への追加を含む）は、この表示契約の実装とは別の evidence/review 付き計画として扱う。表示上の線を追加することを、作品関係・公開事実・世界線の証明とはみなさない。

## 7. 受け入れ基準

次のすべてを満たすまで、この境界の作業を完了としない。

- 時系列の表示線と関係地図の作品関係線が、DOM・Canvas・選択理由のいずれでも混ざらない。
- non-traversable/display-only 線が表示から消えず、選択・経路・理由からは除外される。
- 同一作品対の複数時系列線が固有IDで安定して点灯する。
- 公開順が日付軸として読め、選択によって架空の関係線が出ない。
- PC／モバイル、通常選択／詳細フォーカス、パネル往復の挙動が契約どおりである。
- 既存の関係地図 131作品×2 tier の完全一致監査、全テスト、build、監査が回帰しない。
- canonical data と persistent review ledger は、別途承認されたデータ変更がない限り不変である。
