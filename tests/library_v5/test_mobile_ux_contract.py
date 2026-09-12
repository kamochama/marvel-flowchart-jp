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
        self.assertRegex(self.source, r'id="mobileAreaButton"[^>]*aria-controls="sheetHostPanel"')

    def test_phase5_data_shell_css_has_one_active_presentation_root(self) -> None:
        match = re.search(
            r'<style id="phase5-shell-contract">(?P<body>[\s\S]*?)</style>',
            self.source,
        )
        self.assertIsNotNone(match)
        body = match.group("body") if match else ""
        self.assertIn('html[data-shell="mobile"] .mobile-app-shell', body)
        self.assertIn('html[data-shell="compact"] .mobile-app-shell{display:none!important}', body)
        self.assertIn('html[data-shell="desktop"] .mobile-app-shell{display:none!important}', body)
        self.assertIn('html[data-shell="mobile"] #sheetHost', body)
        self.assertNotIn('visualViewport.height', body)

    def test_mobile_primary_controls_have_44px_touch_targets(self) -> None:
        match = re.search(
            r'<style id="mobile-touch-target-contract">(?P<body>[\s\S]*?)</style>',
            self.source,
        )
        self.assertIsNotNone(match)
        body = match.group("body") if match else ""
        for selector in (
            ".mobile-primary-nav input",
            ".mobile-primary-nav #q",
            ".mobile-primary-nav button",
            ".featured-route-control button",
            "#mobileFocusShell button",
            ".mobile-sheet-head button",
            ".side-tab-btn",
            "#flowchartControls input",
            "#flowchartControls select",
            "#flowchartControls button",
            ".watch-workspace button",
            ".watch-workspace select",
        ):
            self.assertIn(selector, body)
        self.assertRegex(body, r"min-height\s*:\s*44px")

    def test_mobile_header_stays_at_viewport_top_during_page_scroll(self) -> None:
        """The mobile search/area bar lives in the header, so its parent is sticky."""
        self.assertRegex(
            self.source,
            r"@media\(max-width:760px\)\{[\s\S]{0,400}header\{[^}]*position\s*:\s*sticky[^}]*top\s*:\s*0[^}]*z-index\s*:\s*30",
        )

    def test_mobile_area_menu_traps_and_restores_focus(self) -> None:
        open_body = function_body(self.source, "openMobileAreaMenu")
        close_body = function_body(self.source, "closeMobileAreaMenu")
        self.assertIn("openMobileSheet", open_body)
        self.assertIn("settings", open_body)
        self.assertIn("display", open_body)
        self.assertIn("closeMobileSheet", close_body)
        self.assertIn("sheetHost", self.source)
        self.assertIn("event.key!=='Tab'", function_body(self.source, "ensureMobileShell"))

    def test_mobile_sheet_manages_dialog_focus(self) -> None:
        body = function_body(self.source, "openMobileSheet")
        close_body = function_body(self.source, "closeMobileSheet")
        self.assertIn("aria-hidden", body)
        self.assertIn("aria-modal", body)
        self.assertIn("mobileSheetReturnFocus", body)
        self.assertIn("focus", body)
        self.assertIn("mobileSheetReturnFocus", close_body)
        self.assertIn("focus", close_body)
        self.assertIn("setAttribute('aria-modal','true')", self.source)
        self.assertIn("e.key==='Escape'", self.source)

    def test_shared_sheet_host_has_modal_and_docked_presentation_contract(self) -> None:
        self.assertIn("window.marvelSheetHost", self.source)
        self.assertIn("data-presentation", self.source)
        self.assertIn("syncSheetPresentation", self.source)
        self.assertRegex(self.source, r"data-presentation=\"docked\"")
        self.assertIn("setAttribute('role','region')", self.source)

    def test_desktop_inspection_uses_shared_sheet_host_without_goal_mutation(self) -> None:
        body = function_body(self.source, "marvelFocusWork")
        self.assertIn("marvelSheetHost", body)
        self.assertIn("openInspection", body)
        return_body = function_body(self.source, "marvelReturnToGoalView")
        self.assertIn("closeInspection", return_body)

    def test_sheet_modal_lifecycle_owns_inert_scroll_and_pointer_state(self) -> None:
        enter_body = function_body(self.source, "enterSheetModal")
        leave_body = function_body(self.source, "leaveSheetModal")
        self.assertIn("inert", enter_body)
        self.assertIn("scrollY", enter_body)
        self.assertIn("mobileSheetModalGeneration", enter_body)
        self.assertIn("restore", leave_body)
        self.assertIn("scrollTo", leave_body)
        self.assertIn("mobileSheetModalGeneration", leave_body)
        self.assertIn("sheetHostBackdrop", self.source)
        self.assertIn("pointerId", self.source)

    def test_docked_presentation_does_not_use_modal_aria_or_backdrop(self) -> None:
        body = function_body(self.source, "syncSheetPresentation")
        self.assertIn("setAttribute('role','region')", body)
        self.assertIn("removeAttribute('aria-modal')", body)
        self.assertIn("sheetHostBackdrop", self.source)
        self.assertIn("data-presentation=\"docked\"", self.source)

    def test_responsive_switch_closes_docked_inspection_before_mobile_modal(self) -> None:
        body = function_body(self.source, "syncSheetPresentation")
        self.assertIn("marvelSheetHost?.closeInspection", body)
        self.assertIn("dataset.owner==='inspection'", body)

    def test_mobile_sheet_chart_switch_preserves_selection_paint(self) -> None:
        self.assertIn(
            "window.activatePanel?.(button.dataset.sheetDisplayTarget,{fit:false,restoreSelection:true})",
            self.source,
        )

    def test_panel_activation_captures_selection_before_async_paint(self) -> None:
        body = function_body(self.source, "activatePanel")
        self.assertIn("const hadSelection=selectedIds.size>0", body)
        self.assertIn("restoreSelection&&hadSelection", body)

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
        self.assertRegex(self.source, r"getElementById\(['\"]clear['\"]\)\.onclick[\s\S]{0,260}invalidateMobileUndo")


if __name__ == "__main__":
    unittest.main()

