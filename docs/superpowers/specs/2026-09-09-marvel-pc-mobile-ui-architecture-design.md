# Marvel Flowchart JP — PC／モバイルUI統合設計

作成日: 2026-09-09  
状態: ChatGPTレビュー反映・再レビュー待ち
対象: PC版とモバイル版の表示層・操作状態・ナビゲーション設計  
関連仕様: `docs/superpowers/specs/2026-09-04-marvel-mobile-ui-redesign-design.md`

## 1. 設計結論

推奨案は、既存の作品・関係・点灯・予習意味論を共通APIで包み、PCとモバイルの表示層だけを分ける案Bである。

最初は公開HTMLの単一ファイル構成を維持し、`index.html`内に論理的な責務境界を設ける。状態更新、ナビゲーション、派生計算、描画スケジューリングの入口を固定し、既存監査が安定した後にだけ編集用ソース分割を検討する。状態管理の置換、DOMの大規模再配置、SVG／Canvas方式の変更を同じ段階で行わない。

この設計は表示・操作層を対象とし、canonical dataと既存の意味論を変更しない。

### 1.1 レビュー反映後の設計決定

実装前に、次の意味論を固定する。

- チャートの作品クリック／タップは「閲覧対象」の変更であり、ゴール追加ではない。再操作で`inspection.workId`を`null`へ戻す。
- ゴールの追加・解除は、チャート・検索・予習の各面に明示する「ゴールに追加／解除」操作だけが行う。旧`selectedIds`直接操作は互換層に閉じ込める。
- `reason`は作品ID一つから再推論せず、canonical relation IDを正本として履歴・URLから復元する。
- PCの右ペインはSheetHostのdocked表示、モバイルの詳細は同じSheetHostのmodal表示とする。詳細のDOM／状態所有者を二重化しない。
- Shell判定、5表示モードと共通`surface`の対応、履歴操作（push／replace／close）を仕様上の契約として扱う。

## 2. 現状と問題境界

PR #75／#76で、モバイルには「チャート・探す・予習」の専用シェル、検索、予習、詳細シート、ゴール個別解除、チャート復帰、実ブラウザ監査が導入済みである。PCは従来の上部操作、5つの表示モード、中央チャート、右ペイン、予習ワークスペースを維持している。

次の設計上の残差を解消する。

- PCの閲覧対象とモバイルのゴール選択は異なる操作であり、`selectedId`一つへ統合してはならない。
- 詳細シートは実データを表示するが、理由・設定の内容と制御は一つのシートへ統合されていない。
- `mobileAreaSheet`と詳細シートが別系統で、表示切替と詳細表示のライフサイクルが二重になっている。
- ゴール解除ボタンのCSS指定が38pxであり、可視操作全数の44px監査が必要である。
- URLは画面・ゴール・シート・検索を扱うが、tier、表示パネル、カメラ、リスト位置の責務が整理されていない。
- 検索、シート、予習操作はチャートの重い再構築を発生させてはならない。

## 3. 非目標と不変条件

次を本設計および初期実装の対象外とする。

- `data/library/`のcanonical CSV、永続レビュー履歴、作品・人物・関係IDの変更。
- 関係グラフ、世界線、時系列のトポロジーや意味論の変更。
- 公開順を関係線として扱うこと、または時系列の隣接から新しい関係を推定すること。
- 予習計算、点灯判定、人物同一性、別個体の意味論の再設計。
- ログイン、クラウド同期、ネイティブアプリ化、新しい推薦アルゴリズム。
- 公開UIへの「公式予習ルート」選択肢の再導入。内部の公式ルートデータは保持する。

公開プランは引き続き `site-proposal`（サイト提案ルート）と `complete`（完全版）の2つだけとする。全作品を探索できる原則、静的GitHub Pages、所定の配布ZIP構成、既存共有リンクと視聴済みデータを維持する。

## 4. 比較したアプローチ

