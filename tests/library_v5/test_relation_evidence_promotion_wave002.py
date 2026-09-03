from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

WANDAVISION_AGATHA = "work-relation-wandavision-2021-agatha-all-along-2024-spinoff"
AGATHA_VISIONQUEST = "work-relation-agatha-all-along-2024-visionquest-2026-10-14-sequel"
WANDAVISION_VISIONQUEST = "work-relation-wandavision-2021-visionquest-2026-10-14-sequel"
XMEN97_S1_S2 = "work-relation-x-men-97-s1-2024-x-men-97-s2-2026-07-01-sequel"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave002Tests(unittest.TestCase):
    def test_four_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relation_rows = {
            row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")
        }
        expected = {
            WANDAVISION_AGATHA: (
                "wandavision-2021",
                "agatha-all-along-2024",
                "spinoff",
                "strong",
                "probable",
                "evidence-wandavision-agatha-spinoff-disney-2024",
                "disney-agatha-all-along-2024",
                "review-2026-09-03-wandavision-agatha-spinoff",
            ),
            AGATHA_VISIONQUEST: (
                "agatha-all-along-2024",
                "visionquest-2026-10-14",
                "sequel",
                "strong",
                "confirmed",
                "evidence-agatha-visionquest-trilogy-marvel-2026",
                "visionquest",
                "review-2026-09-03-agatha-visionquest-trilogy",
            ),
            WANDAVISION_VISIONQUEST: (
                "wandavision-2021",
                "visionquest-2026-10-14",
                "sequel",
                "strong",
                "confirmed",
                "evidence-wandavision-visionquest-trilogy-marvel-2026",
                "visionquest",
                "review-2026-09-03-wandavision-visionquest-trilogy",
            ),
            XMEN97_S1_S2: (
                "x-men-97-s1-2024",
                "x-men-97-s2-2026-07-01",
                "sequel",
                "direct",
                "confirmed",
                "evidence-xmen97-s1-s2-season-continuation-marvel-2026",
                "xmen97-s2",
                "review-2026-09-03-xmen97-s1-s2-continuation",
            ),
        }

        source_rows = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        self.assertEqual(
            source_rows["disney-agatha-all-along-2024"]["url"],
            "https://thewaltdisneycompany.com/news/a-magical-look-at-the-making-of-agatha-all-along-with-kathryn-hahn-and-jac-schaeffer/",
        )

        evidence_rows = rows(LIB / "evidence.csv")
        review_rows = rows(AUDIT / "reviews.csv")
        for fact_id, (
            source_work_id,
            target_work_id,
            relation_kind,
            directness,
            certainty,
            evidence_id,
            source_id,
            review_id,
        ) in expected.items():
            relation = relation_rows[fact_id]
            self.assertEqual(relation["verification_status"], "source_verified")
            self.assertEqual(relation["source_work_id"], source_work_id)
            self.assertEqual(relation["target_work_id"], target_work_id)
            self.assertEqual(relation["relation_kind"], relation_kind)
            self.assertEqual(relation["directness"], directness)
            self.assertEqual(relation["certainty"], certainty)

            evidence = [row for row in evidence_rows if row["evidence_id"] == evidence_id]
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["fact_table"], "work_relations.csv")
            self.assertEqual(evidence[0]["fact_id"], fact_id)
            self.assertEqual(evidence[0]["source_id"], source_id)
            self.assertEqual(evidence[0]["evidence_role"], "primary")

            review = [row for row in review_rows if row["review_id"] == review_id]
            self.assertEqual(len(review), 1)
            self.assertEqual(review[0]["fact_table"], "work_relations.csv")
            self.assertEqual(review[0]["fact_id"], fact_id)
            self.assertEqual(review[0]["previous_verification_status"], "legacy_seed")
            self.assertEqual(review[0]["new_verification_status"], "source_verified")
            self.assertEqual(review[0]["review_action"], "verified_source")
            self.assertEqual(review[0]["evidence_ids"], evidence_id)

    def test_existing_pairs_and_explicit_reason_ids_are_preserved(self) -> None:
        edge_rows = rows(DERIVED / "work_edges_all.csv")
        reason_rows = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual(len(edge_rows), 355)
        self.assertEqual(len(reason_rows), 562)

        expected_pairs = {
            WANDAVISION_AGATHA: ("wandavision-2021", "agatha-all-along-2024"),
            AGATHA_VISIONQUEST: ("agatha-all-along-2024", "visionquest-2026-10-14"),
            WANDAVISION_VISIONQUEST: ("wandavision-2021", "visionquest-2026-10-14"),
            XMEN97_S1_S2: ("x-men-97-s1-2024", "x-men-97-s2-2026-07-01"),
        }
        for relation_id, (source_work_id, target_work_id) in expected_pairs.items():
            edge = next(
                row
                for row in edge_rows
                if row["source_work_id"] == source_work_id
                and row["target_work_id"] == target_work_id
            )
            expected_reason_id = (
                f"reason-{source_work_id}-{target_work_id}-"
                f"explicit-relation-{relation_id}"
            )
            self.assertIn(expected_reason_id, edge["reason_ids"])

            reason = [
                row
                for row in reason_rows
                if row["reason_kind"] == "explicit_relation"
                and row["relation_id"] == relation_id
            ]
            self.assertEqual(len(reason), 1)
            self.assertEqual(reason[0]["verification_statuses"], "source_verified")
            self.assertEqual(reason[0]["source_work_id"], source_work_id)
            self.assertEqual(reason[0]["target_work_id"], target_work_id)


if __name__ == "__main__":
    unittest.main()
