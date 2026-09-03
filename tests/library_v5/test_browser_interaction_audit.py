from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "library_v5" / "browser_interaction_audit.mjs"
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


class BrowserInteractionAuditTests(unittest.TestCase):
    def test_ci_declares_interaction_audit_job(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("browser-interaction-audit:", workflow)
        self.assertIn("MARVEL_BROWSER_INTERACTION_AUDIT:", workflow)
        self.assertIn("test_browser_interaction_audit", workflow)

    def test_runner_help_declares_reproducible_contract(self) -> None:
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
        self.assertIn("re-click", result.stdout)

    def test_runner_uses_real_pointer_events_and_condition_waits(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('Input.dispatchMouseEvent', source)
        self.assertIn('await poll(', source)
        self.assertNotIn('window.marvelReturnToGoalView', source)

    def test_runner_proves_drag_and_chronology_repaint(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("drag did not change SVG transform", source)
        self.assertIn("chronologyHighlighted > 0", source)

    def test_runner_proves_release_has_no_mobile_synthetic_overlay(self) -> None:
        """Release selection must expose the mobile no-synthetic-edge contract."""
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("Emulation.setDeviceMetricsOverride", source)
        self.assertRegex(source, r"width:\s*390")
        self.assertIn("canvasAudit.active === true", source)
        self.assertIn('canvasAudit.panel === "release"', source)
        self.assertIn("wrap.scrollIntoView", source)
        self.assertIn("state.selected.includes(REPRESENTATIVE_WORK)", source)
        self.assertIn("overlaySyntheticDrawn", source)
        self.assertIn("overlaySyntheticDrawn === 0", source)

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_INTERACTION_AUDIT") == "1",
        "set MARVEL_BROWSER_INTERACTION_AUDIT=1 to run the real headless interaction audit",
    )
    def test_headless_interactions_preserve_selection_contract(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(chrome, "Chrome/Chromium is required when MARVEL_BROWSER_INTERACTION_AUDIT=1")
        with tempfile.TemporaryDirectory(prefix="marvel-browser-interaction-") as temp_dir:
            result = subprocess.run(
                [
                    "node",
                    str(RUNNER),
                    "--root",
                    str(ROOT),
                    "--chrome",
                    str(chrome),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(report["summary"], {"cases": 6, "failures": 0})


if __name__ == "__main__":
    unittest.main()
