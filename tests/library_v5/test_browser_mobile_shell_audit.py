from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "library_v5" / "browser_mobile_shell_audit.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "library-v5-ci.yml"

REQUIRED_REPORT_FIELDS = {
    "viewport",
    "views",
    "selection",
    "history",
    "sheet",
    "rerenders",
    "search",
    "plan",
    "failures",
}


def _chrome_path() -> str | None:
    """Resolve Chrome using the same discovery contract as the other audits."""
    configured = os.environ.get("MARVEL_CHROME_BIN")
    if configured and Path(configured).is_file():
        return configured
    for command in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
    ):
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


def _parse_report(stdout: str) -> dict[str, object]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("mobile shell harness did not emit JSON: stdout was empty")
    try:
        report = json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"mobile shell harness emitted invalid JSON: {error}: {stdout!r}"
        ) from error
    if not isinstance(report, dict):
        raise AssertionError("mobile shell harness JSON report must be an object")
    return report


def _validate_report(report: dict[str, object]) -> None:
    missing = sorted(REQUIRED_REPORT_FIELDS.difference(report))
    if missing:
        raise AssertionError(f"mobile shell report is missing {missing[0]}")
    failures = report["failures"]
    if not isinstance(failures, list):
        raise AssertionError("mobile shell report failures must be an array")
    if failures:
        raise AssertionError(f"mobile shell report failures: {failures!r}")


def _successful_report() -> dict[str, object]:
    return {
        "viewport": {"width": 390, "height": 844},
        "views": {},
        "selection": {},
        "history": {},
        "sheet": {},
        "rerenders": {},
        "search": {},
        "plan": {},
        "failures": [],
    }


class BrowserMobileShellAuditTests(unittest.TestCase):
    def test_ci_declares_mobile_shell_audit_after_publication_order(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        publication = workflow.index("  browser-publication-order-audit:")
        mobile = workflow.index("  browser-mobile-shell-audit:")
        self.assertGreater(mobile, publication)
        job = workflow[mobile:]
        self.assertIn("needs: browser-publication-order-audit", job)
        self.assertIn("MARVEL_BROWSER_MOBILE_SHELL_AUDIT:", job)
        self.assertIn("test_browser_mobile_shell_audit.BrowserMobileShellAuditTests.test_headless_mobile_shell_contract", job)

    def test_runner_help_declares_mobile_shell_contract(self) -> None:
        result = subprocess.run(
            ["node", str(RUNNER), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for term in ("--root", "--chrome", "viewport", "selection", "history", "sheet", "rerenders", "search", "plan", "failures"):
            self.assertIn(term, result.stdout)

    def test_runner_source_preserves_required_json_fields(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for field in REQUIRED_REPORT_FIELDS:
            self.assertIn(field, source)
        self.assertIn("JSON.stringify(report)", source)

    def test_runner_retries_transient_chrome_target_startup(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("launchChromeWithRetries", source)
        self.assertIn("attempts = 3", source)

    def test_runner_bounds_devtools_target_fetch(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("AbortController", source)
        self.assertIn("signal: controller.signal", source)

    def test_chrome_discovery_honors_existing_configured_path(self) -> None:
        with tempfile.NamedTemporaryFile() as chrome:
            with mock.patch.dict(os.environ, {"MARVEL_CHROME_BIN": chrome.name}):
                self.assertEqual(_chrome_path(), chrome.name)

    def test_wrapper_rejects_missing_or_malformed_json(self) -> None:
        with self.assertRaisesRegex(AssertionError, "did not emit JSON"):
            _parse_report("")
        with self.assertRaisesRegex(AssertionError, "invalid JSON"):
            _parse_report("not json\n")

    def test_wrapper_rejects_missing_required_report_field(self) -> None:
        report = _successful_report()
        report.pop("search")
        with self.assertRaisesRegex(AssertionError, "missing search"):
            _validate_report(report)

    def test_wrapper_rejects_non_empty_failures(self) -> None:
        report = _successful_report()
        report["failures"] = ["sheet did not close"]
        with self.assertRaisesRegex(AssertionError, "failures"):
            _validate_report(report)

    def test_wrapper_accepts_success_report_with_required_fields(self) -> None:
        report = _parse_report(json.dumps(_successful_report()))
        _validate_report(report)

    def test_wrapper_is_environment_gated(self) -> None:
        source = (ROOT / "tests" / "library_v5" / "test_browser_mobile_shell_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MARVEL_BROWSER_MOBILE_SHELL_AUDIT", source)
        self.assertIn("skipUnless", source)

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_MOBILE_SHELL_AUDIT") == "1",
        "set MARVEL_BROWSER_MOBILE_SHELL_AUDIT=1 to run the real headless mobile shell audit",
    )
    def test_headless_mobile_shell_contract(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(
            chrome,
            "Chrome/Chromium is required when MARVEL_BROWSER_MOBILE_SHELL_AUDIT=1",
        )
        result = subprocess.run(
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
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
            check=False,
        )
        report = _parse_report(result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        _validate_report(report)


if __name__ == "__main__":
    unittest.main()
