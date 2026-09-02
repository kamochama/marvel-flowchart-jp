from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "library_v5" / "browser_chronology_audit.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "library-v5-ci.yml"


def _chrome_path() -> str | None:
    configured = os.environ.get("MARVEL_CHROME_BIN")
    if configured and Path(configured).is_file():
        return configured
    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
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


class BrowserChronologyAuditTests(unittest.TestCase):
    def test_ci_declares_dedicated_chronology_audit_after_interaction(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        interaction = workflow.index("  browser-interaction-audit:")
        chronology = workflow.index("  browser-chronology-audit:")
        self.assertGreater(chronology, interaction)
        chronology_job = workflow[chronology:]
        self.assertIn("needs: browser-interaction-audit", chronology_job)
        self.assertIn("MARVEL_BROWSER_CHRONOLOGY_AUDIT:", chronology_job)
        self.assertIn("test_browser_chronology_audit.BrowserChronologyAuditTests.test_headless_chronology_contract", chronology_job)

    def test_runner_help_declares_chronology_contract(self) -> None:
        result = subprocess.run(
            ["node", str(RUNNER), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--root", result.stdout)
        self.assertIn("--chrome", result.stdout)
        self.assertIn("non-traversable", result.stdout)
        self.assertIn("edge-id", result.stdout)

    def test_runner_uses_public_pointer_events_and_condition_polling(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("Input.dispatchMouseEvent", source)
        self.assertIn("await poll(", source)
        self.assertIn("data-chronology-edge-id", source)
        self.assertIn("overlayChronologyEdgeId", source)
        self.assertNotIn("window.computeSelectionState", source)
        self.assertNotIn("window.renderChronologySelectionState", source)
        self.assertNotIn("querySelectorAll('g.edge')", source)
        self.assertNotIn('querySelectorAll("g.edge")', source)
        self.assertNotIn("await sleep(", source)

    def test_runner_report_declares_structural_mode_and_parity_results(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for label in (
            "structural",
            "modes",
            "non_traversable",
            "duplicate_ids",
            "svg_canvas_parity",
            "round_trip",
            "coverage_gaps",
        ):
            self.assertIn(label, source)
        self.assertIn("failures", source)
        self.assertIn('coverage:"internal-unit-only"', source)
        self.assertIn("MODE_ORACLE", source)
        self.assertIn("validateModeOracle", source)
        self.assertIn("ORACLE_EDGE_IDS", source)
        self.assertIn("unexpected highlighted", source)
        self.assertIn("category mismatch", source)

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_CHRONOLOGY_AUDIT") == "1",
        "set MARVEL_BROWSER_CHRONOLOGY_AUDIT=1 to run the real headless chronology audit",
    )
    def test_headless_chronology_contract(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(chrome, "Chrome/Chromium is required when MARVEL_BROWSER_CHRONOLOGY_AUDIT=1")
        with tempfile.TemporaryDirectory(prefix="marvel-browser-chronology-") as temp_dir:
            result = subprocess.run(
                ["node", str(RUNNER), "--root", str(ROOT), "--chrome", str(chrome)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        try:
            report = json.loads(result.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as error:
            self.fail(f"chronology harness did not emit JSON: {error}: {result.stdout!r}")
        self.assertEqual(report["summary"]["failures"], 0)
        self.assertEqual(report["structural"]["edge_count"], 74)
        self.assertEqual(report["structural"]["duplicate_ids"], [])
        self.assertEqual(report["structural"]["display_only_highlighted"], [])
        self.assertEqual(report["svg_canvas_parity"]["failures"], [])
        self.assertTrue(report["svg_canvas_parity"]["canvas_available"])
        self.assertTrue(report["round_trip"]["overview_to_chronology"])
        self.assertTrue(report["round_trip"]["chronology_to_overview"])


if __name__ == "__main__":
    unittest.main()