| 案 | 構成 | 利点 | リスク |
| --- | --- | --- | --- |
| A | 現在のグローバル関数・DOMへ個別修正を追加 | 初期差分が小さい | `select`／`render`の多重ラップ、CSS上書き、履歴更新の重複が増える |
| **B（推奨）** | 既存意味論へのFacadeと論理モジュールを置き、PC／モバイル表示層を分離 | 既存監査を利用しつつ段階移行でき、端末ごとの操作差を表現できる | 一時的な互換アダプターが必要 |
| C | 状態管理・描画・ファイル構成を一括置換 | 最終構成は整理しやすい | 差分が大きく、UI回帰と意味論回帰を分離できない |

案Bでは、最初からフォルダを分けるのではなく、公開HTML内の関数群とDOM所有者を先に分離する。ファイル分割は、公開生成物・ロード順・既存テストの同一性を確認できる別段階とする。

## 5. 論理コンポーネントと責務

```text
ViewerApp
├─ RepositoryAdapter       作品・理由・人物・公開情報の読み取り
├─ DomainAdapter           既存の選択・ゴール・tier・視聴済み操作
├─ AppController           UIコマンドを受け状態変更へ集約
├─ NavigationController    URL・履歴・画面復帰
├─ DerivedState
│  ├─ HighlightAdapter     既存の点灯集合・線集合
│  └─ PlanAdapter          既存の予習順・進捗
├─ RenderScheduler         更新集約・revision検証・無効化
├─ ChartHost               SVG／Canvas・パネル・カメラの所有
├─ DesktopShell            Header / ViewTabs / Chart / WatchWorkspace
├─ MobileShell             TopBar / BottomNav / Chart / Search / Plan
└─ SheetHost               detail / reason / settings の唯一の表示先（docked／modal）
```

### 5.1 再利用する既存要素

- `NODES`、`nm`、`inc/out`、理由・人物データはRepositoryAdapterから読み取る。別の作品辞書を作らない。
- `selectedIds`、`selected`、既存の選択APIはDomainAdapterだけが更新する。新UIから直接変更しない。新UIは`inspectWork`、`clearInspection`、`addGoal`、`removeGoal`、`clearGoals`のコマンドを使い、互換層が必要な期間だけ旧`selectedIds`へ投影する。
- 閲覧対象の点灯は`inspection.workId`をHighlightAdapterへ渡す単一作品フォーカスとして扱い、`goals.orderedIds`の変更を伴わない。ゴール点灯は従来どおりPlan／Highlightのゴール派生結果で扱う。
- 既存の点灯・tier・予習計算はHighlightAdapter／PlanAdapterから呼び、意味論を再実装しない。
- `.panel`、`.svg-wrap`、既存SVG、CanvasキャッシュはChartHostが所有し、PC／モバイルで複製しない。
- `marvelWatchProgress`は視聴済み状態の既存所有者として再利用する。

### 5.2 移行中の所有権

各フィールドに正本を一つだけ置く。初期段階では既存処理を正本とし、共通APIは読み取りスナップショットとコマンド入口を提供する。新ストアへ移す場合はフィールド単位で移行し、旧変数は読み取り互換にする。旧変数と新ストアが双方向に購読し合う構成は採らない。

## 6. 共通状態モデル

| 状態 | 不変条件 | 保存先 |
| --- | --- | --- |
| `inspection.workId` | 閲覧中／チャートでフォーカス中の作品。ゴールでなくてもよい | 必要時にURL／履歴 |
| `goals.orderedIds` | 重複なし、順序あり | URL |
| `goals.currentId` | `orderedIds`の要素またはnull | URL |
| `navigation.surface` | `chart`／`search`／`plan` | URL |
| `navigation.chartPanel` | `overview`／`release`／`chronology`／`characters` | URLまたは表示設定 |
| `overlay` | 下記の判別共用体。`closed`／`detail`／`reason`／`settings` | URL＋履歴 |
| `search.rawQuery/filter` | ユーザー入力をそのまま保持する検索条件。正規化値は派生状態 | URL |
| `plan.tier` | `site-proposal`／`complete` | URL |
| `watched.ids` | 既存形式を維持 | localStorage／共有機能 |
| `cameraByPanel` | パネル・レイアウト版ごとの位置・倍率 | メモリ＋履歴 |
| `scrollBySurface` | 検索・予習・PCワークスペースの位置 | メモリ＋履歴 |

`inspection.workId`、`goals.currentId`、シート対象、検索結果からの移動先を`selectedId`一つにまとめない。予習リストから作品詳細を開いても、ゴール集合・現在ゴール・リスト位置は変えない。

