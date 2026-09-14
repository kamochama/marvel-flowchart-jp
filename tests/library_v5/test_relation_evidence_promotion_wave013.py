from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATION_ID = (
    "work-relation-daredevil-born-again-s2-2026-"
    "daredevil-born-again-s3-tba-sequel"
)
SOURCE_ID = "disney-daredevil-born-again-s3-in-works-2025"
EVIDENCE_ID = "evidence-daredevil-born-again-s2-s3-sequel-disney-2025"
REVIEW_ID = "review-2026-09-14-daredevil-born-again-s2-s3-sequel"
SOURCE_URL = (
    "https://press.disney.co.uk/news/"
    "marvel-television-and-marvel-animation-new-york-comic-con-panel-"
    "gives-a-first-look-at-upcoming-disney%2B-slate-with-exclusive-"
    "footage-and-surprise-guests"
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave013Tests(unittest.TestCase):
    def test_daredevil_s2_s3_has_exact_provenance(self) -> None:
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
                "daredevil-born-again-s2-2026", "daredevil-born-again-s3-tba",
                "sequel", "story", "direct", "same_or_intended", "confirmed",
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

    def test_wave013_preserves_graph_shape_and_other_deferred_relations(self) -> None:
        relations = {row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")}
        self.assertEqual(relations[RELATION_ID]["verification_status"], "source_verified")
        for relation_id in (
            "work-relation-spider-man-2-2004-spider-man-3-2007-sequel",
            "work-relation-iron-man-2-2010-iron-man-3-2013-sequel",
            "work-relation-x-men-2000-x2-x-men-united-2003-sequel",
            "work-relation-blade-1998-1998-blade-ii-2002-sequel",
            "work-relation-fantastic-four-2005-fantastic-four-rise-of-the-silver-surfer-2007-sequel",
        ):
            self.assertEqual(relations[relation_id]["verification_status"], "legacy_seed")

        edges = rows(DERIVED / "work_edges_all.csv")
        reasons = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual((len(edges), len(reasons)), (355, 562))


if __name__ == "__main__":
    unittest.main()
