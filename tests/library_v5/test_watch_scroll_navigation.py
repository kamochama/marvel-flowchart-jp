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


if __name__ == "__main__":
    unittest.main()
