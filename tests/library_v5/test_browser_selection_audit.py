from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLOWCHART = ROOT / "data" / "derived" / "flowchart.json"
RUNNER = ROOT / "tests" / "library_v5" / "browser_selection_audit.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "library-v5-ci.yml"

from tests.library_v5.selection_audit_oracle import SelectionAuditOracle


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


def _expected_payload() -> dict[str, dict[str, dict[str, list[str]]]]:
    payload = json.loads(FLOWCHART.read_text(encoding="utf-8"))
    oracle = SelectionAuditOracle(payload)
    return {
        tier: {
            work_id: {
                "back": sorted(expectation.back_edges),
                "forward": sorted(expectation.forward_edges),
                "context": sorted(expectation.context_edges),
            }
            for work_id in oracle.work_ids
            for expectation in [oracle.expected_main_selection(work_id, tier=tier)]
        }
        for tier in ("site-proposal", "complete")
    }


class BrowserSelectionAuditTests(unittest.TestCase):
    def test_ci_declares_required_headless_audit_job(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("browser-selection-audit:", workflow)
        self.assertIn("needs: test", workflow)
        self.assertIn("MARVEL_BROWSER_AUDIT:", workflow)
        self.assertIn("'1'", workflow)
        self.assertIn("test_browser_selection_audit", workflow)

    def test_runner_help_declares_reproducible_audit_contract(self) -> None:
        result = subprocess.run(
            ["node", str(RUNNER), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--root", result.stdout)
        self.assertIn("--expected", result.stdout)
        self.assertIn("--chrome", result.stdout)

    def test_runner_uses_condition_wait_for_tier_changes(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        start = source.index("async function setTier")
        end = source.index("async function clearSelection", start)
        body = source[start:end]
        self.assertIn("poll(", body)
        self.assertNotIn("setTimeout", body)

    def test_runner_cleans_up_failed_chrome_launch(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        start = source.index("async function launchChrome")
        end = source.index("async function stopChrome", start)
        body = source[start:end]
        self.assertIn("catch", body)
        self.assertIn("stopChrome", body)
        self.assertIn('child.once("error"', body)

    def test_runner_retries_busy_chrome_profile_cleanup(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        match = re.search(r"const CHROME_PROFILE_CLEANUP_RETRIES = (\d+);", source)
        self.assertIsNotNone(match, "profile cleanup must declare a bounded retry budget")
        self.assertGreaterEqual(int(match.group(1)), 50)
        self.assertIn("maxRetries: CHROME_PROFILE_CLEANUP_RETRIES", source)
        self.assertIn("retryDelay:", source)

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_AUDIT") == "1",
        "set MARVEL_BROWSER_AUDIT=1 to run the real headless DOM audit",
    )
    def test_headless_dom_matches_python_oracle_for_both_public_tiers(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(chrome, "Chrome/Chromium is required when MARVEL_BROWSER_AUDIT=1")
        with tempfile.TemporaryDirectory(prefix="marvel-browser-audit-") as temp_dir:
            expected_path = Path(temp_dir) / "expected.json"
            expected_path.write_text(
                json.dumps(_expected_payload(), ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "node",
                    str(RUNNER),
                    "--root",
                    str(ROOT),
                    "--expected",
                    str(expected_path),
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
        self.assertEqual(report["summary"], {
            "site-proposal": {"works": 131, "mismatches": 0},
            "complete": {"works": 131, "mismatches": 0},
        })


if __name__ == "__main__":
    unittest.main()
