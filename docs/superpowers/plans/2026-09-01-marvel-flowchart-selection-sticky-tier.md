# Marvel Flowchart Selection, Sticky Guide, and Shared Tier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make chart deselection, desktop sticky navigation, and the three public connection tiers consistent between the chart and watch plan while keeping every database edge rendered.

**Architecture:** Keep `importance` as edge metadata and retain the existing database/export payload. Introduce one chart-facing tier state that reuses `buildMultiGoalPlan` to derive backward route nodes/edges; retain existing forward and scope traversal as an independent axis. Keep the header controls in normal document flow and place only the guide/tabs in a separate `.public-nav-sticky` viewport-top layer, with a pointer gesture guard so only a genuine background click clears goals.

**Tech Stack:** Single-file static HTML/CSS/JavaScript, SVG plus existing mobile Canvas overlay, Python `unittest` contract tests, bundled Codex Python build runtime.

**Spec:** `docs/superpowers/specs/2026-09-01-marvel-flowchart-selection-sticky-tier.md`

## Global Constraints

- Do not modify canonical CSVs, database exports, or review ledgers for this UI-only change.
- Do not map `importance` values to the public three-tier labels.
- Preserve the existing `official` no-route behavior and multi-goal union semantics.
- Preserve mobile navigation, Canvas rendering, chronology/release independent views, and PC right-click goal behavior.
- Work only on `codex/ui-selection-sticky-tier`; do not commit directly to `main`.
- Use RED → GREEN TDD for every behavioral change and run full library-v5 tests plus the bundled build before completion.

---

### Task 1: Add failing UI contract tests

**Files:**
- Modify: `tests/library_v5/test_flowchart_selection_contract.py`
- Modify: `tests/library_v5/test_watch_scroll_navigation.py`
- Modify: `tests/library_v5/test_flowchart_layout_contract.py`

**Interfaces:**
- Tests will assert the HTML contracts introduced by Tasks 2–4.
- No production interface is changed in this task.

- [x] **Step 1: Write failing assertions** for: the dedicated sticky guide/tabs layer, chart selector values `official/site-proposal/complete`, chart tier setter using the shared tier setter, no `importance-hidden` mutation in the new chart path, gesture state (`startTarget`, `didDrag` or equivalent), and background-clear guard.
- [x] **Step 2: Run the focused tests** with the bundled Python runtime and confirm they fail because the current HTML still has guide/tabs in `main`, two old importance buttons, and no background gesture clear.

