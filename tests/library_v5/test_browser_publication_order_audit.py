from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "library_v5" / "browser_publication_order_audit.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "library-v5-ci.yml"
FLOWCHART = ROOT / "data" / "derived" / "flowchart.json"


def _parse_report(stdout: str) -> dict[str, object]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("publication-order harness did not emit JSON: stdout was empty")
    try:
        report = json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"publication-order harness did not emit JSON: {error}: {stdout!r}"
        ) from error
    if not isinstance(report, dict):
        raise AssertionError("publication-order harness JSON report must be an object")
    return report


def _summary_line(report: dict[str, object]) -> str:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise AssertionError("publication-order report is missing summary")
    return (
        f"cards={summary.get('cards')}, failures={summary.get('failures')}, "
        f"syntheticEdges={summary.get('syntheticEdges')}"
    )


def _validate_report(report: dict[str, object]) -> None:
    for key in ("summary", "cases", "failures"):
        if key not in report:
            raise AssertionError(f"publication-order report is missing {key}")
    summary = report["summary"]
    if not isinstance(summary, dict):
        raise AssertionError("publication-order report summary must be an object")
    cases = report["cases"]
    if not isinstance(cases, list):
        raise AssertionError("publication-order report cases must be an array")
    for case in cases:
        state = case.get("state") if isinstance(case, dict) else None
        if isinstance(state, dict) and state.get("overlaySyntheticDrawn", 0) != 0:
            raise AssertionError(
                f"{case.get('name', 'unnamed case')} overlaySyntheticDrawn="
                f"{state.get('overlaySyntheticDrawn')}"
            )
    if summary.get("syntheticEdges") != 0:
        raise AssertionError(
            f"publication-order report syntheticEdges={summary.get('syntheticEdges')}"
        )


def _chrome_path() -> str | None:
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


