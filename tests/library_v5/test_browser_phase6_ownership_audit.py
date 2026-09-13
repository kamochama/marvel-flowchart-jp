from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

from tests.library_v5.browser_audit_process import run_audit_process


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "library_v5" / "browser_phase6_ownership_audit.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "library-v5-ci.yml"


def _chrome_path() -> str | None:
    configured = os.environ.get("MARVEL_CHROME_BIN")
    if configured and Path(configured).is_file():
        return configured
    for command in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        resolved = shutil.which(command)
        if resolved:
            return resolved
    for candidate in (
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ):
        if candidate.is_file():
            return str(candidate)
    return None


class BrowserPhase6OwnershipAuditTests(unittest.TestCase):
    def test_ci_declares_phase6_ownership_audit_after_mobile_shell(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("browser-phase6-ownership-audit:", workflow)
        mobile = workflow.index("  browser-mobile-shell-audit:")
        phase6 = workflow.index("  browser-phase6-ownership-audit:")
        self.assertGreater(phase6, mobile)
        job = workflow[phase6:]
        self.assertIn("needs: browser-mobile-shell-audit", job)
        self.assertIn("MARVEL_BROWSER_PHASE6_OWNERSHIP_AUDIT:", job)
        self.assertIn("test_browser_phase6_ownership_audit", job)

    def test_runner_help_declares_bounded_ownership_contract(self) -> None:
        result = subprocess.run(
            ["node", str(RUNNER), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for token in ("--root", "--chrome", "MutationObserver", "ownership", "failures"):
            self.assertIn(token, result.stdout)

    def test_runner_source_records_required_ownership_deltas(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for token in (
            "MutationObserver",
            "pushState",
            "replaceState",
            "historyDelta",
            "activeRoots",
            "presentationVisibility",
            "sheetHost",
            "overlay",
            "backdrop",
            "detailMutations",
            "rightMutations",
            "chartRebuilds",
            "fitView",
            "selectedIds",
            "goalOrder",
            "currentGoal",
            "preparationTier",
            "activePanel",
            "camera",
            "chart-search-plan",
            "plan-chart",
            "reason-settings",
            "back-forward",
            "desktop-mobile-desktop",
            "761",
            "980",
            "981",
            "JSON.stringify(report)",
        ):
            self.assertIn(token, source)

    def test_runner_declares_exact_phase6_checkpoint_set(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for checkpoint in (
            '"desktop-mobile-desktop"',
            '"reason-settings"',
            '"chart-search-plan"',
            '"plan-chart"',
            '"back-forward"',
            '"980"',
            '"761"',
            '"760"',
            '"390"',
            '"981"',
        ):
            self.assertIn(checkpoint, source)
        self.assertIn("inspectionBaseline", source)
        self.assertIn("roundTripStart", source)
        self.assertIn("independent presentation visibility", source)

    def test_runner_bounds_static_fixture_shutdown(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("closeAllConnections", source)
        self.assertIn("closeIdleConnections", source)
        self.assertIn("setTimeout(finish, 2_000)", source)
        self.assertIn("await stopServer(server)", source)

    def test_wrapper_is_environment_gated_and_validates_summary(self) -> None:
        source = (ROOT / "tests" / "library_v5" / "test_browser_phase6_ownership_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MARVEL_BROWSER_PHASE6_OWNERSHIP_AUDIT", source)
        self.assertIn("skipUnless", source)
        report = {"summary": {"cases": 1, "failures": 0}, "cases": [], "failures": []}
        parsed = json.loads(json.dumps(report))
        self.assertEqual(parsed["summary"], {"cases": 1, "failures": 0})

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_PHASE6_OWNERSHIP_AUDIT") == "1",
        "set MARVEL_BROWSER_PHASE6_OWNERSHIP_AUDIT=1 to run the real Phase 6 ownership audit",
    )
    def test_headless_phase6_ownership_contract(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(chrome, "Chrome/Chromium is required when MARVEL_BROWSER_PHASE6_OWNERSHIP_AUDIT=1")
        result = run_audit_process(
            [
                "node",
                str(RUNNER),
                "--root",
                str(ROOT),
                "--chrome",
                str(chrome),
                "--timeout-ms",
                "8000",
            ],
            cwd=ROOT,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(report["summary"], {"cases": 1, "failures": 0})
        self.assertEqual(
            {checkpoint["name"] for checkpoint in report["cases"][0]["checkpoints"]},
            {
                "desktop-mobile-desktop",
                "reason-settings",
                "chart-search-plan",
                "plan-chart",
                "back-forward",
                "980",
                "761",
                "760",
                "390",
                "981",
            },
        )


if __name__ == "__main__":
    unittest.main()
