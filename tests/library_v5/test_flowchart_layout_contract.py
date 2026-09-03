import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


def function_body(source: str, name: str) -> str:
    match = re.search(rf"function\s+{re.escape(name)}\s*\(", source)
    if not match:
        raise AssertionError(f"function {name} was not found")
    parameter_start = source.find("(", match.start())
    parameter_depth = 0
    parameter_end = None
    for index in range(parameter_start, len(source)):
        char = source[index]
        if char == "(":
            parameter_depth += 1
        elif char == ")":
            parameter_depth -= 1
            if parameter_depth == 0:
                parameter_end = index
                break
    if parameter_end is None:
        raise AssertionError(f"function {name} has unbalanced parameters")
    opening = source.find("{", parameter_end)
    if opening < 0:
        raise AssertionError(f"function {name} body was not found")
    start = opening
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"function {name} has unbalanced braces")


def function_source(source: str, name: str) -> str:
    """Return a complete function declaration for a Node helper fixture."""
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*", source)
    if not match:
        raise AssertionError(f"function {name} was not found")
    return source[match.start() : match.end()] + function_body(source, name)


class FlowchartLayoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def _run_node_json(self, function_names: list[str], expression: str, *, preamble: str = "") -> object:
        """Run production helpers against a deterministic literal fixture."""
        missing = [
            name
            for name in function_names
            if not re.search(rf"function\s+{re.escape(name)}\s*\(", self.source)
        ]
        if missing:
            self.fail(f"missing production helper(s): {', '.join(missing)}")
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for release helper fixture coverage")
        if node is None:
            return None
        declarations = "\n".join(function_source(self.source, name) for name in function_names)
        script = f"{preamble}\n{declarations}\nprocess.stdout.write(JSON.stringify({expression}));"
        result = subprocess.run(
            [node, "-"], input=script, capture_output=True, text=True, encoding="utf-8", check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_desktop_side_panel_tracks_expanded_sticky_header(self) -> None:
        body = function_body(self.source, "syncDesktopSidePanelLayer")
        self.assertIn("advancedOpen", body)
        self.assertIn("right.style.zIndex", body)
        self.assertRegex(self.source, r"advanced-controls[\s\S]{0,500}addEventListener\(['\"]toggle['\"]")

    def test_expanded_side_panel_keeps_existing_sticky_offset(self) -> None:
        body = function_body(self.source, "syncDesktopSidePanelLayer")
        self.assertNotIn("right.style.top=", body)
        self.assertIn("right.style.removeProperty('top')", body)

    def test_desktop_side_panel_remains_clickable_above_expanded_header(self) -> None:
        body = function_body(self.source, "syncDesktopSidePanelLayer")
        self.assertIn("zIndex", body)
        self.assertIn("advancedOpen", body)
        self.assertIn("'19'", body)
        self.assertNotIn("'21'", body)

    def test_closed_advanced_controls_restore_existing_side_panel_position(self) -> None:
        body = function_body(self.source, "syncDesktopSidePanelLayer")
        self.assertRegex(body, r"if\s*\(advancedOpen\)")
        self.assertRegex(body, r"advancedOpen[\s\S]{0,500}removeProperty\('top'\)")

    def test_mobile_restore_uses_exported_selection_state(self) -> None:
        bodies = [
            function_body(self.source, "rebuildMobileCanvas"),
            function_body(self.source, "restoreMobileSelectionOverlay"),
            function_body(self.source, "restoreMobileSelectionOverlayIfNeeded"),
        ]
        self.assertTrue(all("window.__marvelLastSelectionState" in body for body in bodies))
        self.assertTrue(all("selectionStateCache" not in body for body in bodies))

    def test_mobile_clear_refreshes_watch_plan_immediately(self) -> None:
        body = function_body(self.source, "clearAllGoalsWithUndo")
        self.assertIn("updatePreparationPlan();", body)
        self.assertIn("updatePathExplanation();", body)

    def test_clear_svg_removes_detail_focus_highlight(self) -> None:
        body = function_body(self.source, "clearSvg")
        self.assertRegex(body, r"querySelectorAll\([^)]*\.detail-focus")
        self.assertRegex(body, r"classList\.remove\([^)]*['\"]detail-focus['\"]")

    def test_focus_renderer_marks_detail_focus_explicitly(self) -> None:
        body = function_body(self.source, "renderFocusHighlight")
        self.assertIn("g.classList.add('focus','detail-focus')", body)

    def test_release_card_date_label_is_compact_before_kind_column(self) -> None:
        """Long precision notes must not intrude into the release-kind column."""
        body = function_body(self.source, "releaseCardDateLabel")
        self.assertIn("displayDate", body)
        self.assertRegex(body, r"month|undated|cancel|precision")
        release_body = function_body(self.source, "buildReleaseView")
        self.assertIn("releaseCardDateLabel(meta)", release_body)
        self.assertNotIn("font-size=\"8.2\">${esc(meta.displayDate)}", release_body)

    def test_release_date_precision_never_invents_a_day_at_runtime(self) -> None:
        """Day/month/year/none labels must preserve precision in production helpers."""
        fixtures = [
            {"sortDate": "2024-03-09", "displayDate": "2024.03.09", "precision": "day"},
            {"sortDate": "2024-03", "displayDate": "2024.03", "precision": "month"},
            {"sortDate": "2024", "displayDate": "2024", "precision": "year"},
        ]
        expression = f"""(() => {{
  const fixtures = {json.dumps(fixtures)};
  return {{
    labels: fixtures.map(meta => releaseCardDateLabel(meta)),
    anchors: fixtures.map(meta => releaseMetaDate(meta) === null ? null : 'set')
  }};
}})()"""
        result = self._run_node_json(["releaseMetaDate", "releaseCardDateLabel"], expression)
        self.assertEqual(result["labels"], ["2024.03.09", "2024.03", "2024"])
        self.assertEqual(result["anchors"], ["set", "set", "set"])

    def test_release_layout_helper_assigns_tbd_bucket_and_same_day_order(self) -> None:
        """TBD cards and same-day ties must use the executable layout comparator."""
        fixtures = [
            {"workId": "day-work", "stableSortIndex": 2, "meta": {"sortDate": "2024-03-09", "displayDate": "2024.03.09", "precision": "day"}},
            {"workId": "month-work", "stableSortIndex": 1, "meta": {"sortDate": "2024-03", "displayDate": "2024.03", "precision": "month"}},
            {"workId": "year-work", "stableSortIndex": 3, "meta": {"sortDate": "2024", "displayDate": "2024", "precision": "year"}},
            {"workId": "tbd-work", "stableSortIndex": 0, "meta": {"sortDate": "", "displayDate": "TBD", "precision": "none"}},
            {"workId": "same-z", "stableSortIndex": 8, "meta": {"sortDate": "2024-05-01", "displayDate": "2024.05.01", "precision": "day"}},
            {"workId": "same-b", "stableSortIndex": 7, "meta": {"sortDate": "2024-05-01", "displayDate": "2024.05.01", "precision": "day"}},
            {"workId": "same-a", "stableSortIndex": 7, "meta": {"sortDate": "2024-05-01", "displayDate": "2024.05.01", "precision": "day"}},
        ]
        expression = f"""(() => {{
  const fixtures = {json.dumps(fixtures)};
  const layout = fixtures.map(item => releaseLayoutMeta(item.meta, item.stableSortIndex, item.workId));
  return {{
    layout: layout.map(item => ({{sortKey:item.sortKey, precision:item.precision, isTbd:item.isTbd, stableSortIndex:item.stableSortIndex, workId:item.workId}})),
    sorted: layout.slice().sort(compareReleaseItems).map(item => item.workId)
  }};
}})()"""
        result = self._run_node_json(["releaseLayoutMeta", "compareReleaseItems"], expression)
        self.assertEqual(
            result["layout"],
            [
                {"sortKey": "2024-03-09", "precision": "day", "isTbd": False, "stableSortIndex": 2, "workId": "day-work"},
                {"sortKey": "2024-03", "precision": "month", "isTbd": False, "stableSortIndex": 1, "workId": "month-work"},
                {"sortKey": "2024", "precision": "year", "isTbd": False, "stableSortIndex": 3, "workId": "year-work"},
                {"sortKey": "9999-99-99", "precision": "none", "isTbd": True, "stableSortIndex": 0, "workId": "tbd-work"},
                {"sortKey": "2024-05-01", "precision": "day", "isTbd": False, "stableSortIndex": 8, "workId": "same-z"},
                {"sortKey": "2024-05-01", "precision": "day", "isTbd": False, "stableSortIndex": 7, "workId": "same-b"},
                {"sortKey": "2024-05-01", "precision": "day", "isTbd": False, "stableSortIndex": 7, "workId": "same-a"},
            ],
        )
        self.assertEqual(result["sorted"], ["year-work", "month-work", "day-work", "same-a", "same-b", "same-z", "tbd-work"])

    def test_layout_release_lane_calls_compare_release_items(self) -> None:
        """Lane placement must execute the production complete-order comparator."""
        preamble = """
let compareCalls = 0;
let legacyCalls = 0;
const compareReleaseItems = (a,b) => { compareCalls += 1; return 0; };
const compareReleaseIds = (a,b) => { legacyCalls += 1; return 0; };
const RELEASE_META = {
  'same-a': {sortDate:'2024-05-01', precision:'day', stableSortIndex:1},
  'same-b': {sortDate:'2024-05-01', precision:'day', stableSortIndex:2}
};
const nm = {'same-a':{title:'A'}, 'same-b':{title:'B'}};
const releaseXForMeta = () => 10;
const releaseLayoutMeta = (meta,index,workId) => ({sortKey:meta.sortDate, precision:meta.precision, isTbd:false, stableSortIndex:index ?? meta.stableSortIndex, workId:workId ?? ''});
"""
        expression = "(() => { const result = layoutReleaseLane(['same-a','same-b'], {start:'2024',end:'2024'}, 0, 100, 10); return {compareCalls, legacyCalls, itemCount:result.items.length}; })()"
        result = self._run_node_json(["layoutReleaseLane"], expression, preamble=preamble)
        self.assertGreater(result["compareCalls"], 0, "layoutReleaseLane must call compareReleaseItems")
        self.assertEqual(result["legacyCalls"], 0, "layoutReleaseLane must not use the legacy title comparator")

    def test_release_geometry_is_selection_independent(self) -> None:
        """Selection must not rebuild release cards, axes, or relation geometry."""
        release = function_body(self.source, "buildReleaseView")
        self.assertIn("releaseLayoutMeta", release)
        self.assertIn("compareReleaseItems", release)
        for forbidden in ("selectedIds", "backEdges", "forwardEdges", "contextEdges", "pathEdges"):
            self.assertNotIn(forbidden, release)

    def test_chronology_viewbox_contains_fox_world_frame_bottom(self) -> None:
        """The FOX outer frame must fit inside the SVG drawing height."""
        body = function_body(self.source, "buildChronologyView")
        self.assertRegex(body, r"svgW=3560,svgH=18(?:2[4-9]|[3-9][0-9])")


if __name__ == "__main__":
    unittest.main()
