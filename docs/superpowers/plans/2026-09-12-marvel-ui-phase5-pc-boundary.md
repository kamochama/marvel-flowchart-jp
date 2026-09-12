# Marvel UI Phase 5 PC／境界／横向き Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PC・コンパクトPC・モバイルのshell判定を一つのcanonical predicateへ揃え、境界幅・横向きタッチ端末・キーボードによる高さ変化で表示層と操作状態が壊れないことを実ブラウザで保証する。

**Architecture:** 既存の作品データ、選択、ゴール、カメラ、SheetHostを変更せず、`<html data-shell>`をshell判定の正本にする。安定したlayout width／screen短辺長辺／coarse入力だけで判定し、orientation／layout width変更時だけ再評価する。既存の760px以下のmobile shell、761–980pxのcompact PC、981px以上のdesktopを段階的に同じ判定へ接続し、visual viewportの高さ変更では状態を書き換えない。

**Tech Stack:** 単一HTML、CSS media/data attributes、既存のNode/CDPブラウザ監査、Python `unittest`、Bundled Codex Python runtime。

**Spec:** `docs/superpowers/specs/2026-09-09-marvel-pc-mobile-ui-architecture-design.md` §11–§13 Phase 5

## Global Constraints

- Canonical CSV、persistent review ledgers、作品・人物・関係ID、点灯意味論は変更しない。
- `mobileShell = layoutWidth <= 760 || (screenShortSide <= 760 && coarse && screenLongSide <= 1280)` を唯一のmobile predicateとする。
- `761–980px` はcompact PC、`981px`以上はdesktop。`innerHeight`／`visualViewport.height`／UA文字列をshell判定に使わない。
- 既存の`site-proposal`／`complete`、SheetHost、camera、goals、active panelの契約を維持する。
- 実装はREDテストを先に追加し、失敗を確認してから最小実装を行う。

---

### Task 1: Canonical shell synchronization contract

**Files:**
- Modify: `tests/library_v5/test_ui_architecture_contract.py`
- Modify: `tests/library_v5/test_mobile_shell_contract.py`
- Modify: `index.html` (viewer UI state facade and shell lifecycle)

**Interfaces:**
- Produces `window.marvelReadShellMetrics()` and `window.marvelSyncShell(options)` for browser/runtime use.
- `<html data-shell="mobile|compact|desktop">` is the CSS and audit source of truth.

- [x] **Step 1: Write the failing static/runtime tests** for shell sync, stable metrics, no visual-viewport height dependency, and exact boundary values `390×844`, `844×390`, `760`, `761`, `980`, `981`.
- [x] **Step 2: Run the focused tests** and confirm they fail because the current classifier is not connected to `data-shell` and has no runtime sync contract.
- [x] **Step 3: Implement the smallest synchronization layer**: normalize metrics, set `document.documentElement.dataset.shell`, expose the reader/synchronizer, and schedule reevaluation only from initial load plus layout/orientation changes. Keep existing state objects intact.
- [x] **Step 4: Run the focused tests** and confirm GREEN.
- [x] **Step 5: Inspect the diff** to verify no canonical data or unrelated generated output changed.

### Task 2: Boundary and orientation browser audit

**Files:**
- Modify: `tests/library_v5/browser_mobile_shell_audit.mjs`
- Modify: `tests/library_v5/test_browser_mobile_shell_audit.py`

**Interfaces:**
- Browser runner reports `shell`, `dataShell`, viewport dimensions, active surface, focus, camera, goals, and history deltas.
- The audit covers portrait/landscape phone, exact width boundaries, compact PC, desktop, and coarse 761–1280px keyboard-height shrink.

- [x] **Step 1: Add RED scenarios** using CDP `Emulation.setDeviceMetricsOverride` and `Emulation.setTouchEmulationEnabled`, asserting canonical shell and no duplicate mobile/desktop roots.
- [x] **Step 2: Run the opt-in browser audit** and confirm the new scenarios fail against current behavior, especially landscape touch phone and `data-shell` absence.
- [x] **Step 3: Wire the runner to the real shell sync** and assert focus, `surface`, camera token, and selected goal IDs are unchanged after a visual viewport-height-only update.
- [x] **Step 4: Run the browser audit** and confirm all new scenarios pass with zero failures.
- [x] **Step 5: Update the Python contract** to require the JSON fields and failure semantics so CI cannot silently omit the cases.

### Task 3: Compact PC and responsive presentation guardrails

**Files:**
- Modify: `index.html` (data-shell CSS and resize/orientation lifecycle)
- Modify: `tests/library_v5/test_mobile_ux_contract.py`
- Modify: `tests/library_v5/test_mobile_shell_contract.py`

**Interfaces:**
- `[data-shell="mobile"]` owns mobile-only shell visibility; `[data-shell="compact"]` keeps one desktop/compact chart and an on-demand right pane; `[data-shell="desktop"]` keeps the full docked layout.

- [x] **Step 1: Add RED static CSS contracts** for no simultaneous shell visibility, compact layout width, orientation-safe chart sizing, and no fixed-height calculation from keyboard-sensitive viewport height.
- [x] **Step 2: Run focused static tests** and record expected failures.
- [x] **Step 3: Add minimal data-shell selectors and lifecycle hooks** without duplicating SVG/Canvas or changing graph data.
- [x] **Step 4: Run focused static and existing browser tests** and confirm GREEN.
- [x] **Step 5: Verify touch targets, text wrapping, sheet presentation, and scroll ownership remain covered by existing contracts.**

### Task 4: Full verification and handoff

**Files:**
- Modify: `docs/superpowers/plans/2026-09-12-marvel-ui-phase5-pc-boundary.md`
- Modify: `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`
- Modify: `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`

- [x] **Step 1: Run the bundled full unit suite and deterministic build.**
- [x] **Step 2: Run selection, interaction, chronology, publication-order, and mobile-shell browser audits with the required environment flags.**
- [x] **Step 3: Inspect `git diff --check`, canonical CSV diff, audit issue counts, SQLite integrity, and generated-output boundaries.**
- [ ] **Step 4: Commit the feature branch, push, open the normal PR, and wait for all required checks.**
- [ ] **Step 5: Merge only after CI is green, verify `main` and Pages/public HTTP behavior, and record the Phase 5 production baseline in the handoff and roadmap.**

## Execution record

- RED/GREEN: the focused shell contracts were added first; the canonical runtime sync and data-shell selectors then passed the focused tests.
- Local verification: 582 unit tests passed (5 environment-gated skips); deterministic build reported zero audit issues, zero content-audit issues, SQLite integrity `ok`, 131 works, 355 edges, and 562 pair reasons.
- Real Chrome/CDP verification: selection `0` mismatches, interaction `6/6`, chronology `0` failures, publication order `131` cards / `0` failures / `0` synthetic edges, and mobile shell boundary/orientation audit passed.
- Scope: viewer shell classification and audit contracts only; canonical CSVs, persistent review ledgers, graph semantics, and work IDs were unchanged.
