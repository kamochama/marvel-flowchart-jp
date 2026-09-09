from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


class UiArchitectureContractTests(unittest.TestCase):
    """Phase 0 contracts for the shared inspection/goal/sheet state facade."""

    def _run_node(self, expression: str) -> object:
        script = f"""
import fs from 'node:fs';
import vm from 'node:vm';
const html = fs.readFileSync({json.dumps(str(INDEX))}, 'utf8');
const match = html.match(/<script id=\"viewer-ui-state-facade\">([\\s\\S]*?)<\\/script>/);
if (!match) throw new Error('viewer-ui-state-facade script is missing');
const window = {{}};
vm.runInNewContext(match[1], {{ window }});
const result = await (async () => {{ {expression} }})();
process.stdout.write(JSON.stringify(result));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_inspection_toggle_does_not_mutate_goal_collection(self) -> None:
        result = self._run_node(
            """
const initial = window.marvelCreateUiState({goals:{orderedIds:['A','B'],currentId:'B'}});
const inspected = window.marvelApplyUiCommand(initial, {type:'inspect',workId:'C'});
const cleared = window.marvelApplyUiCommand(inspected, {type:'inspect',workId:'C'});
return {inspected,cleared};
"""
        )
        self.assertEqual(result["inspected"]["inspection"]["workId"], "C")
        self.assertEqual(result["inspected"]["goals"], {"orderedIds": ["A", "B"], "currentId": "B"})
        self.assertIsNone(result["cleared"]["inspection"]["workId"])
        self.assertEqual(result["cleared"]["goals"], result["inspected"]["goals"])

    def test_shell_classifier_uses_stable_layout_and_input_metrics(self) -> None:
        result = self._run_node(
            """
const samples = {
  portraitPhone: window.marvelClassifyShell({layoutWidth:390,screenWidth:390,screenHeight:844,coarse:true}),
  landscapeTouchPhone: window.marvelClassifyShell({layoutWidth:844,screenWidth:844,screenHeight:390,coarse:true}),
  exactMobileBoundary: window.marvelClassifyShell({layoutWidth:760,screenWidth:760,screenHeight:844,coarse:false}),
  compactLowerBoundary: window.marvelClassifyShell({layoutWidth:761,screenWidth:761,screenHeight:844,coarse:false}),
  compactUpperBoundary: window.marvelClassifyShell({layoutWidth:980,screenWidth:980,screenHeight:844,coarse:false}),
  desktopLowerBoundary: window.marvelClassifyShell({layoutWidth:981,screenWidth:981,screenHeight:844,coarse:false}),
};
return samples;
"""
        )
        self.assertEqual(
            result,
            {
                "portraitPhone": "mobile",
                "landscapeTouchPhone": "mobile",
                "exactMobileBoundary": "mobile",
                "compactLowerBoundary": "compact",
                "compactUpperBoundary": "compact",
                "desktopLowerBoundary": "desktop",
            },
        )

    def test_non_goal_commands_preserve_an_explicit_null_current_goal(self) -> None:
        result = self._run_node(
            """
const initial = window.marvelCreateUiState({goals:{orderedIds:['A','B'],currentId:null}});
const inspected = window.marvelApplyUiCommand(initial, {type:'inspect',workId:'C'});
const overlay = window.marvelApplyUiCommand(inspected, {type:'openOverlay',overlay:{kind:'settings'}});
return {initial,inspected,overlay};
"""
        )
        self.assertIsNone(result["initial"]["goals"]["currentId"])
        self.assertIsNone(result["inspected"]["goals"]["currentId"])
        self.assertIsNone(result["overlay"]["goals"]["currentId"])

    def test_goal_commands_are_the_only_commands_that_mutate_goals(self) -> None:
        result = self._run_node(
            """
const initial = window.marvelCreateUiState({inspection:{workId:'A'}});
const added = window.marvelApplyUiCommand(initial, {type:'addGoal',workId:'C'});
const removed = window.marvelApplyUiCommand(added, {type:'removeGoal',workId:'C'});
return {initial,added,removed};
"""
        )
        self.assertEqual(result["initial"]["goals"], {"orderedIds": [], "currentId": None})
        self.assertEqual(result["added"]["goals"], {"orderedIds": ["C"], "currentId": "C"})
        self.assertEqual(result["removed"]["goals"], {"orderedIds": [], "currentId": None})
        self.assertEqual(result["removed"]["inspection"], {"workId": "A"})

    def test_inspection_and_surface_history_policies_are_distinct(self) -> None:
        result = self._run_node(
            """