`overlay`は次の判別共用体とし、`reason`を作品ID一つから復元しない。

```text
overlay =
  { kind: "closed" }
  | { kind: "detail", workId }
  | { kind: "reason", relationId, sourceId, targetId }
  | { kind: "settings", section? }
```

`relationId`がcanonical relationの正本であり、`sourceId`／`targetId`は表示・整合性検証用の派生値として保持する。存在しないrelationや不正な端点は開かず、`closed`へフォールバックする。

### 6.1 永続化の責務

- URLは再読み込み・共有で再現すべき画面、作品、ゴール、tier、検索条件を持つ。
- history stateはURLに加え、カメラ、スクロール、シート起点、`entryId`、`parentEntryId`、`transitionKind`を持つ。`popstate`適用中は`pushState`／`replaceState`を発生させない。
- localStorageは既存の視聴済みと表示設定に限定する。ゴールや開いているシートを暗黙に復活させない。
- カメラ座標とピクセル単位のリスト位置はURLへ入れない。
- 起動時・通常遷移の優先順位は、`popstate`スナップショット → 明示URL → localStorageの表示設定 → 組み込み既定値とする。未知のクエリと既存の`#room=...`は保持する。

履歴操作は次の規則に固定する。

| 操作 | 履歴 | 備考 |
| --- | --- | --- |
| surface変更、ゴール追加／解除、overlay新規open | `pushState` | Backで直前の意味状態へ戻れる単位 |
| 検索入力、filter変更、同一detail内のA→B、URL正規化、カメラ／スクロールsnapshot | `replaceState` | 入力1文字・1px移動で履歴を増やさない |
| `popstate`適用中 | 書き込みなし | 到着したsnapshotをそのままhydrateする |
| in-appで作ったoverlayのclose | `history.back()` | 親entryが明確な場合のみ |
| 直接リンク初期entryのoverlay close | `replaceState`でclosed | 外部ページへ意図せず戻らない |

同一detail内のA→Bは`overlay.detail.workId`だけを`replaceState`で更新する。検索・カメラ・スクロールは操作中にpushせず、surface遷移前または離脱時に現在entryへsnapshotする。

## 7. PC表示設計

優先順位は「チャートを見る → 作品を調べる → ゴールとして予習する」である。

- 上部はサイト名、検索、プラン、使い方に集約し、チャート直前の高さを圧迫しない。
- 現行の5表示モードを一列の現在地付きタブとして維持する。
- 主領域はチャートと右の詳細ペイン。右ペインは作品／接続を切り替え、閉じるとチャートを広げる。
- 詳細ペイン上部に作品名、作品情報、ゴール追加／解除、チャートへ戻るを置く。
- 複数ゴールはチャート上部の要約帯に表示し、個別解除と全解除を区別する。
- OR／AND／PATHは複数ゴール時の追加設定としてまとめる。
- ズーム・全体表示・選択へ戻るはチャート内の固定位置に置き、詳細開閉では自動fitしない。
- 予習ワークスペースはページフローに残し、チャートからスクロールで到達できる。戻る操作は直前のパネル、カメラ、選択を復元する。

PCの5表示モードと共通状態の対応は次のとおりとする。

| PC表示 | 共通状態 |
| --- | --- |
| 関係地図 | `surface=chart, chartPanel=overview` |
| 公開順 | `surface=chart, chartPanel=release` |
| 世界線・時系列 | `surface=chart, chartPanel=chronology` |
| この作品を見るなら | `surface=plan`（`watchWorkspace`） |
| 人物・組織 | `surface=chart, chartPanel=characters` |

`surface=search`はPCでは検索結果を主領域またはSheetHostのdocked右ペインに表示し、チャートパネルを変更しない。幅をまたいでもsemantic stateは保持し、`surface=plan`はPC④、モバイル「予習」へ、`surface=chart`は`chartPanel`に対応する表示へ写像する。

PCの作品クリックは`inspection.workId`だけを変更する。ゴール追加／解除は明示ボタンから行い、右クリックは補助操作に限定する。同じ作品の再クリックは閲覧フォーカスだけを解除し、ゴールを解除しない。背景クリックも`inspection.workId=null`だけを行い、全ゴール解除は独立ボタンからのみ実行する。これは既存の「再クリックでゴール解除」契約を意図的に置き換えるため、旧契約テストは削除せず、移行を示す新RED／GREENへ置き換える。

