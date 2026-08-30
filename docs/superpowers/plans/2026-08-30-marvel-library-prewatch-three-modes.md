# Marvel Library prewatch three modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 公開予習プランを「公式予習ルート」「サイト提案ルート」「完全版」の3つに分離し、互いの出典と探索範囲を混同させない。

**Architecture:** 公式ルートは登録済みの監査済みルートだけを返し、未登録時は空状態を明示する。サイト提案はcurated routeとcore前史を使い、完全版はcore/recommendedのグラフ再帰と直接referenceだけを使う。チャートのimportance selectorは予習プランの選択とは独立した状態にする。

**Tech Stack:** 静的HTML/JavaScript、JSON/CSV正本、Python unittest、既存のlibrary_v5 build。

**Spec:** `data/prewatch_policy.json` と `data/README.md` の公開3モード契約。

## Global Constraints

- 公式未登録時にサイト提案へ無言でフォールバックしない。
- 完全版へ公式／サイト提案route IDや出典URLを混入させない。
- 旧 `minimum` / `recommended` 共有状態は `site-proposal` として読み込む。
- チャートは全接続を表示し、予習モード変更でimportance表示を変えない。
- canonical CSVの意味論は変更せず、既存の監査・DBビルドを通す。

### Task 1: RED contract

**Files:**
- Modify: `tests/library_v5/test_watch_scroll_navigation.py`

- [x] **Step 1: Write the failing tests** — 3つのselect値、公式非フォールバック、サイト提案の公式非依存、完全版のroute非混入、旧値正規化、チャートselect独立を固定した。
- [x] **Step 2: Run the focused tests** — 旧実装で新しい5契約が失敗することを確認した。

### Task 2: Planner and selector implementation

**Files:**
- Modify: `index.html`

- [x] **Step 1: Add explicit mode normalization and builders** — `official`、`site-proposal`、`complete`を正規化し、公式未登録を独立状態として扱った。
- [x] **Step 2: Separate chart importance controls** — chart selectorをwatch selectorから分離し、importance変更を`marvelSetImportanceMode`へ移した。
- [x] **Step 3: Remove complete route mixing** — 完全版はgraph recursionと直接referenceだけを使い、公式／サイト提案のroute metadataを引き継がないようにした。
- [x] **Step 4: Run focused tests** — 25件のwatch navigation contractをGREENにした。

### Task 3: Policy and documentation synchronization

**Files:**
- Modify: `data/prewatch_policy.json`
- Modify: `data/README.md`
- Modify: `data/rules.csv`
- Modify: `data/schema.json`
- Modify: `data/manifest.json`
- Modify: `README.md`

- [x] **Step 1: Publish the three-mode policy** — public tiersとlegacy compatibilityを明示した。
- [x] **Step 2: Update user-facing documentation and hashes** — 3モード、非フォールバック、完全版の分離を記録し、manifest hashを更新した。

### Task 4: Full verification

**Files:**
- Generated transient outputs only under `data/content_audit/` and `data/derived/` during build.

- [x] **Step 1: Run the bundled Python build** — audit 0、content audit 0、prewatch 199、story path 83/83、DB works 131を確認した。
- [x] **Step 2: Run the complete unittest suite and clean generated outputs** — 変更後の全テストとworktree-clean確認を行う。
