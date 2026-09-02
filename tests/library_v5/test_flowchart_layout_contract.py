from pathlib import Path
import re
import unittest


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


class FlowchartLayoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

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

    def test_chronology_viewbox_contains_fox_world_frame_bottom(self) -> None:
        """The FOX outer frame must fit inside the SVG drawing height."""
        body = function_body(self.source, "buildChronologyView")
        self.assertRegex(body, r"svgW=3560,svgH=18(?:2[4-9]|[3-9][0-9])")


if __name__ == "__main__":
    unittest.main()
