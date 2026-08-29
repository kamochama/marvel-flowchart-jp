from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


class IndexDbExportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_html_uses_relative_json_and_has_no_embedded_fact_arrays(self) -> None:
        self.assertRegex(
            self.source,
            r"(?:const|let)\s+FLOWCHART_DATA_URL\s*=\s*['\"]data/derived/flowchart\.json['\"]",
        )
        for name in (
            "NODES",
            "EDGES",
            "CHAR_LINKS",
            "RELEASE_META",
            "CHRONOLOGY_LANES",
            "CHRONOLOGY_META",
        ):
            self.assertNotRegex(
                self.source,
                rf"const\s+{name}\s*=\s*(?:\[|Object\.freeze\s*\()",
                msg=f"{name} must not remain an embedded literal",
            )
        self.assertNotIn(
            '<script id="v515-work-details">window.WORK_DETAILS=Object.freeze({',
            self.source,
        )
        self.assertNotRegex(self.source, r"(?i)(?:sqlite|\.wasm|WebAssembly|sql\.js|wa-sqlite)")

    def test_loader_validates_version_shape_and_reports_japanese_status(self) -> None:
        self.assertRegex(self.source, r"async\s+function\s+loadFlowchartData\s*\(")
        self.assertRegex(self.source, r"function\s+initializeFlowchartData\s*\(")
        self.assertRegex(self.source, r"schema_version")
        self.assertRegex(self.source, r"payload\.nodes")
        self.assertRegex(self.source, r"payload\.edges")
        self.assertRegex(self.source, r"payload\.reasons")
        self.assertRegex(self.source, r"payload\.characters")
        self.assertRegex(self.source, r"読み込み中")
        self.assertRegex(self.source, r"読み込みに失敗")
        self.assertRegex(self.source, r"(?:DOMContentLoaded|readyState)[\s\S]{0,240}loadFlowchartData\s*\(")

    def test_initialization_maps_db_ids_edges_reasons_characters_and_view_policy(self) -> None:
        for marker in (
            "row.work_id",
            "row.source_work_id",
            "row.target_work_id",
            "reasonsById",
            "payload.view_policy",
            "view_policy.node_metadata",
            "view_policy.details",
            "view_policy.chronology_lanes",
            "name_ja",
            "work_ids",
        ):
            self.assertIn(marker, self.source, msg=f"missing bootstrap mapping marker: {marker}")
        self.assertRegex(self.source, r"let\s+flowchartReady\s*=\s*false")
        self.assertRegex(self.source, r"flowchartReady\s*=\s*true")

    def test_initial_render_is_gated_until_successful_bootstrap(self) -> None:
        loader = self.source.index("async function loadFlowchartData")
        render_start = self.source.index("function render")
        self.assertLess(render_start, loader)
        render_body = self.source[render_start: self.source.index("function neighborhood", render_start)]
        self.assertRegex(render_body, r"if\s*\(!flowchartReady\)")
        self.assertRegex(
            self.source[loader:],
            r"(?:DOMContentLoaded|readyState)[\s\S]{0,240}loadFlowchartData\s*\(",
        )
        self.assertRegex(self.source, r"if\s*\(flowchartReady\)initSvgInteraction\s*\(\)")


if __name__ == "__main__":
    unittest.main()
