from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

THUNDERBOLTS = (
    "work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in"
)
NWH_BND = (
    "work-relation-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31-story-link"
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave001Tests(unittest.TestCase):
    def test_two_relations_have_source_verified_evidence_and_review_transition(self) -> None:
        relation_rows = {
            row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")
        }
        expected = {
            THUNDERBOLTS: {
                "source_work_id": "thunderbolts-new-avengers-2025",
                "target_work_id": "avengers-doomsday-2026-12-18",
                "relation_kind": "lead_in",
                "directness": "strong",
                "certainty": "confirmed",
            },
            NWH_BND: {
                "source_work_id": "spider-man-no-way-home-2021",
                "target_work_id": "spider-man-brand-new-day-2026-07-31",
                "relation_kind": "story_link",
                "directness": "direct",
                "certainty": "confirmed",
            },
        }
        for fact_id, fields in expected.items():
            self.assertIn(fact_id, relation_rows)
            self.assertEqual(relation_rows[fact_id]["verification_status"], "source_verified")
            for field, value in fields.items():
                self.assertEqual(relation_rows[fact_id][field], value)

        evidence_rows = rows(LIB / "evidence.csv")
        evidence_by_fact = {
            fact_id: [row for row in evidence_rows if row["fact_id"] == fact_id]
            for fact_id in expected
        }
        self.assertEqual(
            {
                row["evidence_id"]
                for rows_for_fact in evidence_by_fact.values()
                for row in rows_for_fact
            },
            {
                "evidence-thunderbolts-doomsday-lead-in-marvel-jp-2025-05-14",
                "evidence-thunderbolts-doomsday-key-turning-point-marvel-jp-2025-04-30",
                "evidence-nwh-brand-new-day-story-link-sony-2026",
            },
        )
        for fact_id, rows_for_fact in evidence_by_fact.items():
            self.assertTrue(rows_for_fact)
            self.assertTrue(
                all(row["fact_table"] == "work_relations.csv" for row in rows_for_fact)
            )
            self.assertTrue(
                all(row["evidence_role"] in {"primary", "supporting"} for row in rows_for_fact)
            )

        review_rows = rows(AUDIT / "reviews.csv")
        reviews_by_fact = {
            fact_id: [row for row in review_rows if row["fact_id"] == fact_id]
            for fact_id in expected
        }
        self.assertEqual(
            {row["review_id"] for rows_for_fact in reviews_by_fact.values() for row in rows_for_fact},
            {
                "review-2026-09-03-thunderbolts-doomsday-lead-in",
                "review-2026-09-03-nwh-brand-new-day-story-link",
            },
        )
        for fact_id, rows_for_fact in reviews_by_fact.items():
            self.assertEqual(len(rows_for_fact), 1)
            review = rows_for_fact[0]
            self.assertEqual(review["fact_table"], "work_relations.csv")
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertTrue(review["evidence_ids"])

    def test_existing_directed_pairs_and_reason_ids_are_preserved(self) -> None:
        edge_rows = rows(DERIVED / "work_edges_all.csv")
        reason_rows = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual(len(edge_rows), 355)
        self.assertEqual(len(reason_rows), 562)

        expected_edges = {
            (
                "thunderbolts-new-avengers-2025",
                "avengers-doomsday-2026-12-18",
            ): "edge-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18",
            (
                "spider-man-no-way-home-2021",
                "spider-man-brand-new-day-2026-07-31",
            ): "edge-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31",
        }
        for (source_work_id, target_work_id), edge_id in expected_edges.items():
            edge = next(
                row
                for row in edge_rows
                if row["source_work_id"] == source_work_id
                and row["target_work_id"] == target_work_id
            )
            self.assertEqual(edge["edge_id"], edge_id)
            self.assertIn("explicit-relation-work-relation-", edge["reason_ids"])

        explicit_reasons = {
            row["relation_id"]: row
            for row in reason_rows
            if row["reason_kind"] == "explicit_relation"
            and row["relation_id"] in {THUNDERBOLTS, NWH_BND}
        }
        self.assertEqual(set(explicit_reasons), {THUNDERBOLTS, NWH_BND})
        self.assertEqual(
            (explicit_reasons[THUNDERBOLTS]["source_work_id"], explicit_reasons[THUNDERBOLTS]["target_work_id"]),
            ("thunderbolts-new-avengers-2025", "avengers-doomsday-2026-12-18"),
        )
        self.assertEqual(
            (explicit_reasons[NWH_BND]["source_work_id"], explicit_reasons[NWH_BND]["target_work_id"]),
            ("spider-man-no-way-home-2021", "spider-man-brand-new-day-2026-07-31"),
        )


if __name__ == "__main__":
    unittest.main()
