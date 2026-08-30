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

    def test_file_open_explains_static_server_requirement(self) -> None:
        """A file:// launch must explain why the JSON-backed viewer is inert."""
        self.assertIn("location.protocol==='file:'", self.source)
        self.assertIn("python -m http.server 8765", self.source)
        self.assertIn("http://127.0.0.1:8765/index.html", self.source)

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
        self.assertIn("policy.default_edge_visibility!=='all'", self.source)
        self.assertIn("policy.default_importance_mode", self.source)
        policy_body = re.search(
            r"function applyFlowchartPolicy\(policy\)\{.*?\n\s*\}",
            self.source,
            re.DOTALL,
        )
        self.assertIsNotNone(policy_body)
        self.assertIn(
            "window.marvelSetImportanceMode(policy.default_importance_mode)",
            policy_body.group(0),
        )
        self.assertNotIn("window.marvelSetConnectionTier(defaultTier)", policy_body.group(0))

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

    def test_payload_rejects_duplicate_edge_ids_and_mismatched_reason_endpoints(self) -> None:
        for marker in (
            "const edgeIds=new Set()",
            "edgeIds.has(row.edge_id)",
            "const reasonsByPayloadId=new Map()",
            "reasonsByPayloadId.set(row.reason_id,row)",
            "reason.source_work_id!==row.source_work_id",
            "reason.target_work_id!==row.target_work_id",
        ):
            self.assertIn(marker, self.source, msg=f"missing payload validation marker: {marker}")

    def test_post_bootstrap_refreshes_missing_edges_and_fan_summary(self) -> None:
        self.assertRegex(
            self.source,
            r"window\.marvelRefreshFlowchartPresentation=\(\)=>\{materializeMissingMasterEdges\(\)",
        )
        self.assertRegex(self.source, r"let\s+fanEdges=\[\]")
        self.assertRegex(self.source, r"window\.marvelRefreshFanEdgeSummary=refreshFanEdgeSummary")
        init = self.source.index("function initializeFlowchartData")
        ready = self.source.index("flowchartReady=true", init)
        refresh = self.source.index("marvelRefreshFlowchartPresentation", ready)
        self.assertLess(ready, refresh)
        self.assertIn("生成JSONに含まれる全接続を表示し、互換性観測値199本を含みます。", self.source)
        self.assertNotIn("生成JSONの全361接続", self.source)
        self.assertNotIn("全199接続", self.source)


if __name__ == "__main__":
    unittest.main()
