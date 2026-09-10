# Marvel UI Phase 4 Search and Preparation Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make search and preparation-plan updates preserve the user's position and focus while proving that no update rebuilds the chart.

**Architecture:** Keep marvelMobileUiStore, the shared watch-progress engine, and the chart renderer as separate owners. Search changes update only search DOM and URL state; watch, tier, and goal changes update only the preparation projection, with a viewport/focus snapshot when markup is replaced.

**Tech Stack:** Static index.html, vanilla JavaScript, Python unittest, Chrome/CDP browser audit, bundled Codex Python runtime.

**Spec:** docs/superpowers/specs/2026-09-09-marvel-pc-mobile-ui-architecture-design.md §13 Phase 4; production boundary is recorded in NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md §0.1.17.

## Global Constraints

- Preserve public mobile tiers site-proposal and complete; do not expose the internal official route.
- Preserve inspection.workId, ordered goals, watched IDs, active panel, camera, and existing selection/highlight semantics.
- Search, watch, tier, and goal updates must not call render, fitView, rebuildMobileCanvas, initMobileCanvas, or mountMobileChartView.
- Query/filter and watch updates may replace the current URL entry, but must not grow browser history; popstate application performs zero history writes.
- Keep the single mobile presentation root and hide legacy chart surfaces on search/plan views.
- Do not modify canonical CSVs, review ledgers, graph/worldline/chronology semantics, desktop behavior, or public ZIP structure.
- Use the bundled Python runtime explicitly; do not invoke bare python.

## Files and responsibilities

- Modify tests/library_v5/test_mobile_shell_contract.py for static no-rebuild, ownership, and viewport/focus contracts.
- Modify tests/library_v5/browser_mobile_shell_audit.mjs for real 390x844 focus/scroll scenarios.
- Modify tests/library_v5/test_browser_mobile_shell_audit.py for runner-shape and result assertions.
- Modify index.html only after RED tests, in the existing search/plan render paths.
- Update this plan with execution evidence; update handoff/roadmap only in the final docs-only handoff commit.

## Observable interfaces

- scheduleMobileSearchRender(query, filter) coalesces DOM updates and never mounts/rebuilds the chart.
- renderMobileSearchResults(query, filter) updates result count/results only; it does not mutate goals or inspection.
- renderMobilePlanScreen() renders from the shared store/watch engine and restores a captured viewport/focus anchor when replacing markup.
- mobileUiStore.getState() remains the source for view, query, filter, goalIds, and selectedId.
- window.__mobileShellAuditCounters exposes existing render, fit, and rebuild counters.
- Browser audit JSON adds phase4.search and phase4.plan; unset fields are failures.

### Task 1: Add RED contracts for state ownership and no-rebuild behavior

**Files:** tests/library_v5/test_mobile_shell_contract.py

- [ ] **Step 1: Write failing static contracts.** Add:

```python
def test_phase4_search_update_keeps_chart_and_goal_owners_separate(self):
    body = function_body(self.source, 'mountMobileSearchView')
    render_body = function_body(self.source, 'renderMobileSearchResults')
    self.assertIn('setSearch', body)
    self.assertIn('setFilter', body)
    for forbidden in ('render(', 'fitView(', 'rebuildMobileCanvas(', 'initMobileCanvas(', 'mountMobileChartView('):
        self.assertNotIn(forbidden, body + render_body)
    self.assertNotIn('selectedIds.clear', body + render_body)
    self.assertNotIn('clearAllGoals', body + render_body)

def test_phase4_plan_update_restores_viewport_and_focus_anchor(self):
    body = function_body(self.source, 'renderMobilePlanScreen')
    for token in ('activeElement', 'scrollTop', 'preventScroll', 'data-mobile-plan-work'):
        self.assertIn(token, body)
    for forbidden in ('fitView(', 'rebuildMobileCanvas(', 'initMobileCanvas(', 'mountMobileChartView('):
        self.assertNotIn(forbidden, body)
```

- [ ] **Step 2: Run the RED tests.**

```powershell
$MarvelPython = 'C:/Users/ataka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw 'Bundled Python runtime not found' }
& $MarvelPython -m unittest tests.library_v5.test_mobile_shell_contract.MobileShellContractTests.test_phase4_search_update_keeps_chart_and_goal_owners_separate tests.library_v5.test_mobile_shell_contract.MobileShellContractTests.test_phase4_plan_update_restores_viewport_and_focus_anchor -v
```

Expected: the new plan viewport/focus assertions fail before implementation.

- [ ] **Step 3: Commit only the RED contracts.**

```powershell
git add tests/library_v5/test_mobile_shell_contract.py
git diff --cached --check
git commit -m 'test: define phase4 search and plan update contracts'
```