## 8. モバイル表示設計

下部ナビは「チャート」「探す」「予習」の3面を維持する。表示パネル切替を下部ナビへ増やさない。

### 8.1 チャート

- 上部は現在の表示名、検索入口、短いゴール要約に限定する。
- 全作品を探索可能にし、作品タップでは点灯結果を先に見せる。詳細を自動で全画面表示しない。
- 1本指パン、2本指ズーム、再タップで`inspection`解除、背景クリックで`inspection`解除、ドラッグ後のフォーカス維持を契約にする。ゴールの追加／解除はノード上または詳細・要約上の明示操作で行う。
- 「全体」「選択へ」は常設し、表示パネル切替・凡例・設定はSheetHostへ集約する。
- 複数ゴールは要約から一覧を開き、長いチップを常設しない。

### 8.2 探す

- 検索欄、結果件数、必要時に開く絞り込みの順で配置する。
- カードには邦題、英題、公開情報、系統を表示する。
- 「チャートで見る」「ゴールに追加／外す」「詳細」を別操作として表示する。「選択」一語に複数の意味を持たせない。
- 検索語・絞り込み・リスト位置を保持し、該当なしから条件解除へ導く。

### 8.3 予習

- ゴール、2プラン、視聴済み数、残り時間を先頭にコンパクトに表示する。
- リストは番号、邦題、公開情報、視聴済みチェックを中心にする。
- 個別解除、全解除、元に戻すを区別し、解除ボタンを実測44px以上にする。
- 視聴済み変更で行を削除・並べ替えせず、位置とフォーカスを維持する。
- 「チャートへ戻る」と「この作品をチャートで見る」を区別する。

## 9. SheetHost設計

PC／モバイルの切替でも破棄されない唯一のSheetHostを設け、`mobileAreaSheet`を含む表示切替、詳細、理由、設定を同じ制御下へ移す。PC右ペインは別のdetail所有者ではなく、SheetHostの`docked` presentationである。モバイルでは同じ内容を`modal` bottom sheetとして描画する。

- `detail`: 作品ID、邦題・英題、公開情報、登録済み詳細、ゴール操作、公式ソース、チャート移動。
- `reason`: source／target／reason ID、既存の関係種別と根拠。時系列隣接から理由を生成しない。
- `settings`: 表示パネル、公開2プラン、既存の複数ゴール設定、凡例。内部専用の公式ルート選択は公開しない。

シートは`closed | detail | reason | settings`のいずれか一つで、`docked`と`modal`の表示モードを持つ。`modal`時だけ`aria-modal`、フォーカストラップ、backdrop、背景`inert`、背景スクロール固定を有効にする。`docked`時は常設Inspectorとして扱い、`aria-modal`、backdrop、focus trapを付けない。両方ともEscape、明示閉じる、起点復帰を実装する。シート内で対象作品をAからBへ変える操作は、同一detailの内容更新として扱い、`replaceState`で不要な履歴を増やさない。ブラウザ戻る／進むでは到着した履歴をそのまま適用し、履歴を書き換えない。

背景クリックはシートを閉じるだけで、背後チャートの選択解除へ伝播させない。閉じた後は元のボタン、作品カード、画面見出しの順でフォーカス復帰先を探す。

backdrop closeは、`pointerdown`と`pointerup`の両方がbackdrop自身だった場合だけ成立させる。シートから始まったdragやpointer sequenceを背景クリックと誤認しない。直接リンクの初期entryを閉じる場合は`replaceState`、アプリ内openのentryを閉じる場合は親entryが一致するときだけ`history.back()`を使う。

## 10. 描画パイプラインと性能

```text
ユーザー操作
  → AppController
  → 状態を一括更新
  → 変更項目を判定
  → 必要な派生結果だけ計算
  → RenderScheduler（rAF／revision）
  → アクティブな表示面だけ更新
```

