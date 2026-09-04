from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATIONS = {
    "work-relation-avengers-age-of-ultron-2015-captain-america-civil-war-2016-aftermath": (
        "avengers-age-of-ultron-2015", "captain-america-civil-war-2016",
        "marvel-age-of-ultron-civil-war-aftermath-2018",
        "evidence-age-of-ultron-civil-war-aftermath-marvel-2018",
        "review-2026-09-04-age-of-ultron-civil-war-aftermath",
        "aftermath", "story", "indirect", "same_or_intended", "probable",
    ),
    "work-relation-thor-ragnarok-2017-avengers-infinity-war-2018-crossover": (
        "thor-ragnarok-2017", "avengers-infinity-war-2018",
        "marvel-thor-ragnarok-infinity-war-loki-2021",
        "evidence-thor-ragnarok-infinity-war-crossover-marvel-2021",
        "review-2026-09-04-thor-ragnarok-infinity-war-crossover",
        "crossover", "crossover", "direct", "same_or_intended", "probable",
    ),
    "work-relation-captain-america-civil-war-2016-ant-man-and-the-wasp-2018-aftermath": (
        "captain-america-civil-war-2016", "ant-man-and-the-wasp-2018",
        "marvel-ant-man-wasp-civil-war-aftermath-2018",
        "evidence-civil-war-ant-man-wasp-aftermath-marvel-2018",
        "review-2026-09-04-civil-war-ant-man-wasp-aftermath",
        "aftermath", "story", "indirect", "same_or_intended", "probable",
    ),
    "work-relation-ms-marvel-2022-the-marvels-2023-story-link": (
        "ms-marvel-2022", "the-marvels-2023",
        "disney-marvels-ms-marvel-kamala-2023",
        "evidence-ms-marvel-the-marvels-story-link-disney-2023",
        "review-2026-09-04-ms-marvel-the-marvels-story-link",
        "story_link", "story", "strong", "same_or_intended", "probable",
    ),
    "work-relation-what-if-s2-2023-what-if-s3-2024-sequel": (
        "what-if-s2-2023", "what-if-s3-2024",
        "marvel-what-if-s2-s3-continuation-2022",
        "evidence-what-if-s2-s3-continuation-marvel-2022",
        "review-2026-09-04-what-if-s2-s3-sequel",
        "sequel", "story", "strong", "same_or_intended", "probable",
    ),
    "work-relation-iron-man-3-2013-all-hail-the-king-2014-sequel": (
        "iron-man-3-2013", "all-hail-the-king-2014",
        "disney-iron-man-3-all-hail-the-king-followup-2014",
        "evidence-iron-man-3-all-hail-the-king-followup-disney-2014",
        "review-2026-09-04-iron-man-3-all-hail-the-king-sequel",
        "sequel", "story", "indirect", "same_or_intended", "probable",
    ),
    "work-relation-the-avengers-2012-item-47-2012-sequel": (
        "the-avengers-2012", "item-47-2012",
        "disney-avengers-item-47-aftermath-2012",
        "evidence-avengers-item-47-aftermath-disney-2012",
        "review-2026-09-04-avengers-item-47-sequel",
        "sequel", "story", "direct", "same_or_intended", "probable",
    ),
    "work-relation-jessica-jones-s1-2015-jessica-jones-s2-2018-sequel": (
        "jessica-jones-s1-2015", "jessica-jones-s2-2018",
        "marvel-jessica-jones-s1-s2-continuation-2017",
        "evidence-jessica-jones-s1-s2-continuation-marvel-2017",
        "review-2026-09-04-jessica-jones-s1-s2-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-jessica-jones-s2-2018-jessica-jones-s3-2019-sequel": (
        "jessica-jones-s2-2018", "jessica-jones-s3-2019",
        "marvel-jessica-jones-s2-s3-continuation-2018",
        "evidence-jessica-jones-s2-s3-sequel-marvel-2018",
        "review-2026-09-04-jessica-jones-s2-s3-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-iron-fist-s1-2017-iron-fist-s2-2018-sequel": (
        "iron-fist-s1-2017", "iron-fist-s2-2018",
        "marvel-iron-fist-s1-s2-continuation-2018",
        "evidence-iron-fist-s1-s2-sequel-marvel-2018",
        "review-2026-09-04-iron-fist-s1-s2-sequel",
        "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-cloak-dagger-20182019-runaways-20172019-crossover": (
        "cloak-dagger-20182019", "runaways-20172019",
        "marvel-cloak-dagger-runaways-crossover-2019",
        "evidence-cloak-dagger-runaways-crossover-marvel-2019",
        "review-2026-09-04-cloak-dagger-runaways-crossover",
        "crossover", "crossover", "direct", "uncertain_legacy_tv", "probable",
    ),
}

DEFERRED = "work-relation-x-men-days-of-future-past-2014-x-men-apocalypse-2016-sequel"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave010Tests(unittest.TestCase):
    def test_eleven_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relations = {row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")}
        sources = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "marvel-age-of-ultron-civil-war-aftermath-2018":
                "https://www.marvel.com/amp/articles/movies/the-essential-marvel-cinematic-universe-guide-phase-three",
            "marvel-thor-ragnarok-infinity-war-loki-2021":
                "https://www.marvel.com/articles/tv-shows/tom-hiddleston-decade-god-of-mischief-loki-mcu",
            "marvel-ant-man-wasp-civil-war-aftermath-2018":
                "https://www.marvel.com/movies/ant-man-and-the-wasp",
            "disney-marvels-ms-marvel-kamala-2023":
                "https://thewaltdisneycompany.com/news/the-marvels-director-nia-dacosta-on-crafting-a-cosmic-team-up-of-epic-proportions/",
            "marvel-what-if-s2-s3-continuation-2022":
                "https://www.marvel.com/articles/tv-shows/sdcc-2022-marvel-studios-animation-panel",
            "disney-iron-man-3-all-hail-the-king-followup-2014":
                "https://www.disneyplus.com/browse/entity-14988369-345c-4984-9c16-59428bd70609",
            "disney-avengers-item-47-aftermath-2012":
                "https://www.disneyplus.com/browse/entity-2cd46937-17fe-4ada-8de4-0972f2763f1c",
            "marvel-jessica-jones-s1-s2-continuation-2017":
                "https://www.marvel.com/amp/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-critically-acclaimed-marvel-s-jessica-jones",
            "marvel-jessica-jones-s2-s3-continuation-2018":
                "https://www.marvel.com/articles/tv-shows/marvel-s-jessica-jones-renewed-for-season-3",
            "marvel-iron-fist-s1-s2-continuation-2018":
                "https://www.marvel.com/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-marvel-s-iron-fist?EML=072018_SDCC_Season2&cid=SDCC18&mi_u=2417338",
            "marvel-cloak-dagger-runaways-crossover-2019":
                "https://www.marvel.com/articles/tv-shows/first-look-runaways-meet-cloak-and-dagger?linkId=78522422",
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
