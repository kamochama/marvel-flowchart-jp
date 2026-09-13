from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"


RELATIONS = {
    "work-relation-captain-america-the-winter-soldier-2014-captain-america-civil-war-2016-sequel": (
        "captain-america-the-winter-soldier-2014", "captain-america-civil-war-2016",
        "disney-captain-america-civil-war-third-installment-2016",
        "evidence-captain-america-winter-soldier-civil-war-third-installment-disney-2016",
        "review-2026-09-14-winter-soldier-civil-war-sequel",
    ),
    "work-relation-thor-the-dark-world-2013-thor-ragnarok-2017-sequel": (
        "thor-the-dark-world-2013", "thor-ragnarok-2017",
        "disney-thor-ragnarok-third-installment-2017",
        "evidence-thor-dark-world-ragnarok-third-installment-disney-2017",
        "review-2026-09-14-thor-dark-world-ragnarok-sequel",
    ),
    "work-relation-thor-ragnarok-2017-thor-love-and-thunder-2022-sequel": (
        "thor-ragnarok-2017", "thor-love-and-thunder-2022",
        "marvel-thor-love-and-thunder-fourth-installment-2022",
        "evidence-thor-ragnarok-love-and-thunder-fourth-installment-marvel-2022",
        "review-2026-09-14-thor-ragnarok-love-and-thunder-sequel",
    ),
}

URLS = {
    "disney-captain-america-civil-war-third-installment-2016":
        "https://thewaltdisneycompany.com/news/brand-new-trailer-and-posters-released-for-marvels-captain-america-civil-war/",
    "disney-thor-ragnarok-third-installment-2017":
        "https://thewaltdisneycompany.com/app/uploads/2017-asm-transcript.pdf",
    "marvel-thor-love-and-thunder-fourth-installment-2022":
        "https://www.marvel.com/watch/trailers-and-extras/kevin-feige-says-thor-love-and-thunder-is-more-than-just-ragnarok-2",
}

DEFERRED = {
    "work-relation-iron-man-2-2010-iron-man-3-2013-sequel",
    "work-relation-spider-man-2-2004-spider-man-3-2007-sequel",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave012Tests(unittest.TestCase):
    def test_three_relations_have_exact_source_evidence_and_review_provenance(self) -> None:
        relations = {row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")}
        sources = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")

        for source_id, url in URLS.items():
            self.assertEqual(sources[source_id]["url"], url)

        for relation_id, (source_work, target_work, source_id, evidence_id, review_id) in RELATIONS.items():
            row = relations[relation_id]
            self.assertEqual(row["verification_status"], "source_verified")
            self.assertEqual(
                (row["source_work_id"], row["target_work_id"], row["relation_kind"],
                 row["relation_scope"], row["directness"], row["continuity_scope"],
                 row["certainty"]),
                (source_work, target_work, "sequel", "story", "direct", "same_or_intended", "confirmed"),
            )
            matching_evidence = [item for item in evidence if item["evidence_id"] == evidence_id]
            self.assertEqual(len(matching_evidence), 1)
            self.assertEqual(
                (matching_evidence[0]["fact_table"], matching_evidence[0]["fact_id"],
                 matching_evidence[0]["source_id"], matching_evidence[0]["evidence_role"]),
                ("work_relations.csv", relation_id, source_id, "primary"),
            )
            matching_reviews = [item for item in reviews if item["review_id"] == review_id]
            self.assertEqual(len(matching_reviews), 1)
            self.assertEqual(
                (matching_reviews[0]["fact_table"], matching_reviews[0]["fact_id"],
                 matching_reviews[0]["previous_verification_status"],
                 matching_reviews[0]["new_verification_status"],
                 matching_reviews[0]["review_action"], matching_reviews[0]["evidence_ids"]),
                ("work_relations.csv", relation_id, "legacy_seed", "source_verified",
                 "verified_source", evidence_id),
            )

        for relation_id in DEFERRED:
            self.assertEqual(relations[relation_id]["verification_status"], "legacy_seed")

    def test_existing_pairs_and_reason_ids_are_preserved(self) -> None:
        edges = rows(DERIVED / "work_edges_all.csv")
        reasons = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual((len(edges), len(reasons)), (355, 562))
        for relation_id, (source_work, target_work, *_rest) in RELATIONS.items():
            edge = next(item for item in edges
                        if item["source_work_id"] == source_work
                        and item["target_work_id"] == target_work)
            expected_reason_id = f"reason-{source_work}-{target_work}-explicit-relation-{relation_id}"
            self.assertIn(expected_reason_id, edge["reason_ids"])
            matching_reasons = [item for item in reasons
                                if item["reason_kind"] == "explicit_relation"
                                and item["relation_id"] == relation_id]
            self.assertEqual(len(matching_reasons), 1)
            self.assertEqual(
                (matching_reasons[0]["verification_statuses"],
                 matching_reasons[0]["source_work_id"], matching_reasons[0]["target_work_id"]),
                ("source_verified", source_work, target_work),
            )


if __name__ == "__main__":
    unittest.main()