Run:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_flowchart_selection_contract tests.library_v5.test_watch_scroll_navigation tests.library_v5.test_flowchart_layout_contract -v
```

Expected: FAIL in the new assertions, with existing tests otherwise loading normally.

---

### Task 2: Make selection and gesture clearing deterministic

**Files:**
- Modify: `index.html:5145-5257,7264-7285,8813-8820`
- Test: `tests/library_v5/test_flowchart_selection_contract.py`

**Interfaces:**
- `ensureViewState(wrap)` gains gesture fields used by pointer handlers.
- The document click delegate calls a background-clear helper only after a non-drag chart gesture.
- Existing `select`, `removeGoal`, and `clearAllGoalsWithUndo` remain the only state mutation paths.

- [x] **Step 1: Add a regression contract** requiring pointer start target/coordinates, an explicit moved/did-drag guard, and a background-only clear branch that excludes nodes, edges, controls, tooltips, and chronology popovers.
- [x] **Step 2: Run the focused test and observe RED.**
- [x] **Step 3: Record pointer gesture state** at `pointerdown`, set `moved` when the existing mouse/touch thresholds are crossed, and carry a `backgroundClickCandidate` only for chart SVG/background targets.
- [x] **Step 4: In the delegated click path**, consume `st.moved` for drag suppression, select nodes as before, and call `clearAllGoalsWithUndo()` for a genuine background click. Do not clear on edge/control/tooltip targets.
- [x] **Step 5: Run the focused test and confirm GREEN**, then manually exercise same-node re-click and drag release in the browser.

---

### Task 3: Add a viewport-sticky guide and tabs layer

**Files:**
- Modify: `index.html:18-25,796-839,853-861`
- Test: `tests/library_v5/test_watch_scroll_navigation.py`, `tests/library_v5/test_flowchart_layout_contract.py`

**Interfaces:**
- The existing `.public-guide` and `.tabs` elements remain single DOM instances with their existing `data-target` values.
- Existing `.mobile-primary-nav` remains the mobile-only navigation surface.

- [x] **Step 1: Add failing DOM/CSS assertions** requiring the dedicated `.public-nav-sticky` layer, single guide/tab instances, and mobile hide rules.
- [x] **Step 2: Run the layout tests and confirm RED.**
- [x] **Step 3: Move the guide, tabs, and flow note into `.public-nav-sticky`** after `header`; remove the old copies from `main` without duplicating IDs/classes.
- [x] **Step 4: Keep the desktop header controls in normal flow** and retain the existing mobile `.tabs,.public-guide{display:none!important}` rule plus mobile wrapper hiding.
- [x] **Step 5: Run focused tests and a desktop browser smoke check**; confirm page vertical scroll leaves the guide/tabs at the viewport top and mobile navigation contracts remain intact.

---

### Task 4: Unify chart connection tiers without hiding database edges

**Files:**
- Modify: `index.html:165-167,821-827,5833-5860,5939-6028,6050-6105,6156-6187,6390-6424,6897-7067`
- Test: `tests/library_v5/test_flowchart_selection_contract.py`, `tests/library_v5/test_watch_scroll_navigation.py`

**Interfaces:**
- Chart control uses `data-chart-tier` values `official`, `site-proposal`, `complete`.
- `window.marvelSetConnectionTier(tier)` is the single public tier setter for chart and watch plan.
- New pure helper `buildTierHighlightState(goalIds, tier, baseState)` returns tier node/edge sets while leaving `EDGES` untouched.
- `computeSelectionState()` includes the tier-derived sets; SVG and Canvas renderers consume the same state.

- [x] **Step 1: Add failing assertions** for the three chart options, `marvelSetConnectionTier` wiring, `buildTierHighlightState`, no public chart `importance-btn` controls, and absence of an `importance-hidden` mutation in the chart tier path.
- [x] **Step 2: Run focused tests and confirm RED.**
- [x] **Step 3: Replace the old chart importance buttons** with one select labeled `つながり`; retain `importanceMode` internally only for edge metadata/path cost compatibility and keep all static edge groups visible.
- [x] **Step 4: Implement `buildTierHighlightState(goalIds,tier,baseState)`**:
  - official: collect registered official route IDs/edges for each goal; no fallback when unavailable;
  - site-proposal: call `buildMultiGoalPlan(goalIds,'site-proposal')`, derive route edge keys from each goal’s plan paths/core ancestry, and union them;
  - complete: preserve the existing recursive backward edge set and direct-reference context;
  - leave forward edge sets controlled by existing `scopeMode` and directed traversal.
- [x] **Step 5: Apply the tier mask in `computeSelectionState` and renderers** by filtering only backward/context highlight sets, retaining selected goals and all unselected SVG/Canvas edges as neutral visible content. Use the same state for `renderSelectionState`, mobile overlay, reason explanation, and selection summaries.
- [x] **Step 6: Synchronize chart select, watch select, active labels, and official-route state** through `window.marvelSetConnectionTier`; remove old chart `recommended/complete` UI text and avoid changing `prepTier` from flowchart policy initialization unexpectedly.
- [x] **Step 7: Run focused tests and browser smoke checks** for tier synchronization and the sparse 369-edge fixture. Confirm changing tiers does not remove edge groups or alter canonical data.

---

### Task 5: Full verification and review handoff

**Files:**
- Inspect only: `index.html`, changed tests, spec, plan, `git diff`

**Interfaces:**
- No further production behavior is introduced.

- [x] **Step 1: Run the full library-v5 test suite** with the bundled runtime (347 tests).
- [x] **Step 2: Run the bundled deterministic build** from the worktree root.
- [x] **Step 3: Inspect `git diff --check`, canonical CSV/data diffs, generated outputs, and worktree status; remove only known transient build outputs if needed.**
- [x] **Step 4: Run a final browser smoke matrix** (desktop sticky scroll, same-node toggle, blank clear, drag guard; mobile contracts remain covered by tests).
- [ ] **Step 5: Commit the bounded branch with an auditable message** only after verification, then report branch/commit and leave merge/push for explicit user direction.
