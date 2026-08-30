# Marvel Library DB v1 全作品 release/status evidence audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全131作品のrelease/status factを監査し、直接証拠があるものだけを小さな検証済みバッチとして昇格し、残りを理由付きで保留する。

**Architecture:** canonical CSVを唯一の事実源とし、evidence/review/applied recordを同じバッチで更新する。読み取り専用監査はsource群で並列化するが、canonical書き込みと統合はprimary agentが直列に行う。release/status metadataはgraph derivationから独立させる。

**Tech Stack:** Python bundled runtime、unittest、CSV、SQLite compiler/build、GitHub PR workflow。

**Spec:** docs/superpowers/specs/2026-08-30-marvel-library-db-v1-full-release-status-audit-design.md

## Global Constraints

- `source_verified` factには個別fact_idを指すprimary/supporting evidenceと `legacy_seed -> source_verified` review transitionを必ず追加する。
- announced/released、asserted_at、territory、JP date、production milestoneを混同・推測しない。
- release/status factsからwork relation、event、transition、appearance、portrayal、identity、Earth番号を派生させない。
- 同じcanonical CSVを複数エージェントが同時編集しない。subagentはread-only監査に限定する。
- 各promotion batchは原則1–5 facts、RED test先行、focused test→全suite→build→strict CSV shapeの順で検証する。
- 既存graph互換性（361 edges、569 reasons、199 prewatch、83/83 paths）を維持する。

---

### Task 1: 全seed fact inventoryと監査台帳

**Files:**
- Create: `scripts/library_v5/release_status_inventory.py`
- Create: `tests/library_v5/test_release_status_inventory.py`
- Create: `docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md`
- Modify: none

**Interfaces:**
- Consumes: `data/library/releases.csv`, `data/library/production_status_assertions.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, `data/library/sources.csv`。
- Produces: deterministic CSV/Markdown inventory with one row per fact and disposition fields `promote`, `defer`, `conflict`。

- [x] **Step 1: Write the failing test**

テストは131作品のstatus 131行とrelease 138行を読み、inventoryが269 factsを返し、各行にfact_id、fact_table、work_id、verification_status、source候補、evidence_count、review_count、disposition列があることを要求する。source_verified済み行はdisposition=promote、未昇格行はpromote/defer/conflictのいずれかを明示する。

- [x] **Step 2: Run test to verify it fails**

Run: `& $MarvelPython -m unittest tests.library_v5.test_release_status_inventory -v`
Expected: inventory moduleまたは出力契約が未実装のためFAIL。

- [x] **Step 3: Write minimal implementation**

`release_status_inventory.py` にCSV reader、fact/evidence/reviewのexact ID join、source候補集計、安定したfact sort、Markdown/CSV出力を実装する。入力CSVは変更せず、出力は指定された監査レビューへ書く。

- [x] **Step 4: Run test to verify it passes**

Run: `& $MarvelPython -m unittest tests.library_v5.test_release_status_inventory -v`
Expected: PASS、release 138/status 131の全269 factsが一意に出力される。

- [x] **Step 5: Commit**

`git add scripts/library_v5/release_status_inventory.py tests/library_v5/test_release_status_inventory.py docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md`
`git commit -m "audit: inventory all release-status seed facts"`

### Task 2: source群別の読み取り専用証拠監査

**Files:**
- Modify: `docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md`
- Create: SDD workspace reports for Marvel Studios/Marvel Television、Sony/Spider-Verse、その他の地域・配信ソース
- Modify: canonical CSVなし

**Interfaces:**
- Consumes: Task 1 inventoryと各source URL/checked_point。
- Produces: factごとの `promote`、`defer`、`conflict` disposition、直接支持の引用要約、再監査条件。

- [x] **Step 1: 三つのread-only subagent監査を並列実行する**

Marvel Studios/Marvel Television、Sony/Spider-Verse、その他の地域・配信群をそれぞれgpt-5.6-luna/xhighで監査する。各agentはcanonicalを編集せず、fact_id単位でsourceがstatus/releaseを直接支持するかだけを報告する。

- [x] **Step 2: Primary agentが台帳を統合する**

同一factの重複報告をdeduplicateし、source登録だけの行、別factのevidenceだけの行、地域不一致を `defer` または `conflict` として記録する。

- [x] **Step 3: 監査台帳を検証する**

Run: `& $MarvelPython -m unittest tests.library_v5.test_release_status_inventory -v`
Expected: 269 factsすべてにdispositionと理由があり、未昇格行が暗黙にverified扱いされない。

- [x] **Step 4: Commit**

`git add docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md`
`git commit -m "audit: classify release-status evidence dispositions"`

### Task 3: 同一一次ソースによるverified promotion wave

**Files:**
- Create: `tests/library_v5/test_release_status_full_audit_wave.py`
- Modify: `data/library/releases.csv` または `data/library/production_status_assertions.csv`（監査台帳のpromote行のみ）
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`
- Create: `data/content_audit/applied/YYYY-MM-DD-release-status-evidence-promotion-batchNNN.json`
- Modify: cumulative promotion tests

