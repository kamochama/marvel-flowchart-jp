from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.library_v5.connection_inventory import audit_inventory, build_inventory
from scripts.library_v5.connectivity_audit import audit_repository


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_DISPOSITIONS = {"retain", "needs-source", "explicit-conflict", "defer"}


class ConnectionInventoryTests(unittest.TestCase):
    def test_current_main_has_complete_inventory_coverage(self) -> None:
        inventory = audit_inventory(ROOT)

        self.assertEqual(inventory["counts"]["works"], 131)
        self.assertEqual(inventory["counts"]["edges"], 355)
        self.assertEqual(inventory["counts"]["reasons"], 562)
        self.assertEqual(inventory["counts"]["works"], len(inventory["works"]))
        self.assertEqual(inventory["counts"]["edges"], len(inventory["edges"]))
        self.assertEqual(inventory["counts"]["reasons"], len(inventory["reasons"]))
        self.assertEqual(inventory["coverage"]["missing_work_ids"], [])
        self.assertEqual(inventory["coverage"]["duplicate_work_ids"], [])
        self.assertEqual(inventory["coverage"]["missing_reason_ids"], [])
        self.assertEqual(inventory["coverage"]["duplicate_reason_ids"], [])
        self.assertEqual(inventory["coverage"]["duplicate_edge_pairs"], [])
        self.assertEqual(inventory["coverage"]["projection_mismatches"], 0)
        self.assertEqual(inventory["coverage"]["reason_orphans"], 0)
        self.assertEqual(inventory["coverage"]["unsupported_transition_edges"], 0)
        self.assertEqual(inventory["coverage"]["missing_inputs"], [])
        self.assertEqual(inventory["coverage"]["source_duplicate_edge_pairs"], [])
        self.assertEqual(inventory["coverage"]["payload_missing_work_ids"], [])
        self.assertEqual(inventory["coverage"]["payload_extra_work_ids"], [])
        self.assertEqual(inventory["coverage"]["payload_missing_edge_pairs"], [])
        self.assertEqual(inventory["coverage"]["payload_extra_edge_pairs"], [])
        self.assertEqual(inventory["coverage"]["payload_missing_reason_ids"], [])
        self.assertEqual(inventory["coverage"]["payload_extra_reason_ids"], [])
        self.assertEqual(inventory["coverage"]["verified_reason_missing_evidence_ids"], [])
        self.assertEqual(inventory["coverage"]["verified_reason_missing_review_ids"], [])
        self.assertEqual(inventory["coverage"]["unresolved_source_fact_ids"], [])
        self.assertEqual(inventory["coverage"]["verified_support_fact_missing_evidence"], [])
        self.assertEqual(inventory["coverage"]["verified_support_fact_missing_review"], [])
        self.assertTrue(
            set(inventory["dispositions"]["edges"]) <= ALLOWED_DISPOSITIONS
        )
        self.assertTrue(
            set(inventory["dispositions"]["works"]) <= ALLOWED_DISPOSITIONS
        )
        self.assertTrue(
            set(inventory["dispositions"]["reasons"]) <= ALLOWED_DISPOSITIONS
        )
        self.assertEqual(len(inventory["zero_degree_works"]), 8)

    def test_missing_reason_id_is_reported_exactly(self) -> None:
        report = audit_repository(ROOT)
        mutated = copy.deepcopy(report)
        mutated["_expected_reason_ids"] = [
            reason["reason_id"]
            for edge in report["edge_inventory"]
            for reason in edge["reasons"]
        ]
        removed_reason = mutated["edge_inventory"][0]["reason_ids"][0]
        mutated["edge_inventory"][0]["reason_ids"] = [
            reason_id
            for reason_id in mutated["edge_inventory"][0]["reason_ids"]
            if reason_id != removed_reason
        ]
        mutated["edge_inventory"][0]["reasons"] = [
            reason
            for reason in mutated["edge_inventory"][0]["reasons"]
            if reason["reason_id"] != removed_reason
        ]

        inventory = build_inventory(mutated)

        self.assertEqual(inventory["coverage"]["missing_reason_ids"], [removed_reason])

    def test_unknown_disposition_is_rejected(self) -> None:
        report = audit_repository(ROOT)
        mutated = copy.deepcopy(report)
        mutated["edge_inventory"][0]["disposition"] = "invented"

        with self.assertRaisesRegex(ValueError, "unknown disposition"):
            build_inventory(mutated)

    def test_shared_entity_provenance_does_not_fan_out_between_facts(self) -> None:
        inventory = audit_inventory(ROOT)
        reason = next(
            row
            for row in inventory["reasons"]
            if row.get("reason_kind") == "shared_entity"
            and row.get("source_work_id") == "avengers-age-of-ultron-2015"
            and row.get("target_work_id") == "avengers-endgame-2019"
            and "appearance-avengers-age-of-ultron-2015-entity-x-7250204b23"
            in row.get("source_fact_ids", [])
        )
        age_fact = next(
            fact
            for fact in reason["source_facts"]
            if fact["fact_id"] == "appearance-avengers-age-of-ultron-2015-entity-x-7250204b23"
        )
        self.assertEqual(age_fact["fact_table"], "appearances.csv")
        self.assertEqual(age_fact["evidence_ids"], [])
        self.assertNotIn(
            "evidence-appearances-csv-appearance-avengers-doomsday-2026-12-18-entity-x-7250204b23-doomsday",
            age_fact["evidence_ids"],
        )
        self.assertEqual(reason["source_fact_table"], ["appearances.csv"])

    def test_markdown_contains_reason_level_provenance_table(self) -> None:
        from scripts.library_v5.connection_inventory import render_markdown

        markdown = render_markdown(audit_inventory(ROOT))
        self.assertIn("## All reasons with exact fact provenance", markdown)
        self.assertIn("| reason_id | source | target | kind | source_facts |", markdown)
        self.assertGreaterEqual(markdown.count("| `reason-"), 562)

    def test_baseline_override_is_recorded_for_archive_checkouts(self) -> None:
        inventory = audit_inventory(ROOT, baseline_sha="example-baseline")

        self.assertEqual(inventory["baseline_sha"], "example-baseline")


if __name__ == "__main__":
    unittest.main()