class BrowserPublicationOrderAuditTests(unittest.TestCase):
    def test_ci_declares_publication_order_audit_after_chronology(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        chronology = workflow.index("  browser-chronology-audit:")
        publication = workflow.index("  browser-publication-order-audit:")
        self.assertGreater(publication, chronology)
        job = workflow[publication:]
        self.assertIn("needs: browser-chronology-audit", job)
        self.assertIn("MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT:", job)
        self.assertIn("test_browser_publication_order_audit", job)

    def test_ci_runs_only_the_dedicated_unittest_once(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        publication = workflow.index("  browser-publication-order-audit:")
        job = workflow[publication:]
        command = (
            "python -m unittest "
            "tests.library_v5.test_browser_publication_order_audit."
            "BrowserPublicationOrderAuditTests.test_headless_publication_order_contract -v"
        )
        self.assertEqual(job.count(command), 1)
        self.assertNotIn(
            "run: node tests/library_v5/browser_publication_order_audit.mjs",
            job,
        )

    def test_runner_help_declares_geometry_and_synthetic_contract(self) -> None:
        result = subprocess.run(
            ["node", str(RUNNER), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for term in ("--root", "--chrome", "geometry", "synthetic"):
            self.assertIn(term, result.stdout)

    def test_runner_report_contract_checks_json_and_synthetic_edges(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("JSON.parse", source)
        self.assertIn("summary", source)
        self.assertIn("cases", source)
        self.assertIn("failures", source)
        self.assertIn("overlaySyntheticDrawn", source)
        self.assertIn("syntheticEdges", source)
        self.assertRegex(source, r"(?:no|missing|invalid).*JSON|JSON.*(?:no|missing|invalid)")
        self.assertRegex(source, r"overlaySyntheticDrawn[^\n]*(?:!==|>)")

    def test_runner_uses_real_pc_and_mobile_input_events(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("Input.dispatchMouseEvent", source)
        self.assertIn("Input.dispatchTouchEvent", source)
        self.assertIn("Emulation.setDeviceMetricsOverride", source)
        self.assertIn("Emulation.clearDeviceMetricsOverride", source)
        self.assertNotIn("window.computeSelectionState", source)
        self.assertNotIn("window.renderSelectionState", source)
        mobile = source[source.index("async function selectMobile") : source.index("async function runAudit")]
        self.assertIn("await touchTap(cdp, point)", mobile)
        self.assertIn("await touchDrag(cdp", mobile)
        self.assertNotIn("await clickPoint(cdp", mobile)
        self.assertNotIn("await dragMouse(cdp", mobile)

    def test_runner_checks_exact_cards_geometry_and_line_free_release(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for term in (
            "release-node",
            "data-release-work-id",
            "data-release-precision",
            "data-release-sort-key",
            "data-release-tbd",
            "g.edge",
            "g.chronology-edge",
            "viewBox",
            "path d",
            "release-history-year",
            "release-history-era",
            "release-lane-row",
            "131",
        ):
            self.assertIn(term, source)
        self.assertIn("exact", source.lower())
        self.assertRegex(source, r"duplicate|duplicates")

    def test_runner_checks_precision_tbd_tie_break_and_round_trips(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for term in (
            "precision",
            "isTbd",
            "sortKey",
            "tie",
            "day",
            "month",
            "year",
            "overview",
            "detail",
            "relation",
            "round_trip",
        ):
            self.assertIn(term, source)
        self.assertIn("invented", source.lower())
        self.assertRegex(source, r"(?:month|year).*day|day.*(?:month|year)")

    def test_runner_round_trip_crosses_real_chronology_panel(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        desktop = source[
            source.index("async function runDesktopAudit") : source.index("async function setMobileViewport")
        ]
        for term in (
            "chronology-middle-round-trip",
            '.tab[data-target="chronology"]',
            "chronology panel readiness",
            "chronologyEdges > 0",
            '.tab[data-target="release"]',
            "chronology to release round-trip",
            "chronology round-trip changed",
        ):
            self.assertIn(term, desktop)

    def test_runner_checks_mobile_canvas_selection_lifecycle(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for term in (
            "marvelCanvasAudit",
            "active === true",
            'panel === "release"',
            "nodeBoxes",
            "390",
            "844",
            "overlaySyntheticDrawn",
            "re-tap",
            "background",
            "drag",
            "touch",
        ):
            self.assertIn(term, source)
        self.assertRegex(source, r"overlaySyntheticDrawn\s*!==?\s*0|overlaySyntheticDrawn\s*[><]\s*0")

    def test_wrapper_skips_live_chrome_without_opt_in(self) -> None:
        source = (ROOT / "tests" / "library_v5" / "test_browser_publication_order_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT", source)
        self.assertIn("skipUnless", source)

    def test_wrapper_rejects_missing_json_report(self) -> None:
        with self.assertRaisesRegex(AssertionError, "did not emit JSON"):
            _parse_report("Chrome exited before reporting\n")

    def test_wrapper_rejects_nonzero_case_synthetic_edges(self) -> None:
        report = {
            "summary": {"cards": 131, "failures": 0, "syntheticEdges": 0},
            "cases": [
                {
                    "name": "dated-touch-select",
                    "state": {"overlaySyntheticDrawn": 1},
                }
            ],
            "failures": [],
        }
        with self.assertRaisesRegex(AssertionError, "overlaySyntheticDrawn"):
            _validate_report(report)

    def test_wrapper_formats_required_ci_summary(self) -> None:
        report = {
            "summary": {"cards": 131, "failures": 0, "syntheticEdges": 0},
            "cases": [],
            "failures": [],
        }
        self.assertEqual(
            _summary_line(report),
            "cards=131, failures=0, syntheticEdges=0",
        )

    @unittest.skipUnless(
        os.environ.get("MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT") == "1",
        "set MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT=1 to run the real headless publication-order audit",
    )
    def test_headless_publication_order_contract(self) -> None:
        chrome = _chrome_path()
        self.assertIsNotNone(
            chrome,
            "Chrome/Chromium is required when MARVEL_BROWSER_PUBLICATION_ORDER_AUDIT=1",
        )
        result = subprocess.run(
            ["node", str(RUNNER), "--root", str(ROOT), "--chrome", str(chrome)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
            check=False,
        )
        report = _parse_report(result.stdout)
        print(_summary_line(report), flush=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        _validate_report(report)
        self.assertIn("summary", report)
        self.assertIn("cases", report)
        self.assertIn("failures", report)
        for key in ("focus", "geometry", "line_free", "precision", "tbd", "tie_break", "round_trip", "mobile"):
            self.assertIn(key, report)
        self.assertEqual(report["summary"]["cards"], 131)
        self.assertEqual(report["summary"]["failures"], 0)
        self.assertEqual(report["summary"]["syntheticEdges"], 0)
        self.assertEqual(
            set(report["precision"]),
            {"exact-day", "month-only", "year-only", "tbd"},
        )
        self.assertTrue(report["round_trip"]["release_to_chronology"])
        self.assertTrue(report["round_trip"]["chronology_to_release"])
        self.assertEqual(report["failures"], [])


if __name__ == "__main__":
    unittest.main()
