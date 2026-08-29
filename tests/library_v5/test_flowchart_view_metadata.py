from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database
from scripts.library_v5.extract_view_metadata import ViewMetadataError, extract_view_metadata
from scripts.library_v5.flowchart_export import export_flowchart
from scripts.library_v5.build import build


ROOT = Path(__file__).resolve().parents[2]


def _html(
    *,
    nodes: str = '[{"id":"work-a","branch":"枝A","branch_en":"Branch A","priority":"MAIN"}]',
    lanes: str = '[{"id":"main","label":"本線","sub":"説明","tone":"#fff"}]',
    chronology: str = '{"work-a":{"lane":"main","order":10,"track":"main","certainty":"confirmed","note":"基準"}}',
    details: str = '{"work-a":{"synopsis_ja":"あらすじ","map_role_ja":"相関図では起点"}}',
) -> str:
    return (
        f"const NODES={nodes};\n"
        f"const CHRONOLOGY_LANES=Object.freeze({lanes});\n"
        f"const CHRONOLOGY_META=Object.freeze({chronology});\n"
        f"<script id=\"v515-work-details\">window.WORK_DETAILS=Object.freeze({details});</script>"
    )


class FlowchartViewMetadataExtractionTests(unittest.TestCase):
    def test_extracts_presentation_metadata_without_canonical_fields(self) -> None:
        result = extract_view_metadata(_html(), {"work-a"})

        self.assertEqual(
            result,
            {
                "node_metadata": {
                    "work-a": {
                        "branch": "枝A",
                        "branch_en": "Branch A",
                        "priority": "MAIN",
                        "chronology": {
                            "lane": "main",
                            "order": 10,
                            "track": "main",
                            "certainty": "confirmed",
                            "note": "基準",
                        },
                    }
                },
                "chronology_lanes": [
                    {"id": "main", "label": "本線", "sub": "説明", "tone": "#fff"}
                ],
                "details": {
                    "work-a": {"synopsis_ja": "あらすじ", "map_role_ja": "相関図では起点"}
                },
            },
        )

    def test_rejects_missing_or_malformed_markers(self) -> None:
        for marker in ("const NODES", "const CHRONOLOGY_LANES", "const CHRONOLOGY_META", "WORK_DETAILS"):
            text = _html().replace(marker, "missing-marker")
            with self.subTest(marker=marker), self.assertRaises(ViewMetadataError):
                extract_view_metadata(text, {"work-a"})

        with self.assertRaises(ViewMetadataError):
            extract_view_metadata(_html(nodes='{"id":"work-a"}'), {"work-a"})

    def test_rejects_duplicate_and_unknown_work_ids(self) -> None:
        duplicate_nodes = _html(
            nodes='[{"id":"work-a","branch":"A","branch_en":"A","priority":"MAIN"},{"id":"work-a","branch":"B","branch_en":"B","priority":"MAIN"}]'
        )
        with self.assertRaisesRegex(ViewMetadataError, "duplicate.*work"):
            extract_view_metadata(duplicate_nodes, {"work-a"})

        unknown_nodes = _html(nodes='[{"id":"work-z","branch":"Z","branch_en":"Z","priority":"MAIN"}]')
        with self.assertRaisesRegex(ViewMetadataError, "unknown.*work"):
            extract_view_metadata(unknown_nodes, {"work-a"})

        unknown_details = _html(details='{"work-z":{"synopsis_ja":"x","map_role_ja":"y"}}')
        with self.assertRaisesRegex(ViewMetadataError, "unknown.*work"):
            extract_view_metadata(unknown_details, {"work-a"})

    def test_rejects_duplicate_chronology_lanes_and_lane_orders(self) -> None:
        duplicate_lanes = _html(
            lanes='[{"id":"main","label":"本線","sub":"説明","tone":"#fff"},{"id":"main","label":"重複","sub":"説明","tone":"#000"}]'
        )
        with self.assertRaisesRegex(ViewMetadataError, "duplicate.*lane"):
            extract_view_metadata(duplicate_lanes, {"work-a"})

        duplicate_orders = _html(
            chronology='{"work-a":{"lane":"main","order":10,"track":"main","certainty":"confirmed","note":"基準"},"work-b":{"lane":"main","order":10,"track":"main","certainty":"confirmed","note":"基準"}}'
        )
        with self.assertRaisesRegex(ViewMetadataError, "duplicate.*lane.*order"):
            extract_view_metadata(duplicate_orders, {"work-a", "work-b"})

    def test_rejects_non_descriptive_details_and_unknown_chronology_lane(self) -> None:
        extra = _html(details='{"work-a":{"synopsis_ja":"x","map_role_ja":"y","title_ja":"禁止"}}')
        with self.assertRaisesRegex(ViewMetadataError, "details"):
            extract_view_metadata(extra, {"work-a"})

        unknown_lane = _html(
            chronology='{"work-a":{"lane":"missing","order":10,"track":"main","certainty":"confirmed","note":"x"}}'
        )
        with self.assertRaisesRegex(ViewMetadataError, "lane"):
            extract_view_metadata(unknown_lane, {"work-a"})

    def test_checked_in_inputs_cover_db_ids_and_are_sorted_utf8_json(self) -> None:
        works = []
        with (ROOT / "data/library/works.csv").open(encoding="utf-8", newline="") as handle:
            works = [row["work_id"] for row in csv.DictReader(handle)]
        node_view_path = ROOT / "views/flowchart/node_view.json"
        details_path = ROOT / "views/flowchart/details.json"
        node_view = json.loads(node_view_path.read_text(encoding="utf-8"))
        details = json.loads(details_path.read_text(encoding="utf-8"))
        self.assertEqual(set(node_view["node_metadata"]), set(works))
        self.assertEqual(set(details["details"]), set(works))
        self.assertEqual(list(node_view["node_metadata"]), sorted(node_view["node_metadata"]))
        self.assertEqual(list(details["details"]), sorted(details["details"]))
        self.assertEqual(node_view_path.read_bytes().count(b"\r\n"), 0)
        self.assertEqual(details_path.read_bytes().count(b"\r\n"), 0)
        self.assertTrue(node_view_path.read_bytes().endswith(b"\n"))
        self.assertTrue(details_path.read_bytes().endswith(b"\n"))

    def test_export_merges_view_metadata_without_overriding_db_node_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "views", temp / "views")
            db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
            output_path = temp / "flowchart.json"
            export_flowchart(
                temp,
                db_path,
                output_path,
                db_manifest={"db_schema_version": "1", "logical_fingerprint": "test"},
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        policy = payload["view_policy"]
        self.assertEqual(set(policy["node_metadata"]), {row["work_id"] for row in payload["nodes"]})
        self.assertEqual(set(policy["details"]), set(policy["node_metadata"]))
        self.assertEqual({lane["id"] for lane in policy["chronology_lanes"]}, {"mcu-main", "raimi", "amazing", "ssu", "fox-xmen"})
        iron = next(row for row in payload["nodes"] if row["work_id"] == "iron-man-2008")
        self.assertEqual(iron["title_ja"], "アイアンマン")
        self.assertEqual(iron["release"], "2008年")
        self.assertEqual(iron["status"], "released")
        self.assertEqual(policy["node_metadata"]["iron-man-2008"]["branch"], "マーベル・スタジオ映画")
        self.assertNotIn("title_ja", policy["node_metadata"]["iron-man-2008"])

    def test_export_succeeds_with_index_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "views", temp / "views")
            db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
            output_path = temp / "flowchart.json"
            counts = export_flowchart(
                temp,
                db_path,
                output_path,
                db_manifest={"db_schema_version": "1", "logical_fingerprint": "test"},
            )
            self.assertTrue(output_path.exists())
            self.assertEqual(counts["nodes"], 131)

    def test_build_succeeds_with_index_absent_after_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            shutil.copytree(ROOT / "data", temp / "data")
            shutil.copytree(ROOT / "views", temp / "views")
            result = build(temp)

        self.assertTrue(result["audit_ok"])
        self.assertEqual(result["flowchart_export"]["nodes"], 131)


if __name__ == "__main__":
    unittest.main()