### Task 2: Preserve search focus, scroll, and history

**Files:** index.html; tests/library_v5/test_mobile_shell_contract.py; tests/library_v5/browser_mobile_shell_audit.mjs

- [ ] **Step 1: Add a RED browser scenario.** Initialize result.phase4.search with focusPreserved, scrollPreserved, chartRebuilds, and historyGrowth. Focus the mobile search input, type Spider, wait for the result count, and compare active element, scroll, rebuild counter, and history log length before and after.

```javascript
const before=await pageEvaluate(cdp,"return {rebuild:window.__mobileShellAuditCounters?.rebuild||0,history:(window.__mobileHistoryLog||[]).length,scroll:Math.round(window.scrollY),focus:document.activeElement?.id||''};");
await pageEvaluate(cdp,"const input=document.querySelector('#mobileViewHost [data-mobile-search-query]'); input.focus(); input.value='Spider'; input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:'Spider'})); return true;");
await waitForSearch(cdp,state=>state.view==='search'&&state.query==='Spider'&&state.resultCount>0,timeoutMs,'phase4 search update');
const after=await pageEvaluate(cdp,"return {rebuild:window.__mobileShellAuditCounters?.rebuild||0,history:(window.__mobileHistoryLog||[]).length,scroll:Math.round(window.scrollY),focus:document.activeElement?.id||''};");
result.phase4.search.chartRebuilds=after.rebuild-before.rebuild;
result.phase4.search.historyGrowth=after.history-before.history;
result.phase4.search.focusPreserved=after.focus==='mobileSearchQuery';
result.phase4.search.scrollPreserved=Math.abs(after.scroll-before.scroll)<=2;
```

- [ ] **Step 2: Run the mobile-shell audit and record RED.** Use MARVEL_BROWSER_MOBILE_SHELL_AUDIT=1 and the existing unittest entry point.
- [x] **Step 3: Confirm the existing lifecycle is sufficient.** The current search path already captures no chart rebuilds, preserves the input focus/scroll in the real audit, and uses replace-only search history; no redundant helper was added. Keep writeMobileUrlState({action:'search-input'}) replace-only and do not call a chart renderer.

```javascript
const captureSearchViewport=surface=>({scrollTop:surface?.scrollTop||0,focus:document.activeElement?.matches?.('[data-mobile-search-query]')});
const restoreSearchViewport=(surface,snapshot)=>{if(!surface||!snapshot)return;surface.scrollTop=snapshot.scrollTop;if(snapshot.focus)surface.querySelector('[data-mobile-search-query]')?.focus({preventScroll:true});};
```

- [x] **Step 4: Run MobileShellContractTests and the mobile-shell browser audit GREEN.** Confirm chart rebuild delta 0 and history growth 0.
- [ ] **Step 5: Commit:** git add index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs; git diff --cached --check; git commit -m 'fix: preserve search viewport and focus during updates'.

### Task 3: Preserve preparation-plan position and focus

**Files:** index.html in renderMobilePlanScreen/removeMobilePlanGoal/plan handlers; tests/library_v5/test_mobile_shell_contract.py; tests/library_v5/browser_mobile_shell_audit.mjs

- [x] **Step 1: Add RED scenarios.** Extend result.phase4.plan for watch, tier, and goal removal. Focus a plan item action, record its data-mobile-plan-work, bounding top, scroll, goal IDs, rebuild counter, and history length, perform the update, then compare the same values.

```javascript
const before=await pageEvaluate(cdp,"const item=document.querySelector('#mobileViewHost [data-mobile-plan-item]'); const box=item?.getBoundingClientRect(); return {id:item?.dataset.mobilePlanWork||'',top:box?.top||0,rebuild:window.__mobileShellAuditCounters?.rebuild||0,history:(window.__mobileHistoryLog||[]).length};");
await clickPoint(cdp,await pointForSelector(cdp,'#mobileViewHost [data-mobile-plan-watched]'));
await waitForPlan(cdp,state=>state.view==='plan'&&state.planSurface,timeoutMs,'phase4 plan watch update');
const after=await pageEvaluate(cdp,"const item=document.querySelector('#mobileViewHost [data-mobile-plan-item]'); const box=item?.getBoundingClientRect(); return {id:item?.dataset.mobilePlanWork||'',top:box?.top||0,rebuild:window.__mobileShellAuditCounters?.rebuild||0,history:(window.__mobileHistoryLog||[]).length};");
result.phase4.plan.chartRebuilds=after.rebuild-before.rebuild;
result.phase4.plan.anchorPreserved=after.id===before.id&&Math.abs(after.top-before.top)<=4;
result.phase4.plan.historyGrowth=after.history-before.history;
```