return {
  inspection: window.marvelUiHistoryPolicy({type:'inspection-focus'}),
  surface: window.marvelUiHistoryPolicy({type:'surface-transition'}),
  goalFocus: window.marvelUiHistoryPolicy({type:'goal-focus'}),
  popstate: window.marvelUiHistoryPolicy({type:'popstate-apply'}),
};
"""
        )
        self.assertEqual(result, {"inspection": "replace", "surface": "push", "goalFocus": "replace", "popstate": "none"})

    def test_goal_mutations_and_overlay_open_push_history(self) -> None:
        result = self._run_node(
            """
return {
  addGoal: window.marvelUiHistoryPolicy({type:'goal-add'}),
  removeGoal: window.marvelUiHistoryPolicy({type:'goal-remove'}),
  clearGoals: window.marvelUiHistoryPolicy({type:'goal-clear'}),
  overlay: window.marvelUiHistoryPolicy({type:'overlay-open'}),
};
"""
        )
        self.assertEqual(result, {"addGoal": "push", "removeGoal": "push", "clearGoals": "push", "overlay": "push"})

    def test_history_writer_uses_policy_and_skips_popstate_writes(self) -> None:
        result = self._run_node(
            """
const calls=[];
const history={
  pushState:(state,title,url)=>calls.push({method:'pushState',state,title,url}),
  replaceState:(state,title,url)=>calls.push({method:'replaceState',state,title,url}),
};
const write=window.marvelCreateUiHistoryWriter(history);
const pop=write({state:{entry:'pop'},url:'?mview=chart',action:{type:'popstate-apply'}});
const surface=write({state:{entry:'surface'},url:'?mview=search',action:{type:'surface-transition'}});
const inspection=write({state:{entry:'inspection'},url:'?mview=search&q=x',action:{type:'inspection-focus'}});
return {pop,surface,inspection,calls};
"""
        )
        self.assertFalse(result["pop"])
        self.assertTrue(result["surface"])
        self.assertTrue(result["inspection"])
        self.assertEqual(
            result["calls"],
            [
                {"method": "pushState", "state": {"entry": "surface"}, "title": "", "url": "?mview=search"},
                {"method": "replaceState", "state": {"entry": "inspection"}, "title": "", "url": "?mview=search&q=x"},
            ],
        )

    def test_history_writer_skips_when_hydration_transaction_is_active(self) -> None:
        result = self._run_node(
            """
window.marvelMobileHistoryApplyDepth = 1;
const calls=[];
const history={
  pushState:()=>calls.push('push'),
  replaceState:()=>calls.push('replace'),
};
const write=window.marvelCreateUiHistoryWriter(history);
const written=write({state:{},url:'?mview=search',action:{type:'surface-transition'}});
return {written,calls};
"""
        )
        self.assertEqual(result, {"written": False, "calls": []})

    def test_history_policy_marks_navigation_write_boundaries(self) -> None:
        result = self._run_node(
            """
return {
  overlayClose: window.marvelUiHistoryPolicy({type:'overlay-close'}),
  searchInput: window.marvelUiHistoryPolicy({type:'search-input'}),
  urlHydrate: window.marvelUiHistoryPolicy({type:'url-hydrate'}),
  scrollSnapshot: window.marvelUiHistoryPolicy({type:'scroll-snapshot'}),
};
"""
        )
        self.assertEqual(result, {"overlayClose": "replace", "searchInput": "replace", "urlHydrate": "replace", "scrollSnapshot": "replace"})
        facade = INDEX.read_text(encoding="utf-8")
        policy_start = facade.index("window.marvelUiHistoryPolicy=function")
        policy_end = facade.index("window.marvelCreateUiHistoryWriter=function", policy_start)
        self.assertIn("scroll-snapshot", facade[policy_start:policy_end])

    def test_sheet_close_uses_content_provenance(self) -> None:
        result = self._run_node(
            """
const base = window.marvelCreateUiState({inspection:{workId:'A'}});
const derived = window.marvelEffectiveSheetContent(base, 'docked');
const explicit = window.marvelApplyUiCommand(base, {type:'openOverlay',overlay:{kind:'settings'}});
const explicitClosed = window.marvelCloseUiOverlay(explicit, 'docked');
const derivedClosed = window.marvelCloseUiOverlay(base, 'docked');
const mobileExplicitClosed = window.marvelCloseUiOverlay(explicit, 'modal');
return {derived,explicit,explicitClosed,derivedClosed,mobileExplicitClosed};
"""
        )
        self.assertEqual(result["derived"], {"kind": "detail", "workId": "A"})
        self.assertEqual(result["explicit"]["overlay"], {"kind": "settings"})
        self.assertEqual(result["explicitClosed"]["overlay"], {"kind": "closed"})
        self.assertEqual(result["explicitClosed"]["inspection"], {"workId": "A"})
        self.assertEqual(result["derivedClosed"]["inspection"], {"workId": None})
        self.assertEqual(result["mobileExplicitClosed"]["overlay"], {"kind": "closed"})
        self.assertEqual(result["mobileExplicitClosed"]["inspection"], {"workId": "A"})

    def test_legacy_selection_bridge_keeps_inspection_and_goal_focus_independent(self) -> None:
        result = self._run_node(
            """
