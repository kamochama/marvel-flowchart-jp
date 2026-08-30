from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "index.html"


class WatchScrollNavigationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_watch_view_keeps_chart_in_document_flow(self) -> None:
        """Opening the plan must not hide the chart needed for upward scrolling."""
        self.assertNotRegex(
            self.html,
            re.compile(
                r"body\.public-watch-view\s+main\s*\{\s*display\s*:\s*none",
                re.IGNORECASE,
            ),
        )
        self.assertRegex(
            self.html,
            re.compile(
                r"body\.public-watch-view\s+main\s*\{\s*display\s*:\s*grid",
                re.IGNORECASE,
            ),
        )

    def test_watch_and_chart_have_scroll_navigation_hooks(self) -> None:
        self.assertIn("watchWorkspace.scrollIntoView", self.html)
        self.assertIn("window.returnToGraphFromWatch", self.html)

    def test_mobile_overlay_restoration_uses_public_selection_state(self) -> None:
        """Global mobile helpers must not reach into the core module's local cache."""
        restore = re.search(
            r"function restoreMobileSelectionOverlayIfNeeded\(.*?\n\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(restore)
        self.assertNotIn("selectionStateCache", restore.group(0))
        self.assertIn("window.__marvelLastSelectionState", restore.group(0))

    def test_minimum_plan_is_direct_core_only(self) -> None:
        """The provisional minimum tier must not fall back to a recursive plan."""
        minimum = re.search(
            r"if\(prepTier==='minimum'\)\{.*?return \{ids,source:",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(minimum)
        self.assertIn("directCore", minimum.group(0))
        self.assertNotIn("recIds", minimum.group(0))

    def test_path_mode_exposes_both_route_preferences(self) -> None:
        """The PATH explanation must have the controls it tells users to use."""
        self.assertRegex(
            self.html,
            re.compile(
                r'class="path-pref-btn active"[^>]+data-path-pref="main"',
                re.IGNORECASE,
            ),
        )
        self.assertRegex(
            self.html,
            re.compile(
                r'class="path-pref-btn"[^>]+data-path-pref="shortest"',
                re.IGNORECASE,
            ),
        )


if __name__ == "__main__":
    unittest.main()
