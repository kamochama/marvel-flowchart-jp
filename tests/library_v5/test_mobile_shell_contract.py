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


if __name__ == "__main__":
    unittest.main()
