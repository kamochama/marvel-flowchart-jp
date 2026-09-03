from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def rows(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class VariantFanoutAuditTests(unittest.TestCase):
    """Regression contract for the explicitly distinct D&W Wolverine variant."""

    def test_deadpool_wolverine_uses_a_distinct_variant_entity(self) -> None:
        entities = {row["entity_id"]: row for row in rows("entities.csv")}
        relations = {row["entity_relation_id"]: row for row in rows("entity_relations.csv")}
        appearances = {row["appearance_id"]: row for row in rows("appearances.csv")}

        variant_id = "entity-x-dw-wolverine-variant-2024"
        legacy_id = "entity-x-680db112c0"
        variant_relation_id = "entity-relation-dw-wolverine-variant-of-logan-2017"
        variant_appearance_id = "appearance-deadpool-wolverine-2024-entity-x-dw-wolverine-variant-2024"
        legacy_appearance_id = "appearance-deadpool-wolverine-2024-entity-x-680db112c0"

        self.assertIn(variant_id, entities)
        self.assertEqual(entities[variant_id]["entity_type"], "character")
        relation = relations[variant_relation_id]
        self.assertEqual(relation["source_entity_id"], variant_id)
        self.assertEqual(relation["relation_kind"], "variant_of")
        self.assertEqual(relation["target_entity_id"], legacy_id)
        self.assertEqual(relation["certainty"], "confirmed")
        self.assertEqual(relation["verification_status"], "source_verified")

        self.assertEqual(appearances[variant_appearance_id]["entity_id"], variant_id)
        self.assertEqual(appearances[variant_appearance_id]["verification_status"], "source_verified")
        self.assertEqual(appearances[legacy_appearance_id]["verification_status"], "superseded")

    def test_variant_boundary_keeps_logan_story_link_without_shared_entity_fanout(self) -> None:
        from scripts.library_v5.derive_edges import derive_reasons

        all_works = rows("works.csv")
        appearances = rows("appearances.csv")
        explicit_relations = [
            row
            for row in rows("work_relations.csv")
            if row["work_relation_id"] == "work-relation-logan-2017-deadpool-wolverine-2024-story-link"
        ]
        entity_relations = rows("entity_relations.csv")
        reasons = derive_reasons(
            all_works,
            appearances,
            explicit_relations,
            entity_relations,
            mode="combined_all_pairs",
        )

        pair = [
            row
            for row in reasons
            if {row["source_work_id"], row["target_work_id"]}
            == {"logan-2017", "deadpool-wolverine-2024"}
        ]
        self.assertTrue(any(row["reason_kind"] == "explicit_relation" for row in pair))
        self.assertFalse(
            any(
                row["reason_kind"] == "shared_entity"
                and row["entity_id"] == "entity-x-680db112c0"
                for row in pair
            )
        )

    def test_variant_facts_have_qualifying_evidence_and_review(self) -> None:
        evidence = {
            (row["fact_table"], row["fact_id"]): row
            for row in rows("evidence.csv")
            if row["evidence_role"] in {"primary", "supporting"}
        }
        reviews = {
            (row["fact_table"], row["fact_id"]): row
            for row in rows_from_audit("reviews.csv")
        }
        expected = {
            ("entity_relations.csv", "entity-relation-dw-wolverine-variant-of-logan-2017"),
            ("appearances.csv", "appearance-deadpool-wolverine-2024-entity-x-dw-wolverine-variant-2024"),
        }
        self.assertTrue(expected <= set(evidence))
        self.assertTrue(expected <= set(reviews))


def rows_from_audit(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / "content_audit" / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
