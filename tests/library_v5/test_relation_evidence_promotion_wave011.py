from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"


RELATIONS = {
    "work-relation-venom-2018-venom-let-there-be-carnage-2021-sequel": (
        "venom-2018", "venom-let-there-be-carnage-2021",
        "sony-venom-ltbc-sequel-2021",
        "evidence-venom-ltbc-sequel-sony-2021",
        "review-2026-09-14-venom-ltbc-sequel",
        "sequel", "story", "direct", "same_or_intended", "probable",
    ),
    "work-relation-your-friendly-neighborhood-spider-man-s1-2025-your-friendly-neighborhood-spider-man-s2-2026-sequel": (
        "your-friendly-neighborhood-spider-man-s1-2025", "your-friendly-neighborhood-spider-man-s2-2026",
        "disney-yfnsm-s1-s2-continuation-2025",
        "evidence-yfnsm-s1-s2-continuation-disney-2025",
        "review-2026-09-14-yfnsm-s1-s2-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-ant-man-and-the-wasp-2018-ant-man-and-the-wasp-quantumania-2023-sequel": (
        "ant-man-and-the-wasp-2018", "ant-man-and-the-wasp-quantumania-2023",
        "marvel-antman-quantumania-third-film-2021",
        "evidence-antman-quantumania-third-film-marvel-2021",
        "review-2026-09-14-antman-quantumania-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-spider-man-2002-spider-man-2-2004-sequel": (
        "spider-man-2002", "spider-man-2-2004",
        "sony-spider-man-2-latest-installment-2004",
        "evidence-spider-man-2-latest-installment-sony-2004",
        "review-2026-09-14-spider-man-2-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-luke-cage-s1-2016-luke-cage-s2-2018-sequel": (
        "luke-cage-s1-2016", "luke-cage-s2-2018",
        "marvel-luke-cage-s1-s2-continuation-2018",
        "evidence-luke-cage-s1-s2-continuation-marvel-2018",
        "review-2026-09-14-luke-cage-s1-s2-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
}

DEFERRED = "work-relation-spider-man-2-2004-spider-man-3-2007-sequel"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave011Tests(unittest.TestCase):
    def test_five_relations_have_exact_source_evidence_and_review_provenance(self) -> None:
        relations = {row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")}
        sources = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "sony-venom-ltbc-sequel-2021":
                "https://www.sonypictures.com/corp/press_releases/2021/0728",
            "marvel-antman-quantumania-third-film-2021":
                "https://www.marvel.com/articles/tv-shows/loki-assembled-jonathan-majors-he-who-remains?linkId=124934704",
            "sony-spider-man-2-latest-installment-2004":
                "https://www.sonypictures.com/movies/spiderman2",
            "marvel-luke-cage-s1-s2-continuation-2018":
                "https://www.marvel.com/articles/tv-shows/marvel-s-luke-cage-season-2-debuts-june-22-on-netflix/",
            "disney-yfnsm-s1-s2-continuation-2025":
                "https://thewaltdisneycompany.com/news/your-friendly-neighborhood-spider-man/",
        }
        for source_id, url in urls.items():
            self.assertEqual(sources[source_id]["url"], url)

        for relation_id, (source_work, target_work, source_id, evidence_id, review_id,
                          relation_kind, relation_scope, directness, continuity_scope,
                          certainty) in RELATIONS.items():
            row = relations[relation_id]
            self.assertEqual(row["verification_status"], "source_verified")
            self.assertEqual(
                (row["source_work_id"], row["target_work_id"], row["relation_kind"],
                 row["relation_scope"], row["directness"], row["continuity_scope"],
                 row["certainty"]),
                (source_work, target_work, relation_kind, relation_scope, directness,
                 continuity_scope, certainty),
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

        self.assertEqual(relations[DEFERRED]["verification_status"], "legacy_seed")

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
