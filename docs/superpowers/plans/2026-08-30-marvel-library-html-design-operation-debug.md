# Marvel Library HTML design and operation debugging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate and document the v5.20.7 watch-plan interaction boundary so that the three viewing tiers, official prewatch provenance, route highlighting, and chart return behavior remain understandable on desktop and mobile.

**Architecture:** The static HTML viewer continues to consume the committed DB-derived JSON export. Canonical CSVs and persistent audit ledgers remain unchanged; the viewer owns only presentation state such as tier selection, watch-plan navigation, and temporary SVG/canvas highlighting. Official prewatch metadata is read from the versioned view policy and is shown separately from curated fallback routes.

**Tech Stack:** Static HTML/CSS/JavaScript, versioned `data/derived/flowchart.json`, bundled Codex Python runtime, `unittest`, and the in-app browser static-server smoke test.

**Spec:** `docs/superpowers/specs/2026-08-29-marvel-library-db-v1-html-db-export-design.md`

## Global Constraints

- Keep the provisional minimum tier direct-core-only; it must not recursively expand the graph.
- Keep recommended mode official-route-first, with an explicit curated/connection-table fallback when no official route is registered.
- Keep complete mode recursive for core/recommended edges while treating reference edges as direct context only.
- Keep the watch plan and chart in the same document flow so `↑ チャートへ戻る` remains usable after opening the plan.
- Do not infer canonical release/status facts, graph edges, territory, production milestones, or universe identities from UI behavior.
- Do not modify canonical CSVs or persistent `data/content_audit/reviews.csv` during ordinary viewer work.

---

### Task 1: Freeze the UI regression contract

**Files:**
- Modify: `tests/library_v5/test_watch_scroll_navigation.py`
- Read: `data/prewatch_policy.json`, `data/prewatch_official_routes.json`, `data/derived/flowchart.json`

**Interfaces:**
- The test contract checks the existing HTML hooks and exported view-policy shape; it does not execute browser JavaScript or mutate canonical data.

- [x] **Step 1: Assert the navigation and tier invariants**

  Keep assertions for chart-in-document-flow, chart return hooks, direct-core minimum semantics, and the three synchronized tier labels.

- [x] **Step 2: Assert provenance and route-highlight hooks**

  Assert the official/curated provenance boundary, the registered Thunderbolts route, the route toggle, stable route IDs, and the redraw overlay hook.

- [x] **Step 3: Run the focused contract**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_watch_scroll_navigation -v
  ```

  Expected: every contract test passes.

### Task 2: Verify official prewatch presentation

**Files:**
- Read: `index.html`
- Read: `data/prewatch_official_routes.json`
- Read: `data/derived/flowchart.json`

**Interfaces:**
- `chooseOfficialPrewatchRoute(goalId)` supplies the route and provenance used by `updatePreparationPlan()`.
- `toggleOfficialRouteHighlight(enabled)` applies temporary classes only to existing SVG nodes and edges.

- [x] **Step 1: Confirm route ordering and provenance**

  Confirm that the Thunderbolts route is ordered before graph expansion, carries its official source URL and checked date, and renders an official provenance badge.

- [x] **Step 2: Confirm highlight scope**

  Confirm that highlighting uses existing route edges only, preserves the selected goal styling, and is reapplied after detail-focus redraws.

- [x] **Step 3: Confirm fallback wording**

  Confirm that a goal without a registered official route is labeled as an editorial/connection-table fallback and is not presented as an official required list.

### Task 3: Execute desktop and mobile interaction smoke checks

**Files:**
- Read: `index.html`
- Read: `docs/superpowers/reviews/2026-08-30-marvel-library-html-design-operation-debug.md`

**Interfaces:**
- Desktop static-server URL: `http://127.0.0.1:8765/index.html`.
- Required observable state: loaded status, goal selection, plan navigation, route toggle state, and chart-return state.

- [x] **Step 1: Check desktop loading and tier switching**

  At a 1280px viewport, verify the 131-work loaded status, switch `最低限 / おすすめ / 完全版`, and confirm the active control and plan tier label agree.

- [x] **Step 2: Check multiple goals and official route highlighting**

  Add Doomsday and Thunderbolts as goals, verify the `公式＋編集ルート` provenance, activate the official route button, and observe four highlighted route edges and three route-only nodes without creating new graph edges.

- [x] **Step 3: Check chart return and watched state**

  Open the watch plan, return with `↑ チャートへ戻る`, and verify the chart remains reachable; check and clear one watched item and verify the progress text updates.

- [x] **Step 4: Check mobile navigation**

  At 393×873, verify the goal bar, `予習プランを見る`, plan-to-chart return, and preservation of the selected goal without an overlay or focus trap regression.

### Task 4: Full verification and audit handoff

**Files:**
- Read: `AGENTS.md`
- Read: `README.md`
- Create: `docs/superpowers/reviews/2026-08-30-marvel-library-html-design-operation-debug.md`

- [x] **Step 1: Run the bundled full suite and build**

  ```powershell
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

  Expected: all tests pass, audit and review issue counts are zero, SQLite foreign keys are zero, and integrity is `ok`.

- [x] **Step 2: Inspect and remove only known generated outputs**

  Remove the build-generated audit/DB paths listed in `AGENTS.md`; keep canonical CSVs, `reviews.csv`, and the committed flowchart export untouched.

- [x] **Step 3: Record the review and leave the branch clean**

  Record the branch SHA, smoke observations, semantic boundaries, test/build output, and the remaining limitation that browser scenarios are manual rather than a headless DOM regression suite.