- ゴール点灯、詳細点灯、予習順、視聴進捗を別の派生結果として扱う。
- 検索、シート開閉、視聴済みチェック、ゴール個別解除で`fitView`、SVG生成、Canvasキャッシュ再構築を呼ばない。
- カメラ操作・表示更新は1フレーム1予約へ集約する。
- 非表示面の予約を取り消し、古いrevisionの結果が新状態を上書きしないようにする。
- SVG／Canvasは各パネル1実体とし、PC・モバイルで同じ図を複製しない。
- 既存のCanvas画素予算を不用意に増やさない。性能値は同条件で測定してから予算化する。

変更項目ごとの無効化範囲を固定し、不要な`render()`／`fitView()`を呼ばない。

| 変更 | 更新対象 | 更新しないもの |
| --- | --- | --- |
| `search.rawQuery`／filter | Search DOM、件数 | ChartHost、camera、Canvas cache |
| `overlay` | SheetHost | ChartHost、camera、goals |
| `watched.ids` | Plan DOM、進捗表示 | ChartHost、camera、goal集合 |
| `inspection.workId` | 点灯フォーカス、Inspector／detail要約 | Plan順、goal集合 |
| `goals.*` | ゴール点灯、Plan、要約 | 検索条件、既存camera（明示「選択へ」以外） |
| `navigation.chartPanel` | パネル表示（初回のみlazy build可） | 他パネルのSVG／Canvas、goal集合 |

## 11. レスポンシブとアクセシビリティ

- 第1段階は既存の`760px`境界を維持する。
- `761–980px`はコンパクトPCとして右ペインを必要時に開き、`981px`以上はチャート＋右ペインを基本とする。
- Shell判定はCSS、JavaScript、ブラウザ監査で同じcanonical predicateを使う。`shortSide=min(innerWidth,innerHeight)`、`longSide=max(...)`、`coarse=matchMedia('(pointer: coarse)').matches`として、`mobileShell = innerWidth <= 760 || (shortSide <= 760 && coarse && longSide <= 1280)`、それ以外では`761–980`をcompact PC、`981`以上をPCとする。UA文字列へ依存しない。
- 期待値は`390×844=mobile`、`844×390=mobile`、`760×844=mobile`、`761×844=compact PC`、`980×844=compact PC`、`981×844=PC`と固定する。タッチ主体の横向き端末でもPCとモバイルのshellを同時表示しない。
- 390×844では上部バー、主領域、下部ナビをsafe-area込みで配置する。多重な固定`dvh`計算を増やさない。
- すべてのボタン、ゴール解除、閉じる、チェックラベルを実測44px以上にする。
- Canvasだけに情報を閉じず、検索・作品一覧・関連一覧からキーボード操作でも同じ作品へ到達可能にする。
- 色だけで前史・後続・選択を伝えず、方向ラベル、枠、凡例を併用する。
- `aria-current`、`aria-modal`、短い`aria-live`通知、動きを減らす設定を適用する。
- チャート、検索／予習、シートごとにスクロール所有者を一つにする。

## 12. 状態遷移と受け入れ条件

| 操作 | 変わる状態 | 保持する状態 |
| --- | --- | --- |
| PC作品クリック | `inspection.workId` | ゴール、tier、カメラ |
| モバイル作品タップ | `inspection.workId`（同一作品なら`null`） | ゴール、tier、カメラ |
| ゴールに追加／解除 | `goals.orderedIds/currentId` | 閲覧対象、検索条件 |
| チャート→探す／予習 | `navigation.surface` | 選択、ゴール、tier、カメラ |
| 予習→チャート | `navigation.surface` | 予習位置、ゴール、直前カメラ |
| 詳細／理由／設定 | `overlay` | 背後の画面・選択・ゴール |
| 戻る／進む | 履歴スナップショット全体 | 新しい履歴を作らない |

ゴール削除時に`goals.currentId`を削除した場合は、同じ`orderedIds`の直前要素、なければ次要素、どちらもなければ`null`の順で決定する。この規則はPC・モバイル・履歴復元で共通とする。

完了条件は次のとおり。