const legacy = {goalIds:['A','B','A'],currentId:'B',inspectionId:'C',surface:'chart',chartPanel:'overview'};
const bridge = window.marvelCreateLegacySelectionBridge(() => legacy);
const snapshot = bridge.getSnapshot();
const before = JSON.parse(JSON.stringify(snapshot));
snapshot.goals.orderedIds.push('D');
legacy.goalIds=['A','C']; legacy.currentId='C'; legacy.inspectionId='D';
return {legacy,before,mutated:snapshot,after:bridge.getSnapshot()};
"""
        )
        self.assertEqual(result["legacy"]["goalIds"], ["A", "C"])
        self.assertEqual(result["before"]["goals"], {"orderedIds": ["A", "B"], "currentId": "B"})
        self.assertEqual(result["before"]["inspection"], {"workId": "C"})
        self.assertEqual(result["mutated"]["goals"]["orderedIds"], ["A", "B", "D"])
        self.assertEqual(result["after"], {"inspection": {"workId": "D"}, "goals": {"orderedIds": ["A", "C"], "currentId": "C"}})

    def test_legacy_selection_bridge_does_not_apply_facade_goal_reducer(self) -> None:
        result = self._run_node(
            """
const legacy = {goalIds:['A','C'],currentId:'C',inspectionId:null};
const bridge = window.marvelCreateLegacySelectionBridge(() => legacy);
const snapshot = bridge.getSnapshot();
return {snapshot,reduced:window.marvelApplyUiCommand(snapshot,{type:'removeGoal',workId:'C'})};
"""
        )
        self.assertEqual(result["snapshot"]["goals"], {"orderedIds": ["A", "C"], "currentId": "C"})
        self.assertEqual(result["reduced"]["goals"], {"orderedIds": ["A"], "currentId": "A"})

    def test_legacy_selection_bridge_coalesces_publish_notifications(self) -> None:
        result = self._run_node(
            """
const legacy = {goalIds:['A'],currentId:'A',inspectionId:null};
const bridge = window.marvelCreateLegacySelectionBridge(() => legacy);
const seen=[]; const unsubscribe=bridge.subscribe(state=>seen.push(state));
bridge.requestPublish();
legacy.goalIds=['A','B']; legacy.currentId='B'; legacy.inspectionId='C';
bridge.requestPublish();
await Promise.resolve();
const after=bridge.getSnapshot();
unsubscribe(); legacy.goalIds=['A']; legacy.currentId='A'; bridge.requestPublish(); await Promise.resolve();
return {seen,after};
"""
        )
        self.assertEqual(len(result["seen"]), 1)
        self.assertEqual(result["seen"][0], {"inspection": {"workId": "C"}, "goals": {"orderedIds": ["A", "B"], "currentId": "B"}})
        self.assertEqual(result["after"], result["seen"][0])

    def test_legacy_selection_bridge_skips_noop_publish_after_initial_read(self) -> None:
        result = self._run_node(
            """
const legacy = {goalIds:['A'],currentId:'A',inspectionId:null};
const bridge = window.marvelCreateLegacySelectionBridge(() => legacy);
bridge.getSnapshot();
const seen=[]; bridge.subscribe(state=>seen.push(state));
bridge.requestPublish(); await Promise.resolve();
legacy.inspectionId='C'; bridge.requestPublish(); await Promise.resolve();
return {seen};
"""
        )
        self.assertEqual(result["seen"], [{"inspection": {"workId": "C"}, "goals": {"orderedIds": ["A"], "currentId": "A"}}])

    def test_legacy_selection_bridge_isolates_subscriber_payloads(self) -> None:
        result = self._run_node(
            """
const legacy = {goalIds:['A'],currentId:'A',inspectionId:null};
const bridge = window.marvelCreateLegacySelectionBridge(() => legacy);
const seen=[];
bridge.subscribe(state=>{state.goals.orderedIds.push('MUTATED');seen.push(state);});
bridge.subscribe(state=>seen.push(state));
legacy.goalIds=['A','B']; legacy.currentId='B'; bridge.requestPublish(); await Promise.resolve();
return {seen};
"""
        )
        self.assertEqual(result["seen"][0]["goals"]["orderedIds"], ["A", "B", "MUTATED"])
        self.assertEqual(result["seen"][1]["goals"]["orderedIds"], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
