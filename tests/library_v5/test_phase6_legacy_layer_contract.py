from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


class Phase6LegacyLayerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def _phase5_shell_css(self) -> str:
        match = re.search(
            r'<style id="phase5-shell-contract">(?P<body>[\s\S]*?)</style>',
            self.source,
        )
        self.assertIsNotNone(match)
        return match.group("body") if match else ""

    def test_phase6_right_is_desktop_only_presentation_root(self) -> None:
        """The canonical mobile shell must own presentation in coarse landscape too."""
        css = self._phase5_shell_css()
        self.assertIn(
            'html[data-shell="mobile"] #right{display:none!important;pointer-events:none!important}',
            css,
        )
        self.assertIn('html[data-shell="compact"] .mobile-app-shell{display:none!important}', css)
        self.assertIn('html[data-shell="desktop"] .mobile-app-shell{display:none!important}', css)
        self.assertIn('id="sidePanelWorks"', self.source)
        self.assertIn('id="sidePanelLinks"', self.source)

    def test_phase6_detail_goal_summary_and_sheet_host_are_separate(self) -> None:
        """The goal summary remains while inspection content has one SheetHost owner."""
        open_body = self.source[self.source.find("function openDockedInspection") :]
        open_body = open_body[: open_body.find("function closeDockedInspection")]
        close_body = self.source[self.source.find("function closeDockedInspection") :]
        close_body = close_body[: close_body.find("function setMobileView")]
        self.assertNotIn("sheetHostMirror", open_body)
        self.assertIn("renderSheetContent({kind:'detail',workId})", open_body)
        self.assertNotIn("data-sheet-host-mirror", close_body)
        self.assertIn("#detail", self.source)
        self.assertIn("sheetHostBody", self.source)

    def test_phase6_detail_inspection_has_single_sheet_host_owner(self) -> None:
        """Desktop inspection must not call the legacy detail writer."""
        focus_start = self.source.find("function renderFocusHighlight")
        focus_end = self.source.find("function queueFocusPaint", focus_start)
        focus_body = self.source[focus_start:focus_end]
        self.assertGreaterEqual(focus_start, 0)
        self.assertNotIn("marvelRenderFocusedDetail", focus_body)
        self.assertNotRegex(focus_body, r"detail\\.(?:innerHTML|textContent)")

        open_start = self.source.find("function openDockedInspection")
        open_end = self.source.find("function closeDockedInspection", open_start)
        close_start = open_end
        close_end = self.source.find("function setMobileView", close_start)
        open_body = self.source[open_start:open_end]
        close_body = self.source[close_start:close_end]
        self.assertNotIn("sheetHostMirror", open_body)
        self.assertNotIn("data-sheet-host-mirror", close_body)
        self.assertIn("renderSheetContent({kind:'detail',workId})", open_body)
        self.assertIn("sheetHostBody", self.source)

    def test_phase6_retired_inspection_markup_is_absent(self) -> None:
        """Task 2's retired detail writer and its private markup are gone."""
        for token in (
            "marvelRenderFocusedDetail",
            "sortedDirect",
            "attrEsc",
            "v515-detail-title",
            "v515-detail-section",
            "v515-detail-actions",
            "v515-goal-cta",
            "v515-return-goals",
            "v515-prevnext",
            "v515-work-links",
            "v515-work-link",
            "v515-meta",
            "mobileWorkDetailHtml",
        ):
            self.assertNotIn(token, self.source)

        # The chart's focus paint is a separate, still-active responsibility.
        self.assertIn("g.node.detail-focus", self.source)
        self.assertIn("function sheetWorkDetailHtml", self.source)

    def test_phase6_search_projection_remains_active_adapter(self) -> None:
        """Mobile search still delegates filtering to the shared DOM-backed predicate."""
        start = self.source.find("function renderMobileSearchResults")
        self.assertGreaterEqual(start, 0)
        body = self.source[start : self.source.find("window.renderMobileSearchResults", start)]
        for token in ("getElementById('q')", "pass", "NODES.filter(pass)"):
            self.assertIn(token, body + self.source)
