from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

from tests.library_v5.browser_audit_process import run_audit_process


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

    def test_runner_bounds_and_retries_chrome_cdp_startup(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("launchChromeWithRetries", source)
        self.assertIn("attempts = 3", source)
        self.assertIn("AbortController", source)
        self.assertIn("signal: controller.signal", source)
        self.assertIn("commandTimeoutMs", source)
        self.assertIn("runAuditWithRetries", source)

    def test_python_wrapper_retries_only_outer_process_timeouts(self) -> None:
        source = (ROOT / "tests" / "library_v5" / "test_browser_interaction_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_audit_process", source)
        self.assertIn("TimeoutExpired", source)

    def test_runner_retries_only_explicit_harness_timeout_reports(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("retryable", source)
        self.assertIn("timed out", source)
        self.assertIn("failure.retryable", source)
        self.assertRegex(source, r"report\.failures\.every\(\(failure\)\s*=>\s*failure\.retryable\s*===\s*true\)")

    def test_runner_closes_static_server_with_keepalive_guard(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("async function closeStaticServer(server)", source)
        self.assertIn("server.closeAllConnections?.()", source)
        self.assertIn("await closeStaticServer(staticServer.server)", source)

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

    def test_runner_proves_phase6_detail_ownership(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('"phase6-detail-ownership"', source)
        self.assertIn("detailHtml", source)
        self.assertIn("detailCardHidden", source)
        self.assertIn("detailMirror", source)
        self.assertIn("hostOwner", source)
        self.assertIn("hostPresentation", source)
        self.assertIn("hostParent", source)
        self.assertIn("historyLength", source)
        self.assertIn('hostParent!=="right"', source)

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_INTERACTION_AUDIT") == "1",
        "set MARVEL_BROWSER_INTERACTION_AUDIT=1 to run the real headless interaction audit",
    )
    def test_headless_interactions_preserve_selection_contract(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(chrome, "Chrome/Chromium is required when MARVEL_BROWSER_INTERACTION_AUDIT=1")
        try:
            result = run_audit_process(
                [
                    "node",
                    str(RUNNER),
                    "--root",
                    str(ROOT),
                    "--chrome",
                    str(chrome),
                ],
                cwd=ROOT,
                timeout=180,
            )
        except subprocess.TimeoutExpired as error:
            self.fail(
                f"browser interaction harness timed out after {error.timeout}s; "
                f"partial stdout={error.output!r}; partial stderr={error.stderr!r}"
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(report["summary"], {"cases": 8, "failures": 0})


if __name__ == "__main__":
    unittest.main()
