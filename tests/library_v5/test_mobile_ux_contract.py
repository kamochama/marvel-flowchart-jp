from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


def function_body(source: str, name: str) -> str:
    match = re.search(
        rf"(?:function\s+{re.escape(name)}\s*\(|(?:window\.)?{re.escape(name)}\s*=\s*function\s*\()",
        source,
    )
    if not match:
        raise AssertionError(f"function {name} was not found")
    parameter_start = source.find("(", match.start())
    depth = 0
    parameter_end = None
    for index in range(parameter_start, len(source)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                parameter_end = index
                break
    if parameter_end is None:
        raise AssertionError(f"function {name} has unbalanced parameters")
    opening = source.find("{", parameter_end)
    if opening < 0:
        raise AssertionError(f"function {name} body was not found")
    quote = None
    escaped = False
    depth = 0
    for index in range(opening, len(source)):
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
                return source[opening : index + 1]
    raise AssertionError(f"function {name} has unbalanced braces")


class MobileUxContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_mobile_navigation_exposes_controls_and_relationships(self) -> None:
        self.assertRegex(self.source, r'id="mobileControlsButton"[^>]*aria-controls="flowchartControls"')
        self.assertRegex(self.source, r'<div id="flowchartControls" class="controls"')
        self.assertRegex(self.source, r'id="mobileAreaButton"[^>]*aria-controls="mobileAreaSheet"')

    def test_mobile_area_menu_traps_and_restores_focus(self) -> None:
        open_body = function_body(self.source, "openMobileAreaMenu")
        close_body = function_body(self.source, "closeMobileAreaMenu")
        self.assertIn("mobileAreaReturnFocus", open_body)
        self.assertRegex(open_body, r"focus\(\)")
        self.assertIn("mobileAreaReturnFocus", close_body)
        self.assertRegex(close_body, r"focus\(\)")
        self.assertIn("mobileAreaOpen", self.source)
        self.assertIn("e.key!=='Tab'", self.source)

    def test_mobile_details_panel_manages_dialog_focus(self) -> None:
        body = function_body(self.source, "setDetails")
        self.assertIn("aria-hidden", body)
        self.assertIn("aria-expanded", body)
        self.assertIn("detailsReturnFocus", body)
        self.assertIn("detailsOpen", self.source)
        self.assertIn("e.key!=='Tab'", self.source)

    def test_side_tabs_expose_active_panel_state(self) -> None:
        body = function_body(self.source, "showSideTab")
        self.assertIn("aria-selected", body)
        self.assertIn("aria-hidden", body)
        self.assertIn("side-tab-", body)

    def test_mobile_work_list_uses_keyboard_buttons(self) -> None:
        render_body = self.source[self.source.find("render = function(){") :]
        self.assertRegex(render_body, r'<button type="button" class="node-item')
        self.assertIn("aria-pressed", render_body)

    def test_mobile_hit_test_prefers_nearest_exact_node(self) -> None:
        body = function_body(self.source, "mobileCanvasHitTest")
        self.assertIn("bestDistance", body)
        self.assertIn("best", body)
        self.assertIn("pad", body)

    def test_mobile_canvas_cache_has_a_bounded_pixel_budget(self) -> None:
        body = function_body(self.source, "renderMobileCanvasCache")
        self.assertIn("MOBILE_CANVAS_MAX_CACHE_PIXELS", body)
        self.assertIn("total+pixels", body)
        chooser = function_body(self.source, "chooseMobileCanvasCache")
        self.assertIn("available", chooser)

    def test_inactive_mobile_panels_defer_canvas_rebuilds(self) -> None:
        body = function_body(self.source, "initMobileCanvas")
        self.assertIn("needsRebuild", body)
        self.assertRegex(body, r"panel[\s\S]{0,500}classList\.contains\('active'\)")

    def test_mobile_clear_and_undo_keep_ui_and_overlay_in_sync(self) -> None:
        clear_body = function_body(self.source, "clearAllGoalsWithUndo")
        undo_body = function_body(self.source, "undoClearGoals")
        self.assertIn("resetPanels()", clear_body)
        self.assertIn("render()", clear_body)
        self.assertIn("drawMobileSelectionOverlay", undo_body)
        self.assertIn("window.__marvelLastSelectionState", undo_body)
        self.assertRegex(self.source, r"function\s+invalidateMobileUndo\s*\(")


if __name__ == "__main__":
    unittest.main()
