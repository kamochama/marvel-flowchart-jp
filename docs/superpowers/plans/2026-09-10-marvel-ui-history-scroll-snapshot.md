# Marvel Mobile History Scroll Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the mobile document scroll position in the current history entry so browser Back/Forward restores the preparation/search/chart surface at the same list position without creating extra history entries.

**Architecture:** Extend the existing `viewerNavigation.snapshot.mobile` object with finite `scrollX`/`scrollY` values. Scroll events are coalesced to one `replaceState` per event-loop turn through the existing policy-driven writer; popstate restoration runs inside the existing history-application guard and never writes history. Initial URL hydration does not restore an old snapshot, preserving the existing reload behavior.

**Tech Stack:** Static `index.html`, browser History API, Python `unittest` source/runtime contracts, and the existing Chrome/CDP mobile-shell audit.

**Spec:** `docs/superpowers/specs/2026-09-09-marvel-pc-mobile-ui-architecture-design.md` sections 6.1, 8.2, 10, and 13 Phase 2.

## Global Constraints

- Preserve the public URL keys `mview`, `goals`, `sheet`, `sheetWork`, `q`, and `mfilter`, the existing hash, and unknown query parameters.
- Keep `popstate` hydration write-free, including the scroll restoration callback and nested panel/tier callbacks.
- Scroll snapshots use `replaceState`; scrolling must never create a new history entry.
- Do not change canonical CSVs, persistent review history, graph topology, public tier names, chart drawing, or camera semantics in this slice.
- Keep initial page-load behavior unchanged: only `fromPopstate:true` applies a stored mobile snapshot.
- Use the bundled Python runtime and preserve `.codex-remote-attachments/`; remove only known generated outputs.

---

### Task 1: Add RED contracts for scroll snapshot capture and restoration

**Files:**
- Modify: `tests/library_v5/test_mobile_shell_contract.py`
- Modify: `tests/library_v5/test_ui_architecture_contract.py`
- Modify: `tests/library_v5/browser_mobile_shell_audit.mjs`

**Interfaces:**
- `readMobileHistorySnapshot()` returns finite `scrollX` and `scrollY` fields.
- `applyMobileHistorySnapshot(snapshot)` delegates restoration to a named scroll helper after the active surface is mounted.
- A scroll listener uses a coalescing scheduler and `writeMobileUrlState({action:'scroll-snapshot',replace:true})`.
- `marvelUiHistoryPolicy({type:'scroll-snapshot'})` remains `replace`.

- [x] **Step 1: Write failing source/runtime contracts**

Add assertions that require `scrollX`, `scrollY`, `restoreMobileHistoryScroll`, `scheduleMobileHistoryScrollSnapshot`, and the `scroll-snapshot` action. Add a Node contract that confirms the policy returns `replace` for the new action.

- [x] **Step 2: Extend the real-browser audit scenario**

After the existing panel snapshot round trip, scroll the search surface to a non-zero position, assert the current entry stores a positive `scrollY`, navigate to chart, then go back and assert the search surface returns with a matching scroll position and the history write log remains unchanged during popstate. Restore scroll to zero before the remaining scenarios.

- [x] **Step 3: Run the focused tests and confirm RED**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_ui_architecture_contract -v
```

Expected: the new source contracts fail because the production snapshot has no scroll fields/helper/scheduler yet.

### Task 2: Implement coalesced capture and guarded restoration

**Files:**
- Modify: `index.html`

**Interfaces:**
- `readMobileHistorySnapshot()` reads finite non-negative `scrollX` and `scrollY` from the document viewport.
- `restoreMobileHistoryScroll(snapshot)` schedules a bounded `requestAnimationFrame` restoration with `window.scrollTo`, normalizing invalid values to zero.
- `scheduleMobileHistoryScrollSnapshot()` coalesces scroll events and calls the existing writer with `scroll-snapshot`; it is a no-op while `mobileHistoryApplying()` is true or while the page is not mobile.

- [x] **Step 1: Add the minimal snapshot fields and helper**

Read `window.scrollX`/`window.scrollY` (falling back to `document.scrollingElement`) and clamp finite values to non-negative integers. Restore after mount in one or two animation frames so a newly mounted search/plan surface has layout before scrolling.

- [x] **Step 2: Add the coalesced scroll listener**

Register one passive `window` scroll listener during mobile-shell initialization. Use a single RAF token; each flush calls `writeMobileUrlState({replace:true,action:'scroll-snapshot'})`. The existing transaction guard must suppress this write during popstate restoration.

- [x] **Step 3: Run the focused tests and real mobile audit**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_ui_architecture_contract -v
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
Remove-Item Env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT -ErrorAction SilentlyContinue
```

Require `failures=[]`, a positive stored scroll snapshot, restored scroll parity, and zero writes during popstate.

### Task 3: Full verification and integration handoff

**Files:**
- No canonical data changes permitted.

- [x] **Step 1: Inspect the diff and run the full bundled-Python suite/build**

```powershell
git diff --check
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Require `audit_ok=true`, zero audit/content-audit issues, zero SQLite foreign-key rows, and `integrity_check=ok`.

- [x] **Step 2: Clean only known generated outputs**

Remove `data/content_audit/CONTENT_AUDIT.md`, `data/content_audit/queue.csv`, `data/derived/LIBRARY_AUDIT.md`, `data/derived/audit.json`, `data/derived/db/`, `data/derived/library_manifest.json`, and generated `__pycache__` directories. Preserve canonical CSVs, persistent reviews, and `.codex-remote-attachments/`.

- [ ] **Step 3: Commit, push, and open a normal PR**

```powershell
git add docs/superpowers/plans/2026-09-10-marvel-ui-history-scroll-snapshot.md index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/test_ui_architecture_contract.py tests/library_v5/browser_mobile_shell_audit.mjs
git commit -m "feat: restore mobile scroll history snapshots"
git push -u origin codex/mobile-history-scroll-snapshot
gh pr create --base main --head codex/mobile-history-scroll-snapshot --title "feat: restore mobile scroll history snapshots" --body "Preserve mobile scroll position in guarded history snapshots. No canonical data or graph semantics changed."
```

Wait for all required CI jobs before merge; verify main and Pages after integration.
