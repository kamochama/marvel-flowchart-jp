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
FIXTURE = ROOT / "tests" / "library_v5" / "browser_chronology_fixture.json"
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
        self.assertIn("display-only-endpoint", source)
        self.assertIn("morbius-2022", source)
        self.assertNotIn("semantic SVG remains the", source)

    def test_fixed_chronology_fixture_is_complete_and_validator_is_dom_independent(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(len(fixture), 74)
        self.assertEqual(len({record["edge_id"] for record in fixture}), 74)
        self.assertEqual(sum(record["traversable"] is False for record in fixture), 3)
        self.assertEqual(sum(record["displayOnly"] is True for record in fixture), 3)
        for record in fixture:
            self.assertEqual(
                set(record), {"edge_id", "source", "target", "traversable", "displayOnly"}
            )
            self.assertEqual(record["displayOnly"], record["traversable"] is False)

        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("browser_chronology_fixture.json", source)
        self.assertIn("loadChronologyFixture", source)
        self.assertIn("buildModeOracle", source)
        validator = source[source.index("function validateModeOracle"):source.index("async function setTier")]
        self.assertIn("fixture", validator)
        self.assertNotIn("snapshot.records", validator)
        self.assertNotIn("for (const record of snapshot.records", validator)
        self.assertNotIn("window.computeSelectionState", source)
        self.assertNotIn("window.renderChronologySelectionState", source)
        oracle = source[source.index("function buildModeOracle"):source.index("async function poll")]
        self.assertIn("ORACLE_EDGE_IDS.iron_to_iron2", oracle)
        self.assertIn("record.edge_id === edgeId", oracle)

    def test_structural_audit_checks_fixture_metadata_not_only_edge_ids(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        structural = source[source.index("const structuralFailures"):source.index("cases.push(await runCase")]
        for field in ("source", "target", "traversable", "displayOnly"):
            self.assertIn(f"fixture {field} mismatch", structural)
        self.assertIn("fixtureRecord", structural)

    def test_mode_oracles_keep_or_and_site_tier_independent(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        oracle = source[source.index("const MODE_ORACLE"):source.index("// The structural contract")]
        self.assertIn('combine:"union"', oracle)
        self.assertIn('combine:"intersection"', oracle)
        self.assertNotIn('and: {goals: [PRIMARY_WORK, SECONDARY_WORK], directions: ["incoming", "outgoing"]}', oracle)
        self.assertIn("tierNodeIds", oracle)
        self.assertNotIn("excluded", oracle)
        builder = source[source.index("function buildModeOracle"):source.index("async function poll")]
        self.assertIn("goalMaps", builder)
        self.assertIn("intersection", builder)
        self.assertIn("tierNodeIds", builder)
        self.assertIn("orExpected", source)
        self.assertIn("andExpected", source)
        self.assertIn("oracle mode expectations must differ", source)

    def test_canvas_audit_requires_chronology_metadata_parity(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        canvas = source[source.index("async function canvasChronologySnapshot"):source.index("async function inspectParity")]
        self.assertIn("overlayChronologyDisplayOnly", canvas)
        self.assertIn("overlayChronologyTraversable", canvas)
        self.assertIn("metadata", source[source.index("async function inspectParity"):source.index("async function runCase")])

    def test_display_only_endpoints_are_all_exercised(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        start = source.index('"display-only-endpoint"')
        endpoint_case = source[start:source.index("await clearSelection(cdp,timeoutMs); await setCombine", start)]
        for work_id in ("morbius-2022", "madame-web-2024", "kraven-the-hunter-2024", "deadpool-2016", "logan-2017"):
            self.assertIn(work_id, endpoint_case)

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