**Interfaces:**
- Consumes: Task 2で `promote` と分類された最大5 factsと、各factのsource/evidence要約。
- Produces: exact fact/evidence/review IDsを持つsource_verified rows、適用ハッシュ、graph fingerprint parity。

- [x] **Step 1: REDテストを書く**

各waveのテストは対象factが変更前はlegacy_seed、対応evidence/reviewが存在しないこと、JP行・関連graph行が対象外であることを固定する。既存のbatch001–007 cumulative testsと同じexact ID契約を使う。

- [x] **Step 2: REDを確認する**

Run: `& $MarvelPython -m unittest tests.library_v5.test_release_status_full_audit_wave -v`
Expected: 対象factの未昇格状態によりFAIL。

- [x] **Step 3: 最小データ変更を適用する**

対象factだけをsource_verifiedへ更新し、同じfact_idを指すprimary/supporting evidence、legacy_seed -> source_verified review、applied JSONのrow countsとSHA-256を追加する。statusのannounced/released、asserted_at、territory、JP blank dateは変更しない。

- [x] **Step 4: focused GREENを確認する**

Run: `& $MarvelPython -m unittest tests.library_v5.test_release_status_full_audit_wave -v`
Expected: PASS。

- [x] **Step 5: 全体検証を実行する**

Run: `& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v` と `& $MarvelPython -m scripts.library_v5.build --repo-root .`
Expected: 全テストPASS、audit/content-audit issue 0、FK 0、SQLite integrity ok、graph compatibility unchanged。

- [x] **Step 6: Commit**

`git add data/library data/content_audit tests/library_v5 docs/superpowers/reviews`
`git commit -m "audit: promote evidence-backed release-status wave NNN"`

### Task 4: defer/conflictの全件記録

**Files:**
- Modify: `docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md`
- Create: `data/content_audit/applied/YYYY-MM-DD-release-status-audit-dispositions.json`
- Modify: canonical CSVなし（保留理由をfact notesへ書く必要がある場合は別reviewを先に追加）

**Interfaces:**
- Consumes: Task 2のdefer/conflict report。
- Produces: 269 factsの最終disposition集計、再監査条件、未昇格件数。

- [x] **Step 1: disposition集計を固定する**

台帳にverified/promote/defer/conflictの件数、fact ID一覧、理由、必要な次回証拠を記録する。statusがlegacy_seedのままでも、監査済みであることをapplied JSONに記録する。

- [x] **Step 2: invariantテストを追加する**

verifiedでないfactにevidence/reviewがないことをエラーにせず、promote済みfactには両方が必須であること、JP blank dateが補完されていないことを検証する。

- [x] **Step 3: Commit**

`git add docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md data/content_audit/applied`
`git commit -m "audit: record full release-status dispositions"`

### Task 5: branch全体レビューとmain統合

**Files:**
- Modify: `AGENTS.md`
- Modify: `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`
- Modify: `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`
- Modify: `docs/superpowers/reviews/2026-08-28-marvel-library-db-v1-releases-production-status-review.md`

**Interfaces:**
- Consumes: Tasks 1–4のinventory、promotion batches、defer/conflict ledger、full verification output。
- Produces: 新しいsemantic baseline、全作品監査完了記録、次のUI/debug boundary。

- [ ] **Step 1: 最終検証を実行する**

Run: `& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v` と `& $MarvelPython -m scripts.library_v5.build --repo-root .`。strict CSV shape、logical determinism、graph compatibility、protected input hashも確認する。

- [ ] **Step 2: 全branch差分をレビューする**

canonical変更がpromote dispositionと一致し、defer/conflict行を誤ってsource_verifiedにしていないことを確認する。review integrity issueが1件でもあればmergeしない。

- [ ] **Step 3: PRを作成・統合する**

PR bodyにpromote/defer/conflict件数、全テスト/build結果、graph compatibility、Pages影響を記載する。通常のPR経路でmainへ統合し、main HEADと主要fact countsを再確認する。

- [ ] **Step 4: Docs baselineを更新する**

AGENTS、handoff、roadmap、historical reviewにsemantic baseline SHA、CI run、fact counts、deferred scopeを反映する。

- [ ] **Step 5: Commit**

`git commit -m "docs: record full release-status audit baseline"`

