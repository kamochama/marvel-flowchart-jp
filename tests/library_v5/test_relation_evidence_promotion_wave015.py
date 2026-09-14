from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"

RELATION_ID = "work-relation-the-defenders-2017-daredevil-s3-2018-aftermath"
SOURCE_ID = "marvel-daredevil-s3-defenders-aftermath-2018"
EVIDENCE_ID = "evidence-defenders-daredevil-s3-aftermath-marvel-2018"
REVIEW_ID = "review-2026-09-14-defenders-daredevil-s3-aftermath"
SOURCE_URL = "https://www.marvel.com/amp/articles/tv-shows/marvel-daredevil-season-3-creating-the-look"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave015Tests(unittest.TestCase):
    def test_defenders_daredevil_s3_has_exact_provenance(self) -> None:
        relations = {row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")}
        sources = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")

        self.assertEqual(sources[SOURCE_ID]["url"], SOURCE_URL)
        relation = relations[RELATION_ID]
        self.assertEqual(
            (
                relation["source_work_id"], relation["target_work_id"],
                relation["relation_kind"], relation["relation_scope"],
                relation["directness"], relation["continuity_scope"],
                relation["certainty"], relation["verification_status"],
            ),
            (
                "the-defenders-2017", "daredevil-s3-2018",
                "aftermath", "story", "strong", "same_or_intended", "probable",
                "source_verified",
            ),
        )

        matching_evidence = [item for item in evidence if item["evidence_id"] == EVIDENCE_ID]
        self.assertEqual(len(matching_evidence), 1)
        self.assertEqual(
            (
                matching_evidence[0]["fact_table"], matching_evidence[0]["fact_id"],
                matching_evidence[0]["source_id"], matching_evidence[0]["evidence_role"],
            ),
            ("work_relations.csv", RELATION_ID, SOURCE_ID, "primary"),
        )

        matching_reviews = [item for item in reviews if item["review_id"] == REVIEW_ID]
        self.assertEqual(len(matching_reviews), 1)
        self.assertEqual(
            (
                matching_reviews[0]["fact_table"], matching_reviews[0]["fact_id"],
                matching_reviews[0]["previous_verification_status"],
                matching_reviews[0]["new_verification_status"],
                matching_reviews[0]["review_action"], matching_reviews[0]["evidence_ids"],
            ),
            (
                "work_relations.csv", RELATION_ID, "legacy_seed", "source_verified",
                "verified_source", EVIDENCE_ID,
            ),
        )


if __name__ == "__main__":
    unittest.main()