1. チャート・探す・予習の3面を切り替えられる。
2. どの面からも共通のゴール・点灯状態になる。
3. 閲覧フォーカス、再タップ解除、背景解除、ドラッグ後の保持が新しい契約どおり動き、ゴール追加／解除は明示操作だけで行われる。
4. detail／reason／settingsを単一シートで扱い、戻る操作が予測可能である。
5. URL／履歴から画面、作品、ゴール、検索条件を復元できる。
6. 検索・予習・シート操作で不要なチャート再構築が発生しない。
7. 760／761px、980／981px、390×844、844×390でcanonical predicateどおりのshellになり、重複UI、文字被り、タッチ領域不足、スクロール不能がない。
8. 全131作品×公開2プランの点灯集合、公開順の合成線ゼロ、既存時系列表示契約が維持される。
9. PC、canonical data、関係・世界線・時系列の意味論に回帰がない。

## 13. 段階的実装計画とテスト

### Phase 0 — 現状固定

PC閲覧・ゴール、検索→チャート、履歴、境界幅の観測契約を追加する。特に、(a)ゴール`[A,B]`を保持したまま作品Cの詳細を開いて`inspection`だけが変わる、(b)「チャートで見る」は`inspection`だけ、「ゴールに追加」は`goals`だけを変える、(c)旧再クリック＝ゴール解除契約を意図的に置き換える、のRED／GREENを先に固定する。テスト追加のみで、失敗時のロールバック境界はテストコミットとする。

### Phase 1 — 共通API境界

UIが状態を二重更新しないこと、閲覧対象・ゴール順序・現在ゴールが独立していることをRED化する。見た目とcanonical dataは変更しない。

### Phase 2 — ナビゲーション・履歴

tier／panel、直接リンク、戻る／進む、シート対象、カメラ復帰を追加する。reasonのrelation round-trip、`closed → detail A → close → Back/Forward`、直接detailリンクのclose、detail A→Bのreplace、検索20文字入力・連続pan・長いscrollで履歴が増殖しないことを実ブラウザで確認する。`popstate`適用中のhistory書き込み回数は0とする。

### Phase 3 — 単一シート

二重モーダル禁止、detail／reason／settingsの実内容、38px解除修正、対象変更、フォーカス復帰、背景伝播防止を実装する。docked PCでは`aria-modal`／focus trap／backdropなし、modal mobileでは`inert`／scroll lock／focus trapありを監査する。backdropはpointerdown／pointerupの両方がbackdrop自身の場合だけ閉じる。

### Phase 4 — 検索・予習更新

検索入力、視聴チェック、ゴール解除でチャート再構築がゼロであること、長いリストの位置・フォーカスが維持されることを監査する。

### Phase 5 — PC・境界・横向き

5表示と`surface/chartPanel`対応、右ペイン、中間幅、横向き、タッチ主体PCを監査し、canonical predicate、シェル二重表示、カメラ・ゴール・active panelの消失を防ぐ。390×844、844×390、760、761、980、981の全ケースを対象にする。

### Phase 6 — 旧層撤去と統合

旧シート、不要CSS、重複ハンドラを一つずつ確認して撤去する。全unit、build、選択、操作、時系列、公開順、モバイル監査、canonical差分、Pages公開を確認する。

各Phaseは通常PRとして独立し、失敗時に直前の表示層へ戻せる。編集用ソース分割はPhase 6後の任意作業とし、公開ZIPの構造を変えない。

## 14. 変更しないもの

- canonical CSV、永続レビュー履歴、作品・人物・関係ID。
- 関係グラフ、世界線、時系列の既存トポロジーと意味論。
- 公開順からの関係線生成、公開日精度、未定情報の扱い。
- 予習計算、点灯判定、人物・別個体の解釈。
- `site-proposal`／`complete`の2プランと、内部公式ルートの非公開境界。
- 全作品探索、静的GitHub Pages、共有リンク、視聴済みデータ、配布ZIP構成。

## 15. 未解決事項

実装開始を止める設計上の未解決事項は、レビュー反映により解消した。作品クリックは閲覧フォーカス、ゴール操作は明示操作、reasonはrelation ID、PC右ペインはSheetHostのdocked表示、横向き判定はcanonical predicateとして固定する。実装前にPhase 0のRED／ブラウザ監査を追加し、旧契約との差分を意図的変更として記録する。ユーザー向けの追加確認は、代表フローとして「チャートから探索」と「検索から予習」のどちらを先に手触り確認するかだけとする。
