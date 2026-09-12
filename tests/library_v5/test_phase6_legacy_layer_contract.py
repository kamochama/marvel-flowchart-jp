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

    def test_phase6_legacy_detail_mirror_is_explicit_active_adapter(self) -> None:
        """Do not delete the live desktop mirror before its owner is replaced."""
        open_body = self.source[self.source.find("function openDockedInspection") :]
        open_body = open_body[: open_body.find("function closeDockedInspection")]
        close_body = self.source[self.source.find("function closeDockedInspection") :]
        close_body = close_body[: close_body.find("function setMobileView")]
        self.assertIn("sheetHostMirror", open_body)
        self.assertIn("renderSheetContent({kind:'detail',workId})", open_body)
        self.assertIn("data-sheet-host-mirror", close_body)
        self.assertIn("sheetHostBody", self.source)

    def test_phase6_search_projection_remains_active_adapter(self) -> None:
        """Mobile search still delegates filtering to the shared DOM-backed predicate."""
        start = self.source.find("function renderMobileSearchResults")
        self.assertGreaterEqual(start, 0)
        body = self.source[start : self.source.find("window.renderMobileSearchResults", start)]
        for token in ("getElementById('q')", "pass", "NODES.filter(pass)"):
            self.assertIn(token, body + self.source)
