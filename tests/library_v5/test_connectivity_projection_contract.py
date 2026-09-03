from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ConnectivityProjectionContractTests(unittest.TestCase):
    def test_public_chart_has_only_site_proposal_and_complete_tiers(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        match = re.search(
            r'<select[^>]+id="chartConnectionTier"[^>]*>(.*?)</select>',
            html,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        values = re.findall(r'<option\s+value="([^"]+)"', match.group(1))
        self.assertEqual(values, ["site-proposal", "complete"])

    def test_publication_order_does_not_project_relationship_edges(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-relationship-edges="off"', html)
        self.assertIn("data-release-work-id", html)

    def test_static_export_has_one_node_per_work_and_traceable_edge_reasons(self) -> None:
        payload = json.loads((ROOT / "data" / "derived" / "flowchart.json").read_text(encoding="utf-8"))
        node_ids = [str(row["work_id"]) for row in payload["nodes"]]
        self.assertEqual(len(node_ids), 131)
        self.assertEqual(len(node_ids), len(set(node_ids)))

        edge_pairs = [(row["source_work_id"], row["target_work_id"]) for row in payload["edges"]]
        self.assertEqual(len(edge_pairs), len(set(edge_pairs)))
        reason_ids = {str(row["reason_id"]) for row in payload["reasons"]}
        for edge in payload["edges"]:
            self.assertTrue(edge["reason_ids"])
            self.assertTrue(set(edge["reason_ids"]) <= reason_ids)
            self.assertIn(edge["source_work_id"], node_ids)
            self.assertIn(edge["target_work_id"], node_ids)


if __name__ == "__main__":
    unittest.main()
