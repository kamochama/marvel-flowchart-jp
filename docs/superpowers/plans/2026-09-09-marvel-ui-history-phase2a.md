# Marvel UI History Phase 2A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make mobile URL/history transitions use one guarded writer so `popstate` hydration never writes a new history entry and equivalent actions do not grow history.

**Architecture:** Keep the existing mobile store, URL schema, sheet ownership metadata, and `marvelUiHistoryPolicy` as the semantic sources. Add a small transaction guard around history hydration and route every mobile history write through the existing writer; do not redesign the chart, canonical data, or camera snapshots in this phase.

**Tech Stack:** Static `index.html`, browser History API, Python `unittest` source/runtime contracts, and the existing Chrome/CDP mobile-shell audit.

**Spec:** `docs/superpowers/specs/2026-09-09-marvel-pc-mobile-ui-architecture-design.md` sections 6.1, 9, and 12.

## Global Constraints

- Preserve the public URL keys `mview`, `goals`, `sheet`, `sheetWork`, `q`, and `mfilter`, the existing hash, and unknown query parameters.
- `popstate` application must perform zero `pushState` and zero `replaceState` calls, including nested sheet/store/render callbacks.
- Surface changes, goal mutations, and new in-app overlays remain `pushState`; search input, inspection focus, same-detail target changes, and direct-link close remain `replaceState`.
- Repeated equivalent actions are no-ops for history; state hydration and DOM synchronization still run when required.
- Direct-link sheet close must not call `history.back()`; only an app-created overlay entry with a matching parent may traverse back.
- Do not change canonical CSVs, persistent reviews, graph topology, public tier names, chart drawing, or camera restoration in this phase.
- Use RED → GREEN → full bundled-Python verification; preserve `.codex-remote-attachments/` and remove only known generated build outputs.

---

### Task 1: Add executable history-transaction RED contracts

**Files:**
- Modify: `tests/library_v5/test_mobile_shell_contract.py`
- Modify: `tests/library_v5/test_ui_architecture_contract.py`

**Interfaces:**
- Tests inspect the real `writeMobileUrlState`, `applyMobileUrlState`, `handleMobilePopState`, and `closeMobileSheet` implementations rather than only testing the policy return values.

- [ ] **Step 1: Write failing tests**

Add source contracts that require a named hydration guard and its `try/finally` release, and add a Node runtime contract for the writer to reject writes while the guard is active:

```python
def test_mobile_history_hydration_has_transaction_guard(self):
    apply_body = function_body(self.source, "applyMobileUrlState")
    self.assertIn("mobileHistoryApplyDepth", self.source)
    self.assertIn("try", apply_body)
    self.assertIn("finally", apply_body)

def test_mobile_writer_skips_when_history_hydration_is_active(self):
    result = self._run_node("""
window.marvelMobileHistoryApplyDepth = 1;
const calls = [];
const history = {pushState(){calls.push('push')}, replaceState(){calls.push('replace')}};
const write = window.marvelCreateUiHistoryWriter(history);
const written = write({state:{}, url:'?mview=search', action:{type:'surface-transition'}});
return {written, calls};
""")
    self.assertEqual(result, {"written": False, "calls": []})
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_ui_architecture_contract -v
```

Expected: the new guard tests fail because the current writer has no shared hydration-depth check.

### Task 2: Implement the guarded writer and hydration boundary

**Files:**
- Modify: `index.html:8581-8719,9821-9840`

**Interfaces:**
- Produces `window.marvelMobileHistoryApplyDepth` as a numeric transaction depth.
- `writeMobileUrlState` returns `false` without touching History API while the depth is positive.
- `applyMobileUrlState({fromPopstate:true})` increments the depth for its entire popstate state-application transaction and decrements it in `finally`; initial URL hydration may still perform its explicit normalization replacement.
- Existing `suppressMobileSheetHistory` remains a sheet-content guard, not a replacement for the global transaction guard.

- [ ] **Step 1: Add the smallest shared guard**

Declare the counter beside the existing mobile history variables:

```javascript
let mobileHistoryApplyDepth=0;
window.marvelMobileHistoryApplyDepth=0;
```

Use a helper so the writer and the hydration code share one value:

```javascript
function mobileHistoryApplying(){
  return mobileHistoryApplyDepth>0||window.marvelMobileHistoryApplyDepth>0;
}
```

- [ ] **Step 2: Guard every writer entry**

At the start of `writeMobileUrlState`, before URL construction or writer creation, return `false` when `mobileHistoryApplying()` is true. In `marvelCreateUiHistoryWriter`, apply the same guard before selecting `pushState` or `replaceState`; this protects callbacks that reach the writer directly.

- [ ] **Step 3: Wrap URL hydration**

Change `applyMobileUrlState` to increment both the local counter and exported counter, then execute the existing body in `try`, and decrement in `finally`. Keep `fromPopstate` behavior intact: no URL normalization write is allowed in either the direct popstate path or nested callbacks. Do not early-return before the `finally` block.

- [ ] **Step 4: Keep close semantics explicit**

`handleMobilePopState` continues calling `closeMobileSheet({syncHistory:false})` and then `applyMobileUrlState({fromPopstate:true})`. Direct-link close still uses `overlay-close` replacement; matching app-owned entries still use one `history.back()`.

### Task 3: Reuse the real-browser no-write regression coverage

**Files:**
- Modify: `tests/library_v5/test_mobile_shell_contract.py`
- Modify: `tests/library_v5/test_ui_architecture_contract.py`

**Interfaces:**
- The existing browser audit's `history.popstateNoWrites` and `history.forwardNoWrites` counters fail if hydration writes history.
- Existing view, sheet, selection, and rerender assertions remain unchanged.

- [ ] **Step 1: Confirm the existing RED browser instrumentation**

The current runner already wraps `history.pushState` and `history.replaceState`, resets the log around a back/forward restoration, and asserts `popstateNoWrites` / `forwardNoWrites`. Keep that instrumentation and use it as the regression oracle for the new transaction guard; no duplicate counter is needed.

- [ ] **Step 2: Run the focused static tests**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract tests.library_v5.test_ui_architecture_contract -v
```

- [ ] **Step 3: Run the real mobile-shell audit**

```powershell
$env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract -v
Remove-Item Env:MARVEL_BROWSER_MOBILE_SHELL_AUDIT -ErrorAction SilentlyContinue
```

Expected: the report has `failures=[]`, `history.popstateNoWrites=true`, and `history.forwardNoWrites=true`.

### Task 4: Full verification and integration handoff

**Files:**
- No canonical data changes permitted.

- [ ] **Step 1: Run the full bundled-Python suite and build**

```powershell
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Require `audit_ok=true`, zero audit/content-audit issues, zero SQLite foreign-key rows, and `integrity_check=ok`.

- [ ] **Step 2: Inspect and clean generated outputs**

Inspect the build summary, then remove only `data/content_audit/CONTENT_AUDIT.md`, `data/content_audit/queue.csv`, `data/derived/LIBRARY_AUDIT.md`, `data/derived/audit.json`, `data/derived/db/`, `data/derived/library_manifest.json`, and generated `__pycache__` directories. Preserve canonical CSVs, persistent reviews, and `.codex-remote-attachments/`.

- [ ] **Step 3: Review the full diff and commit**

```powershell
git diff --check
git status --short --branch
git add docs/superpowers/plans/2026-09-09-marvel-ui-history-phase2a.md index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/test_ui_architecture_contract.py
git commit -m "fix: guard mobile history hydration"
```

Open a PR from a `codex/` branch. Do not change canonical data or merge until required CI and Pages checks are green.
