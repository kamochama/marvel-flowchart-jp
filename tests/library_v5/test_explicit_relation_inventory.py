from __future__ import annotations

import unittest
from pathlib import Path

from scripts.library_v5.explicit_relation_inventory import (
    _markdown,
    _disposition,
    _split_preserve_duplicates,
    build_inventory,
)


ROOT = Path(__file__).resolve().parents[2]


class ExplicitRelationInventoryTests(unittest.TestCase):
    def test_inventory_covers_every_relation_row(self) -> None:
        report = build_inventory(ROOT)
        self.assertEqual(
            report["summary"],
            {
                "total": 164,
                "active": 161,
                "source_verified": 62,
                "legacy_seed": 99,
                "superseded": 3,
            },
        )
        self.assertEqual(report["coverage"]["missing_relation_ids"], [])
        self.assertEqual(report["coverage"]["duplicate_relation_ids"], [])

    def test_source_verified_relations_have_exact_provenance(self) -> None:
        report = build_inventory(ROOT)
        self.assertEqual(report["coverage"]["source_verified_missing_evidence"], [])
        self.assertEqual(report["coverage"]["source_verified_missing_review"], [])
        self.assertEqual(report["coverage"]["source_verified_missing_source"], [])
        for row in report["relations"]:
            if row["verification_status"] == "source_verified":
                self.assertTrue(row["evidence_ids"])
                self.assertTrue(row["review_ids"])
                self.assertEqual(row["disposition"], "retain")

    def test_relation_provenance_does_not_fan_out_by_fact_id(self) -> None:
        report = build_inventory(ROOT)
        row = next(
            item
            for item in report["relations"]
            if item["work_relation_id"]
            == "work-relation-avengers-age-of-ultron-2015-captain-america-civil-war-2016-aftermath"
        )
        self.assertTrue(
            all(item["fact_table"] == "work_relations.csv" for item in row["source_facts"])
        )

    def test_graph_topology_is_unchanged(self) -> None:
        report = build_inventory(ROOT)
        self.assertEqual(report["graph"], {"works": 131, "edges": 355, "reasons": 562})
        self.assertEqual(report["coverage"]["projection_mismatches"], 0)
        self.assertEqual(report["coverage"]["reason_orphans"], 0)

    def test_each_active_relation_has_exact_reason_support_and_edge_projection(self) -> None:
        report = build_inventory(ROOT)
        for key in (
            "relation_reason_missing",
            "relation_reason_duplicate",
            "relation_reason_direction",
            "relation_reason_support",
            "relation_reason_status",
            "relation_reason_certainty",
            "relation_reason_edge",
            "relation_reason_edge_duplicate",
            "relation_reason_notes",
            "relation_reason_id",
            "extra_explicit_relation_reasons",
            "superseded_reason_orphans",
            "source_verified_missing_qualifying_evidence",
            "review_missing_evidence",
        ):
            self.assertEqual(report["coverage"][key], [], key)
        for row in report["relations"]:
            if row["verification_status"] != "superseded":
                self.assertEqual(len(row["reason_ids"]), 1)
                self.assertEqual(len(row["edge_ids"]), 1)

    def test_source_verified_rows_expose_same_fact_and_external_evidence(self) -> None:
        report = build_inventory(ROOT)
        for row in report["relations"]:
            if row["verification_status"] == "source_verified":
                self.assertTrue(row["qualifying_evidence_ids"])
                self.assertTrue(
                    all(
                        detail["fact_table"] == "work_relations.csv"
                        and detail["fact_id"] == row["work_relation_id"]
                        for detail in row["source_details"]
                        if detail["evidence_id"] in row["qualifying_evidence_ids"]
                    )
                )

    def test_markdown_report_renders_without_formatting_collision(self) -> None:
        report = build_inventory(ROOT)
        markdown = _markdown(report)
        self.assertIn("# Marvel explicit relation inventory", markdown)
        self.assertIn("work-relation-iron-man-2008-iron-man-2-2010-sequel", markdown)

    def test_edge_reason_parser_preserves_duplicate_tokens_for_audit(self) -> None:
        self.assertEqual(_split_preserve_duplicates("reason-a|reason-a|reason-b"), [
            "reason-a",
            "reason-a",
            "reason-b",
        ])

    def test_blank_source_id_is_reported_as_missing_provenance(self) -> None:
        disposition, source_ids = _disposition(
            {"verification_status": "source_verified"},
            [{"source_id": "", "evidence_role": "primary"}],
            [{"review_id": "review-1"}],
            {},
        )
        self.assertEqual(disposition, "defer")
        self.assertEqual(source_ids, [""])


if __name__ == "__main__":
    unittest.main()
