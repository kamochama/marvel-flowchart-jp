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
        self.assertIn("marvelCreateUiHistoryWriter", self.source)
        self.assertIn('aria-modal="true"', self.source)

    def test_mobile_history_writer_is_policy_driven(self) -> None:
        write_body = function_body(self.source, "writeMobileUrlState")
        self.assertIn("action", write_body)
        self.assertIn("marvelCreateUiHistoryWriter", write_body)
        self.assertNotRegex(write_body, r"if\(replace\)window\.history\.replaceState")

    def test_mobile_history_hydration_has_transaction_guard(self) -> None:
        apply_body = function_body(self.source, "applyMobileUrlState")
        self.assertIn("mobileHistoryApplyDepth", self.source)
        self.assertIn("try", apply_body)
        self.assertIn("finally", apply_body)

    def test_mobile_writer_checks_history_hydration_guard(self) -> None:
        write_body = function_body(self.source, "writeMobileUrlState")
        self.assertIn("mobileHistoryApplying", write_body)

    def test_mobile_popstate_applies_without_any_history_write(self) -> None:
        apply_body = function_body(self.source, "applyMobileUrlState")
        popstate_body = function_body(self.source, "handleMobilePopState")
        self.assertRegex(self.source, r"function applyMobileUrlState\(\{fromPopstate=false\}=\{\}\)")
        self.assertRegex(apply_body, r"syncHistory:!fromPopstate")
        self.assertRegex(apply_body, r"!fromPopstate[\s\S]{0,80}writeMobileUrlState")
        self.assertIn("applyMobileUrlState({fromPopstate:true})", popstate_body)

    def test_mobile_sheet_history_distinguishes_app_open_from_direct_url_hydration(self) -> None:
        self.assertIn("mobileSheetHistoryOwner", self.source)
        self.assertIn("mobileSheetHistoryEntryId", self.source)
        open_body = function_body(self.source, "openMobileSheet")
        close_body = function_body(self.source, "closeMobileSheet")
        self.assertIn("suppressMobileSheetHistory", open_body)
        self.assertIn("viewerNavigation", open_body)
        write_body = function_body(self.source, "writeMobileUrlState")
        self.assertIn("entryId", write_body)
        self.assertIn("parentEntryId", write_body)
        self.assertIn("parentEntryId", close_body)
        self.assertIn("history.back()", close_body)

    def test_mobile_sheet_owner_transitions_preserve_url_parent_and_mark_app_child(self) -> None:
        open_body = function_body(self.source, "openMobileSheet")
        write_body = function_body(self.source, "writeMobileUrlState")
        self.assertRegex(
            open_body,
            r"if\(action==='overlay-open'\)mobileSheetHistoryOwner='app'",
        )
        self.assertRegex(
            write_body,
            r"historyAction==='overlay-open'&&mobileSheetHistoryOwner==='app'",
        )
        self.assertIn("previousNavigation.sheetOwner", write_body)

    def test_mobile_url_state_uses_documented_keys_and_preserves_hash(self) -> None:
        read_body = function_body(self.source, "readMobileUrlState")
        write_body = function_body(self.source, "writeMobileUrlState")
        for key in ("mview", "goals", "sheet", "sheetWork", "q", "mfilter"):
            self.assertIn(key, read_body)
            self.assertIn(key, write_body)
        self.assertIn("URLSearchParams", read_body)
        self.assertIn("URLSearchParams", write_body)
        self.assertIn("location.hash", write_body)

    def test_mobile_history_snapshot_captures_panel_and_preparation_tier(self) -> None:
        snapshot_body = function_body(self.source, "readMobileHistorySnapshot")
        write_body = function_body(self.source, "writeMobileUrlState")
        self.assertIn("panelId", snapshot_body)
        self.assertIn("prepTier", snapshot_body)
        self.assertIn("viewerNavigation", write_body)
        self.assertIn("snapshot", write_body)

    def test_mobile_history_snapshot_restores_without_writing_during_popstate(self) -> None:
        apply_body = function_body(self.source, "applyMobileHistorySnapshot")
        hydrate_body = function_body(self.source, "applyMobileUrlState")
        self.assertIn("activatePanel", apply_body)
        self.assertIn("marvelSetConnectionTier", apply_body)
        self.assertRegex(hydrate_body, r"applyMobileHistorySnapshot\([\s\S]{0,180}viewerNavigation")
        self.assertIn("mobileHistoryApplying", self.source)

    def test_panel_and_tier_changes_replace_the_current_mobile_snapshot(self) -> None:
        panel_body = function_body(self.source, "activatePanel")
        tier_body = function_body(self.source, "marvelSetConnectionTier")
        self.assertIn("panel-change", panel_body)
        self.assertIn("writeMobileUrlState", panel_body)
        self.assertIn("tier-change", tier_body)
        self.assertIn("writeMobileUrlState", tier_body)

    def test_mobile_history_snapshot_tracks_scroll_without_new_entries(self) -> None:
        snapshot_body = function_body(self.source, "readMobileHistorySnapshot")
        scroll_body = function_body(self.source, "mobileHistoryScrollPosition")
        apply_body = function_body(self.source, "applyMobileHistorySnapshot")
        self.assertIn("mobileHistoryScrollPosition", snapshot_body)
        self.assertIn("scrollX", scroll_body)
        self.assertIn("scrollY", scroll_body)
        self.assertIn("restoreMobileHistoryScroll", apply_body)
        self.assertIn("scheduleMobileHistoryScrollSnapshot", self.source)
        self.assertIn("scroll-snapshot", self.source)

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
        self.assertRegex(close_body, r"else if\(wasOpen&&syncHistory\)\{[\s\S]*writeMobileUrlState")
        self.assertRegex(close_body, r"mobileSheetHistoryEntryId&&navigation\.entryId===mobileSheetHistoryEntryId")
        self.assertIn("navigation.parentEntryId", close_body)

        popstate_body = function_body(self.source, "handleMobilePopState")
        self.assertIn("closeMobileSheet({syncHistory:false})", popstate_body)
        self.assertRegex(
            popstate_body,
            r"closeMobileSheet\(\{syncHistory:false\}\)[\s\S]*applyMobileUrlState\(\{fromPopstate:true\}\)",
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

    def test_mobile_search_selection_uses_exported_goal_order_adapter(self) -> None:
        render_body = function_body(self.source, "renderMobileSearchResults")
        self.assertIn("marvelOrderedGoalIds", render_body)
        self.assertNotIn("setGoals(orderedGoalIds()", render_body)

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

    def test_mobile_search_surface_results_are_separate_from_legacy_overlay(self) -> None:
        mount_body = function_body(self.source, "mountMobileSearchView")
        render_body = function_body(self.source, "renderMobileSearchResults")
        self.assertIn("mobile-search-surface-results", mount_body)
        self.assertIn("mobile-search-surface-results", self.source)
        self.assertNotIn("className='mobile-search-results'", render_body)
        self.assertNotRegex(mount_body, r'class="mobile-search-results"')

    def test_mobile_legacy_search_input_syncs_active_surface(self) -> None:
        body = function_body(self.source, "syncMobileSearchStateFromControls")
        self.assertIn("marvelMobileUiStore", body)
        self.assertIn("getState", body)
        self.assertIn("view==='search'", body)
        self.assertIn("data-mobile-search-query", body)
        self.assertIn("scheduleMobileSearchRender", body)
        self.assertNotIn("renderMobileSearchResults(", body)
        self.assertIn("window.marvelMobileUiStore?.getState?.().view==='search'", self.source)

    def test_mobile_search_input_debounces_dom_only_rendering(self) -> None:
        mount_body = function_body(self.source, "mountMobileSearchView")
        self.assertIn("scheduleMobileSearchRender", mount_body)
        self.assertIn("requestAnimationFrame", self.source)
        self.assertRegex(self.source, r"mobileSearchRenderRaf")
        for forbidden in ("fitView(", "initMobileCanvas(", "rebuildMobileCanvas(", "mountMobileChartView("):
            self.assertNotIn(forbidden, mount_body)

    def test_mobile_plan_renderer_reuses_shared_plan_and_watch_engines(self) -> None:
        mount_body = function_body(self.source, "mountMobilePlanView")
        render_body = function_body(self.source, "renderMobilePlanScreen")
        shared_body = function_body(self.source, "renderPrepPlan")
        for token in ("buildMultiGoalPlan", "orderedGoalIds", "prepTier", "renderPrepPlan"):
            self.assertIn(token, mount_body + render_body)
        for token in ("marvelWatchProgress", "prep-watched-check", "setWatched", "watchedIds"):
            self.assertIn(token, render_body + shared_body)
        self.assertIn("mobileViewHost", mount_body)

    def test_mobile_plan_exposes_only_public_site_and_complete_tiers(self) -> None:
        mount_body = function_body(self.source, "mountMobilePlanView")
        render_body = function_body(self.source, "renderMobilePlanScreen")
        plan_source = mount_body + render_body + function_body(self.source, "renderPrepPlan")
        self.assertIn("site-proposal", plan_source)
        self.assertIn("complete", plan_source)
        self.assertIn("サイト提案ルート", plan_source)
        self.assertIn("完全版", plan_source)
        self.assertNotIn("公式予習ルート", plan_source)
        self.assertNotIn("official", plan_source)

    def test_mobile_plan_has_summary_progress_checklist_sheet_and_chart_return(self) -> None:
        mount_body = function_body(self.source, "mountMobilePlanView")
        render_body = function_body(self.source, "renderMobilePlanScreen")
        plan_source = mount_body + render_body + function_body(self.source, "renderPrepPlan")
        for token in (
            "data-mobile-plan-summary",
            "data-mobile-plan-progress",
            "data-mobile-plan-item",
            "data-mobile-plan-detail",
            "チャートで見る",
            "openMobileSheet('detail'",
            "remainingKnownMinutes",
            "progressbar",
        ):
            self.assertIn(token, plan_source)

    def test_mobile_plan_can_remove_each_goal_without_rebuilding_the_chart(self) -> None:
        render_body = function_body(self.source, "renderMobilePlanScreen")
        plan_source = render_body + function_body(self.source, "renderPrepPlan") + function_body(self.source, "removeMobilePlanGoal")
        for token in (
            "data-mobile-plan-remove-goal",
            "removeMobilePlanGoal",
            "syncMobileUiGoals",
            "writeMobileUrlState",
            "renderMobilePlanScreen",
            "scheduleMobilePlanRender",
        ):
            self.assertIn(token, plan_source)
        self.assertNotIn("removeGoal(button.dataset.mobilePlanRemoveGoal)", render_body)

    def test_mobile_plan_switch_hides_legacy_surfaces_and_coalesces_renders(self) -> None:
        mount_body = function_body(self.source, "mountMobilePlanView")
        self.assertIn("scheduleMobilePlanRender", mount_body)
        self.assertIn("mobilePlanRenderRaf", self.source)
        self.assertRegex(
            self.source,
            r"body\.mobile-chart-host-only\s+#mobileFocusShell[^}]*display:none!important",
        )
        self.assertRegex(
            self.source,
            r"body\.mobile-chart-host-only\s+#watchWorkspace[^}]*display:none!important",
        )

    def test_mobile_plan_jump_uses_the_new_mobile_view(self) -> None:
        goal_bar_body = function_body(self.source, "wireStableMobileGoalBar")
        self.assertIn("setMobileView", goal_bar_body)
        self.assertIn("mobileWidth()", goal_bar_body)
        self.assertIn("showWatchWorkspace?.()", goal_bar_body)

    def test_mobile_detail_sheet_renders_work_metadata(self) -> None:
        body = function_body(self.source, "openMobileSheet")
        body += function_body(self.source, "mobileWorkDetailHtml")
        for token in ("WORK_DETAILS", "nm?.[", "synopsis_ja", "map_role_ja", "innerHTML"):
            self.assertIn(token, body)

    def test_mobile_plan_watch_toggle_updates_plan_only_without_chart_rebuild(self) -> None:
        render_body = function_body(self.source, "renderMobilePlanScreen")
        mount_body = function_body(self.source, "mountMobilePlanView")
        self.assertIn("setWatched", render_body)
        self.assertIn("renderMobilePlanScreen", render_body + mount_body)
        for forbidden in ("fitView(", "initMobileCanvas(", "rebuildMobileCanvas(", "mountMobileChartView("):
            self.assertNotIn(forbidden, render_body)

    def test_mobile_plan_view_is_mounted_instead_of_placeholder_and_hides_legacy_panels(self) -> None:
        body = function_body(self.source, "mountMobileView")
        self.assertIn("mountMobilePlanView", body)
        self.assertIn("normalized==='plan'", body)
        self.assertIn("mobile-chart-host-only", body)

    def test_mobile_shell_is_the_only_active_mobile_presentation_root(self) -> None:
        self.assertEqual(self.source.count('id="mobileAppShell"'), 1)
        self.assertNotIn("mobileBackdrop", self.source)
        self.assertNotIn("mobile-graph-actions", self.source)
        self.assertNotIn("mobileDetailsFloat", self.source)
        self.assertNotIn("mobile-details-open", self.source)

    def test_mobile_right_panel_has_no_legacy_bottom_sheet_transform_path(self) -> None:
        self.assertNotRegex(self.source, r"body\.mobile-details-open\s+#right")
        self.assertNotRegex(self.source, r"#right\{[^}]*transform:translateY")
        self.assertNotIn("setDetails(open)", self.source)

    def test_mobile_shell_mounts_one_heavy_renderer_per_active_view(self) -> None:
        for name in ("mountMobileChartView", "mountMobileSearchView", "mountMobilePlanView"):
            body = function_body(self.source, name)
            self.assertNotIn("mobile-graph-actions", body)
            self.assertNotIn("mobileDetailsFloat", body)
        chart_body = function_body(self.source, "mountMobileChartView")
        self.assertEqual(chart_body.count("mobileHost.replaceChildren"), 1)
        for name in ("mountMobileSearchView", "mountMobilePlanView"):
            self.assertIn("mobileHost.replaceChildren", function_body(self.source, name))

    def test_mobile_chart_browser_runner_has_json_scenario_contract(self) -> None:
        runner = ROOT / "tests" / "library_v5" / "browser_mobile_shell_audit.mjs"
        self.assertTrue(runner.is_file(), "M3 browser runner must exist")
        source = runner.read_text(encoding="utf-8")
        for token in ("--root", "--chrome", "390", "844", "Input.dispatchMouseEvent", "data-mobile-camera", "selection", "sheet", "rerenders", "failures", "panelHasWork", "nonChartDocumentPanel", "nonChartHidesLegacyPanel", "displayChooser", "charactersPanel", "responsiveSearchSync", "setDeviceMetricsOverride", "search", "history", "plan", "mobilePlanSnapshot", "data-mobile-plan-summary", "data-mobile-plan-watched", "data-mobile-plan-detail", "data-mobile-plan-remove-goal", "sheetBodyText", "layout", "mobilePrepJump", "Spider-Man 3", "data-mobile-search-query", "data-mobile-search-select", "firstCardInViewport", "legacyQuerySync", "scrollY", "historySnapshot"):
            self.assertIn(token, source)
        self.assertIn("mobileAreaSheet", source)
        self.assertIn('data-mobile-target="release"', source)
        self.assertIn("panelId", source)
        self.assertIn("const state = await snapshot(cdp)", source)
        self.assertIn("if(predicate(state))return state", source)
        self.assertIn("error.state=state", source)


if __name__ == "__main__":
    unittest.main()
