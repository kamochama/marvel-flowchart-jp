from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.library_v5.browser_audit_process import run_audit_process


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
    "phase4",
    "phase5",
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
    phase4 = report["phase4"]
    if not isinstance(phase4, dict) or not isinstance(phase4.get("search"), dict) or not isinstance(phase4.get("plan"), dict):
        raise AssertionError("mobile shell report phase4 must contain search and plan objects")
    search = phase4["search"]
    plan = phase4["plan"]
    for section, required in (
        (search, ("focusPreserved", "scrollPreserved", "chartRebuilds", "historyGrowth")),
        (plan, ("anchorPreserved", "chartRebuilds", "historyGrowth")),
    ):
        missing_section = [key for key in required if key not in section]
        if missing_section:
            raise AssertionError(f"mobile shell report phase4 field missing: {missing_section[0]}")
    if not search["focusPreserved"] or not search["scrollPreserved"] or search["chartRebuilds"] != 0 or search["historyGrowth"] != 0:
        raise AssertionError(f"mobile shell phase4 search contract failed: {search!r}")
    if not plan["anchorPreserved"] or plan["chartRebuilds"] != 0 or plan["historyGrowth"] != 0:
        raise AssertionError(f"mobile shell phase4 plan contract failed: {plan!r}")
    phase5 = report["phase5"]
    if not isinstance(phase5, dict) or not isinstance(phase5.get("shellBoundary"), dict):
        raise AssertionError("mobile shell report phase5 must contain shellBoundary")
    expected_boundaries = {"portrait390", "landscape844", "width760", "width761", "width980", "width981"}
    if set(phase5["shellBoundary"]) != expected_boundaries:
        raise AssertionError(f"mobile shell phase5 boundaries mismatch: {phase5['shellBoundary']!r}")
    if any(not isinstance(row, dict) or row.get("ok") is not True for row in phase5["shellBoundary"].values()):
        raise AssertionError(f"mobile shell phase5 boundary contract failed: {phase5!r}")
    if phase5.get("coarseLandscape") is not True or phase5.get("visualViewportHeightInvariant") is not True:
        raise AssertionError(f"mobile shell phase5 coarse/height contract failed: {phase5!r}")


def _format_timeout_diagnostic(error: subprocess.TimeoutExpired) -> str:
    """Keep partial Node output visible when the outer watchdog fires."""
    stdout = error.stdout or ""
    stderr = error.stderr or ""
    return (
        f"mobile shell harness timed out after {error.timeout}s; "
        f"partial stdout={stdout!r}; partial stderr={stderr!r}"
    )


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
        "phase4": {
            "search": {"focusPreserved": True, "scrollPreserved": True, "chartRebuilds": 0, "historyGrowth": 0},
            "plan": {"anchorPreserved": True, "chartRebuilds": 0, "historyGrowth": 0},
        },
        "phase5": {
            "shellBoundary": {
                key: {"ok": True}
                for key in ("portrait390", "landscape844", "width760", "width761", "width980", "width981")
            },
            "coarseLandscape": True,
            "visualViewportHeightInvariant": True,
        },
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

    def test_python_wrapper_retries_only_outer_process_timeouts(self) -> None:
        source = (ROOT / "tests" / "library_v5" / "test_browser_mobile_shell_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_audit_process", source)
        self.assertIn("TimeoutExpired", source)

    def test_runner_closes_static_server_with_keepalive_guard(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("async function closeStaticServer(server)", source)
        self.assertIn("server.closeAllConnections?.()", source)
        self.assertIn("await closeStaticServer(staticServer.server)", source)

    def test_runner_bounds_cdp_connection_and_retries_audit(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("CDP_COMMAND_TIMEOUT_MS", source)
        self.assertIn("CDP WebSocket connection timed out", source)
        self.assertIn("runAuditWithRetries", source)

    def test_runner_does_not_retry_semantic_failures(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("const report = await runAudit(args);\n      return report;", source)
        self.assertNotIn("if (!report.failures.length) return report;", source)

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

    def test_timeout_diagnostic_preserves_partial_node_output(self) -> None:
        error = subprocess.TimeoutExpired(
            ["node", str(RUNNER)],
            timeout=240,
            output="partial stdout",
            stderr="partial stderr",
        )
        diagnostic = _format_timeout_diagnostic(error)
        self.assertIn("partial stdout", diagnostic)
        self.assertIn("partial stderr", diagnostic)

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
        try:
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
        except subprocess.TimeoutExpired as error:
            self.fail(_format_timeout_diagnostic(error))
        report = _parse_report(result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        _validate_report(report)


if __name__ == "__main__":
    unittest.main()