- [x] **Step 2: Run the browser audit and record RED.** The new anchor/focus fields were added and the existing audit established the baseline behavior before the helper was installed.
- [x] **Step 3: Implement the snapshot.** Before replacing plan markup, record surface.scrollTop, focused data-mobile-plan-work, and action kind. After listeners attach, restore scrollTop, find the same item/action, and focus with preventScroll:true. If a goal was removed, focus the nearest surviving item, then a tabindex=-1 plan heading fallback.

```javascript
function captureMobilePlanViewport(surface){
  const active=document.activeElement;
  const item=active?.closest?.('[data-mobile-plan-item]');
  return {scrollTop:surface?.scrollTop||0,workId:item?.dataset.mobilePlanWork||'',action:active?.matches?.('[data-mobile-plan-watched]')?'watched':active?.matches?.('[data-mobile-plan-detail]')?'detail':''};
}
function restoreMobilePlanViewport(surface,snapshot){
  if(!surface||!snapshot)return;
  surface.scrollTop=snapshot.scrollTop;
  const selector=snapshot.action==='watched'?'[data-mobile-plan-watched]':'[data-mobile-plan-detail]';
  const item=snapshot.workId&&[...surface.querySelectorAll('[data-mobile-plan-item]')].find(node=>node.dataset.mobilePlanWork===snapshot.workId);
  (item?.querySelector(selector)||surface.querySelector('#mobilePlanTitle'))?.focus?.({preventScroll:true});
}
```

- [x] **Step 4: Run focused unit and browser audits GREEN.** Verify rebuild delta 0, history growth 0, ordered goals correct, and watched progress changes only in the plan projection.
- [ ] **Step 5: Commit:** git add index.html tests/library_v5/test_mobile_shell_contract.py tests/library_v5/browser_mobile_shell_audit.mjs; git diff --cached --check; git commit -m 'fix: preserve preparation plan position and focus'.

### Task 4: Integrate and verify

**Files:** tests/library_v5/test_browser_mobile_shell_audit.py; this plan; handoff and roadmap for the final baseline.

- [x] **Step 1: Require phase4.search and phase4.plan in the Python harness; require every boolean true and every counter/history delta zero.**
- [x] **Step 2: Run the exact bundled-Python full suite, build, selection audit, interaction audit, and mobile-shell audit from AGENTS.md.**
- [x] **Step 3: Inspect the complete diff. Confirm only planned HTML/test/docs files changed; canonical CSVs and persistent review ledgers are byte-identical; git diff --check is clean.**
- [ ] **Step 4: Record RED/GREEN counts, hosted CI, Pages, and unchanged semantic boundaries; state that Phase 5 PC/breakpoint/orientation work is next and not included.**
- [ ] **Step 5: Push the feature branch, create a normal PR, wait for required checks, merge, verify main SHA and Pages/public HTML, then update this plan's execution record. Never commit directly to main or force-push.**

## Self-review checklist

- Phase 4 covers search input/filter, watch toggles, tier changes, and goal removal; Phase 5/6 are out of scope.
- Every implementation step has a concrete RED scenario, minimal implementation shape, GREEN verification, and commit boundary.
- The plan never changes canonical data or derives graph edges.
- Counter deltas, history writes, scroll anchors, focus targets, goal order, and public tier visibility are explicit acceptance evidence.

## Execution record (2026-09-10)

- Task 1 RED: the search ownership contract was already satisfied; the new plan viewport/focus contract failed because `renderMobilePlanScreen` had no snapshot lifecycle.
- Task 2: the existing search renderer was confirmed by real Chrome to preserve input focus, keep scroll stable for the exercised update, avoid chart rebuilds (`0`), and add no `pushState` entries (`0`). No redundant search implementation rewrite was made; the browser regression fields were added instead.
- Task 3 GREEN: `captureMobilePlanViewport`/`restoreMobilePlanViewport` now preserve plan surface/document scroll and focused plan actions with `preventScroll`, while initial surface mounts do not inherit stale chart focus/scroll. The real mobile-shell report recorded `anchorPreserved=true`, `chartRebuilds=0`, and `historyGrowth=0`.
- Task 4 verification: bundled-Python suite `577` pass (`5` environment-gated skips); build `audit_issue_count=0`, content-audit issue count `0`, story paths `83/83`, prewatch edges `199`, export `131` nodes / `355` edges / `562` reasons; real Chrome selection, interaction, and mobile-shell audits pass. Generated build outputs were inspected and removed as transient; canonical CSVs and review ledgers remained unchanged.
- Production handoff and roadmap update, PR creation, hosted CI, Pages verification, and merge remain the final integration steps after the implementation diff is reviewed.
