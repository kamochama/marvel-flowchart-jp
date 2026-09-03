from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATIONS = {
    "work-relation-avengers-endgame-2019-spider-man-far-from-home-2019-aftermath": (
        "avengers-endgame-2019", "spider-man-far-from-home-2019",
        "marvel-spider-man-far-from-home-endgame-aftermath-2019",
        "evidence-endgame-far-from-home-aftermath-marvel-2019",
        "review-2026-09-04-endgame-far-from-home-aftermath",
        "aftermath", "story", "direct", "same_or_intended", "probable",
    ),
    "work-relation-wandavision-2021-doctor-strange-in-the-multiverse-of-madness-2022-story-link": (
        "wandavision-2021", "doctor-strange-in-the-multiverse-of-madness-2022",
        "marvel-wandavision-mom-direct-connection-2019",
        "evidence-wandavision-mom-direct-connection-marvel-2019",
        "review-2026-09-04-wandavision-mom-story-link",
        "story_link", "story", "indirect", "same_or_intended", "probable",
    ),
    "work-relation-ant-man-2015-ant-man-and-the-wasp-2018-sequel": (
        "ant-man-2015", "ant-man-and-the-wasp-2018",
        "marvel-ant-man-ant-man-wasp-sequel-2017",
        "evidence-ant-man-ant-man-wasp-sequel-marvel-2017",
        "review-2026-09-04-ant-man-ant-man-wasp-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-x-men-first-class-2011-x-men-days-of-future-past-2014-crossover": (
        "x-men-first-class-2011", "x-men-days-of-future-past-2014",
        "twentieth-xmen-first-class-days-crossover-2014",
        "evidence-xmen-first-class-days-crossover-twentieth-2014",
        "review-2026-09-04-xmen-first-class-days-crossover",
        "crossover", "crossover", "strong", "same_or_intended", "probable",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave009Tests(unittest.TestCase):
    def test_four_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relations = {row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")}
        sources = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "marvel-spider-man-far-from-home-endgame-aftermath-2019":
                "https://www.marvel.com/movies/spider-man-far-from-home",
            "marvel-wandavision-mom-direct-connection-2019":
                "https://www.marvel.com/articles/movies/sdcc-2019-marvel-studios-doctor-strange-in-the-multi-verse-of-Madness-announced",
            "marvel-ant-man-ant-man-wasp-sequel-2017":
                "https://www.marvel.com/articles/movies/marvel-studios-ant-man-and-the-wasp-begins-production",
            "twentieth-xmen-first-class-days-crossover-2014":
                "https://www.20thcenturystudios.com/movies/x-men-days-of-future-past",
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
