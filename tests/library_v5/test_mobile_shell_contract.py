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


class MobileShellContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_mobile_store_has_single_state_source(self) -> None:
        body = function_body(self.source, "createMobileUiStore")
        self.assertIn("getState", body)
        self.assertIn("subscribe", body)
        self.assertIn("setGoals", body)
        self.assertIn("setSheet", body)

    def test_mobile_store_normalizes_invalid_view_and_sheet(self) -> None:
        self.assertIn("view==='chart'", self.source)
        self.assertIn("sheet==='closed'", self.source)
        self.assertIn("window.marvelMobileUiStore", self.source)

    def test_mobile_shell_has_one_host_nav_and_sheet_before_desktop_main(self) -> None:
        main_start = self.source.find("<main>")
        self.assertGreater(main_start, 0)
        shell_start = self.source.find('id="mobileAppShell"')
        self.assertGreaterEqual(shell_start, 0)
        self.assertLess(shell_start, main_start)
        for element_id in ("mobileViewHost", "mobileBottomNav", "mobileSheet"):
            element_start = self.source.find(f'id="{element_id}"')
            self.assertGreaterEqual(element_start, shell_start)
            self.assertLess(element_start, main_start)
        self.assertEqual(self.source.count('id="mobileSheet"'), 1)

    def test_mobile_navigation_handlers_update_store_and_history(self) -> None:
        mount_body = function_body(self.source, "mountMobileView")
        self.assertIn("mobileViewHost", mount_body)
        self.assertIn("viewStates", mount_body)

        set_view_body = function_body(self.source, "setMobileView")
        self.assertIn("marvelMobileUiStore", set_view_body)
        self.assertIn("mountMobileView", set_view_body)
        self.assertIn("writeMobileUrlState", set_view_body)
        self.assertIn("aria-current", self.source)

        open_body = function_body(self.source, "openMobileSheet")
        self.assertIn("setSheet", open_body)
        self.assertIn("sheetWork", open_body)
        self.assertIn("writeMobileUrlState", open_body)

        close_body = function_body(self.source, "closeMobileSheet")
        self.assertIn("setSheet", close_body)
        self.assertIn("focus", close_body)
        self.assertIn("mobileSheet", close_body)

        self.assertIn('addEventListener(\'popstate\'', self.source)
        self.assertIn("history.pushState", self.source)
        self.assertIn('aria-modal="true"', self.source)

    def test_mobile_url_state_uses_documented_keys_and_preserves_hash(self) -> None:
        read_body = function_body(self.source, "readMobileUrlState")
        write_body = function_body(self.source, "writeMobileUrlState")
        for key in ("mview", "goals", "sheet", "sheetWork", "q", "mfilter"):
            self.assertIn(key, read_body)
            self.assertIn(key, write_body)
        self.assertIn("URLSearchParams", read_body)
        self.assertIn("URLSearchParams", write_body)
        self.assertIn("location.hash", write_body)

    def test_mobile_url_reapplies_sheet_work_when_kind_is_unchanged(self) -> None:
        body = function_body(self.source, "applyMobileUrlState")
        self.assertRegex(body, r"const current=store\.getState\(\)")
        self.assertRegex(
            body,
            r"current\.sheet!==parsed\.sheet[\s\S]{0,120}current\.sheetWork!==parsed\.sheetWork",
        )

    def test_mobile_search_url_and_controls_share_store_adapter(self) -> None:
        project_body = function_body(self.source, "syncMobileSearchControls")
        self.assertIn("q.value", project_body)
        self.assertIn("branch.value", project_body)
        self.assertIn("character.value", project_body)
        self.assertIn("status.value", project_body)

        input_body = function_body(self.source, "syncMobileSearchStateFromControls")
        self.assertIn("setSearch", input_body)
        self.assertIn("setFilter", input_body)
        self.assertIn("q", input_body)
        self.assertIn("mfilter", input_body)

        apply_body = function_body(self.source, "applyMobileUrlState")
        self.assertIn("syncMobileSearchControls", apply_body)

    def test_mobile_url_hydrates_semantic_selection_from_store(self) -> None:
        hydrate_body = function_body(self.source, "hydrateMobileSelectionFromStore")
        self.assertIn("selectedIds", hydrate_body)
        self.assertIn("selected", hydrate_body)
        self.assertIn("refreshSelection", hydrate_body)

        apply_body = function_body(self.source, "applyMobileUrlState")
        self.assertRegex(
            apply_body,
            r"store\.setGoals\(parsed\.goalIds,parsed\.selectedId\)[\s\S]{0,180}hydrateMobileSelectionFromStore",
        )

    def test_mobile_url_hydration_restores_goal_order(self) -> None:
        body = function_body(self.source, "hydrateMobileSelectionFromStore")
        self.assertRegex(body, r"const currentIds=\[\.\.\.selectedIds\]")
        self.assertRegex(
            body,
            r"currentIds\.every\(\(id,index\)=>id===orderedIds\[index\]\)",
        )

    def test_mobile_popstate_sheet_close_does_not_rewrite_target_history(self) -> None:
        close_body = function_body(self.source, "closeMobileSheet")
        self.assertRegex(
            self.source,
            r"function closeMobileSheet\(\{restoreFocus=true,syncHistory=true\}=\{\}\)",
        )
        self.assertRegex(close_body, r"if\(wasOpen&&syncHistory\)writeMobileUrlState")

        popstate_body = function_body(self.source, "handleMobilePopState")
        self.assertIn("closeMobileSheet({syncHistory:false})", popstate_body)
        self.assertRegex(
            popstate_body,
            r"closeMobileSheet\(\{syncHistory:false\}\)[\s\S]*applyMobileUrlState\(\)",
        )

    def test_focus_goal_syncs_store_after_desktop_semantic_update(self) -> None:
        self.assertRegex(
            self.source,
            r"focusGoal\s*=\s*function\(id\)\{[\s\S]{0,180}if\(!mobileWidth\(\)\)\{const result=focusGoalBeforeV51511\(id\);syncMobileUiGoals\(\);return result;\}",
        )

    def test_mobile_chart_mount_reuses_existing_renderer_and_shared_apis(self) -> None:
        body = function_body(self.source, "mountMobileChartView")
        self.assertIn("mobileCanvasStates", body)
        self.assertIn("viewStates", body)
        for api in ("select", "clearAllGoalsWithUndo", "fitView", "centerNodeInView"):
            self.assertIn(api, body)
        self.assertIn("mobileViewHost", body)
        self.assertNotIn("NODES.map", body)
        self.assertNotIn("EDGES.map", body)
        self.assertNotIn("mobileSelectionApis", body)

    def test_mobile_chart_mount_tracks_current_active_panel_and_each_origin(self) -> None:
        mount_body = function_body(self.source, "mountMobileChartView")
        self.assertIn("activeMobileChartPanel", mount_body)
        self.assertIn("mobileChartMountedPanel", mount_body)
        self.assertIn("panel.id", mount_body)
        self.assertIn("restoreMobileChartPanel", mount_body)
        self.assertNotIn("mobileChartPanelElement()", mount_body)
        self.assertIn("mobileChartPanelOrigins", self.source)
        self.assertIn("restoreMobileChartPanels", self.source)

    def test_mobile_activate_panel_remounts_active_chart_panel(self) -> None:
        body = function_body(self.source, "activatePanel")
        self.assertIn("mountMobileChartView", body)
        self.assertIn("mobileChartMotion.matches", body)
        self.assertIn("marvelMobileUiStore", body)
        self.assertIn("panel.querySelector('.svg-wrap')", body)

    def test_mobile_chart_mount_supports_characters_panel(self) -> None:
        body = function_body(self.source, "activeMobileChartPanel")
        self.assertIn("querySelector('.svg-wrap')", body)
        self.assertIn("mobileChartMountedPanel", body)
        self.assertIn("mobileChartLastPanel", body)
        self.assertIn("characters", self.source)

    def test_mobile_viewport_sync_reapplies_non_chart_visibility(self) -> None:
        match = re.search(
            r"const syncMobileChartForViewport=\(\)=>\{(?P<body>[\s\S]*?)\n  \};",
            self.source,
        )
        self.assertIsNotNone(match, "viewport sync function must exist")
        body = match.group("body")
        self.assertRegex(body, r"mobileUiStore\(\)\?\.getState\(\)\.view")
        self.assertIn("mobile-chart-host-only", body)
        self.assertIn("document.body.classList.add('mobile-chart-host-only')", body)
        self.assertIn("restoreMobileChartPanels", body)
        self.assertIn("host?.replaceChildren", body)

    def test_mobile_view_mount_only_attaches_chart_surface_for_chart_view(self) -> None:
        body = function_body(self.source, "mountMobileView")
        self.assertRegex(body, r"normalized===['\"]chart['\"]")
        self.assertIn("mountMobileChartView", body)
        self.assertIn("replaceChildren", body)
        self.assertRegex(body, r"normalized!==['\"]chart['\"]")
        self.assertIn("restoreMobileChartPanels", body)
        self.assertNotIn("detachMobileChartPanel()", body)
        self.assertIn("mobile-chart-host-only", body)

    def test_mobile_chart_controls_keep_touch_target_contract(self) -> None:
        self.assertRegex(self.source, r"mobile-chart-controls[\s\S]{0,500}min-height:44px")
        self.assertIn("mobileChartFit", self.source)
        self.assertIn("mobileChartSelected", self.source)
        self.assertIn("mobileChartDetails", self.source)
        self.assertIn("mobileChartViewButton", self.source)

    def test_mobile_sheet_open_close_have_no_chart_rebuild_path(self) -> None:
        for name in ("openMobileSheet", "closeMobileSheet"):
            body = function_body(self.source, name)
            for forbidden in ("render(", "fitView(", "rebuildMobileCanvas(", "initMobileCanvas(", "mountMobileChartView("):
                self.assertNotIn(forbidden, body, f"{name} must not rebuild chart state")

    def test_mobile_search_renderer_has_semantic_surface_and_shared_filter_contract(self) -> None:
        mount_body = function_body(self.source, "mountMobileSearchView")
        render_body = function_body(self.source, "renderMobileSearchResults")
        self.assertIn("data-mobile-surface','search", mount_body)
        self.assertIn('data-mobile-search-query', mount_body)
        self.assertIn('aria-live="polite"', mount_body)
        self.assertIn("renderMobileSearchResults(query,filter)", mount_body)
        self.assertIn("NODES.filter(pass)", render_body)
        self.assertIn("decodeMobileFilter", render_body)
        self.assertIn("mfilter", render_body)
        self.assertIn("data-mobile-search-count", mount_body)

    def test_mobile_search_results_separate_selection_navigation_and_detail_actions(self) -> None:
        mount_body = function_body(self.source, "mountMobileSearchView")
        render_body = function_body(self.source, "renderMobileSearchResults")
        for token in (
            "data-mobile-search-select",
            "data-mobile-search-chart",
            "data-mobile-search-detail",
            "setGoals",
            "setMobileView('chart')",
            "openMobileSheet('detail'",
        ):
            self.assertIn(token, self.source)
        self.assertIn("setMobileView('chart')", render_body)
        self.assertIn("openMobileSheet('detail'", render_body)
        for token in ("title_en", "release", "title"):
            self.assertIn(token, render_body)

    def test_mobile_search_typing_only_updates_dom_and_shared_query_filter_state(self) -> None:
        mount_body = function_body(self.source, "mountMobileSearchView")
        render_body = function_body(self.source, "renderMobileSearchResults")
        self.assertIn("setSearch", mount_body)
        self.assertIn("setFilter", mount_body)
        self.assertIn("renderMobileSearchResults", mount_body)
        for forbidden in ("fitView(", "initMobileCanvas(", "rebuildMobileCanvas(", "mountMobileChartView("):
            self.assertNotIn(forbidden, mount_body)
            self.assertNotIn(forbidden, render_body)

    def test_mobile_search_controls_keep_accessible_touch_target_and_empty_state_contract(self) -> None:
        self.assertRegex(self.source, r"mobile-search-result-action[\s\S]{0,500}min-height:44px")
        self.assertRegex(self.source, r"mobile-search-surface[\s\S]{0,700}input")
        self.assertIn("該当なし", self.source)
        self.assertIn("aria-live", self.source)

    def test_mobile_search_view_is_mounted_instead_of_placeholder_and_keeps_legacy_panels_hidden(self) -> None:
        body = function_body(self.source, "mountMobileView")
        self.assertIn("mountMobileSearchView", body)
        self.assertIn("normalized==='search'", body)
        self.assertIn("mobile-chart-host-only", body)

    def test_mobile_chart_browser_runner_has_json_scenario_contract(self) -> None:
        runner = ROOT / "tests" / "library_v5" / "browser_mobile_shell_audit.mjs"
        self.assertTrue(runner.is_file(), "M3 browser runner must exist")
        source = runner.read_text(encoding="utf-8")
        for token in ("--root", "--chrome", "390", "844", "Input.dispatchMouseEvent", "data-mobile-camera", "selection", "sheet", "rerenders", "failures", "panelHasWork", "nonChartDocumentPanel", "nonChartHidesLegacyPanel", "displayChooser", "charactersPanel", "responsiveSearchSync", "setDeviceMetricsOverride", "search", "history", "Spider-Man 3", "data-mobile-search-query", "data-mobile-search-select"):
            self.assertIn(token, source)
        self.assertIn("mobileAreaSheet", source)
        self.assertIn('data-mobile-target="release"', source)
        self.assertIn("panelId", source)
        self.assertIn("const state = await snapshot(cdp)", source)
        self.assertIn("return predicate(state) ? state : null", source)


if __name__ == "__main__":
    unittest.main()
