from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_export import export_work_graph
from scripts.library_v5.db_fingerprint import logical_fingerprint
from scripts.library_v5.flowchart_export import export_flowchart


ROOT = Path(__file__).resolve().parents[2]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class FlowchartExportContractTests(unittest.TestCase):
    def _compile(self, temp: Path) -> tuple[Path, dict[str, object]]:
        db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
        manifest = logical_fingerprint(db_path, repo_root=ROOT)
        return db_path, manifest

    def test_export_has_versioned_shape_stable_ids_and_reason_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path, manifest = self._compile(temp)
            output_path = temp / "flowchart.json"
            counts = export_flowchart(ROOT, db_path, output_path, db_manifest=manifest)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(payload),
            {"schema_version", "generated_from", "nodes", "edges", "reasons", "characters", "view_policy"},
        )
        self.assertEqual(payload["schema_version"], "1")
        self.assertEqual(
            payload["generated_from"],
            {
                "db_schema_version": manifest["db_schema_version"],
                "logical_fingerprint": manifest["equivalence"],
            },
        )

        node_ids = [row["work_id"] for row in payload["nodes"]]
        self.assertEqual(node_ids, sorted(node_ids))
        self.assertEqual(len(node_ids), len(set(node_ids)))

        edge_ids = [row["edge_id"] for row in payload["edges"]]
        reason_ids = [row["reason_id"] for row in payload["reasons"]]
        self.assertEqual(edge_ids, sorted(edge_ids))
        self.assertEqual(reason_ids, sorted(reason_ids))
        self.assertEqual(len(edge_ids), len(set(edge_ids)))
        self.assertEqual(len(reason_ids), len(set(reason_ids)))
        reasons_by_id = {row["reason_id"]: row for row in payload["reasons"]}
        for edge in payload["edges"]:
            self.assertEqual(edge["reason_ids"], sorted(edge["reason_ids"]))
            self.assertEqual(edge["reason_count"], len(edge["reason_ids"]))
            for reason_id in edge["reason_ids"]:
                reason = reasons_by_id[reason_id]
                self.assertEqual(
                    (reason["source_work_id"], reason["target_work_id"]),
                    (edge["source_work_id"], edge["target_work_id"]),
                )
            for field in (
                "type",
                "type_en",
                "strength",
                "render_class",
                "importance",
                "importance_ja",
                "importance_note",
            ):
                self.assertIn(field, edge)

        self.assertEqual(
            counts,
            {
                "nodes": len(payload["nodes"]),
                "edges": len(payload["edges"]),
                "reasons": len(payload["reasons"]),
                "characters": len(payload["characters"]),
            },
        )

    def test_export_pairs_match_sql_candidates_and_csv_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path, manifest = self._compile(temp)
            output_path = temp / "flowchart.json"
            export_flowchart(ROOT, db_path, output_path, db_manifest=manifest)
            export_work_graph(db_path, temp / "derived")
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            json_pairs = {
                (row["source_work_id"], row["target_work_id"])
                for row in payload["edges"]
            }
            csv_pairs = {
                (row["source_work_id"], row["target_work_id"])
                for row in _read_csv(temp / "derived" / "work_edges_all.csv")
            }
            connection = open_query_connection(db_path)
            try:
                candidate_pairs = {
                    (row[0], row[1])
                    for row in connection.execute(
                        "SELECT source_work_id,target_work_id FROM v_flowchart_edge_candidates"
                    )
                }
            finally:
                connection.close()

        self.assertEqual(json_pairs, candidate_pairs)
        self.assertEqual(json_pairs, csv_pairs)

    def test_export_is_byte_deterministic_and_characters_use_canonical_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path, manifest = self._compile(temp)
            first = temp / "first.json"
            second = temp / "second.json"
            export_flowchart(ROOT, db_path, first, db_manifest=manifest)
            export_flowchart(ROOT, db_path, second, db_manifest=manifest)
            payload = json.loads(first.read_text(encoding="utf-8"))

            connection = open_query_connection(db_path)
            try:
                expected = {
                    entity_id: sorted(work_ids)
                    for entity_id, work_ids in connection.execute(
                        """
                        SELECT h.canonical_entity_id, group_concat(DISTINCT h.work_id)
                        FROM v_entity_work_history AS h
                        JOIN entities AS e ON e.entity_id = h.canonical_entity_id
                        WHERE e.entity_type='character'
                        GROUP BY h.canonical_entity_id
                        ORDER BY h.canonical_entity_id
                        """
                    )
                    for work_ids in [work_ids.split(",")]
                }
                release_ids = {row[0] for row in connection.execute("SELECT release_id FROM releases")}
                status_ids = {
                    row[0]
                    for row in connection.execute(
                        "SELECT production_status_assertion_id FROM production_status_assertions"
                    )
                }
            finally:
                connection.close()
            first_bytes = first.read_bytes()
            second_bytes = second.read_bytes()
            actual = {row["entity_id"]: row["work_ids"] for row in payload["characters"]}
            serialized_reasons = json.dumps(payload["reasons"], ensure_ascii=False)

        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(actual, expected)
        self.assertTrue(all(fact_id not in serialized_reasons for fact_id in release_ids | status_ids))

    def test_export_uses_lf_for_cross_platform_byte_determinism(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path, manifest = self._compile(temp)
            output_path = temp / "flowchart.json"
            export_flowchart(ROOT, db_path, output_path, db_manifest=manifest)
            output = output_path.read_bytes()

        self.assertTrue(output.endswith(b"\n"))
        self.assertFalse(output.endswith(b"\r\n"))
        self.assertNotIn(b"\r\n", output)

    def test_policy_has_all_edge_defaults_and_conservative_reason_kind_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path, manifest = self._compile(temp)
            output_path = temp / "flowchart.json"
            export_flowchart(ROOT, db_path, output_path, db_manifest=manifest)
            policy = json.loads(output_path.read_text(encoding="utf-8"))["view_policy"]

        self.assertEqual(policy["default_edge_visibility"], "all")
        self.assertEqual(policy["default_importance_mode"], "reference")
        rules = policy["reason_kind_rules"]
        self.assertEqual(
            set(rules),
            {"explicit_relation", "shared_entity", "multiverse_transition", "fallback"},
        )
        for rule in rules.values():
            self.assertTrue(rule["label_ja"])
            self.assertTrue(rule["label_en"])
            self.assertTrue(rule["strength_thresholds"])
            self.assertTrue(rule["importance_thresholds"])


if __name__ == "__main__":
    unittest.main()
