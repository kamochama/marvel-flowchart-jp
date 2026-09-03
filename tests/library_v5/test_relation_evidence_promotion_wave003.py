from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"


RELATIONS = {
    "work-relation-the-avengers-2012-avengers-age-of-ultron-2015-sequel": (
        "the-avengers-2012",
        "avengers-age-of-ultron-2015",
        "disney-avengers-age-of-ultron-sequel-2015",
        "evidence-avengers-age-of-ultron-sequel-disney-2015",
        "review-2026-09-03-avengers-age-of-ultron-sequel",
        "probable",
    ),
    "work-relation-captain-america-the-first-avenger-2011-captain-america-the-winter-soldier-2014-sequel": (
        "captain-america-the-first-avenger-2011",
        "captain-america-the-winter-soldier-2014",
        "disney-captain-america-winter-soldier-sequel-2013",
        "evidence-captain-america-winter-soldier-sequel-disney-2013",
        "review-2026-09-03-captain-america-winter-soldier-sequel",
        "confirmed",
    ),
    "work-relation-thor-2011-thor-the-dark-world-2013-sequel": (
        "thor-2011",
        "thor-the-dark-world-2013",
        "disney-thor-dark-world-sequel-2013",
        "evidence-thor-dark-world-sequel-disney-2013",
        "review-2026-09-03-thor-dark-world-sequel",
        "confirmed",
    ),
    "work-relation-guardians-of-the-galaxy-2014-guardians-of-the-galaxy-vol-2-2017-sequel": (
        "guardians-of-the-galaxy-2014",
        "guardians-of-the-galaxy-vol-2-2017",
        "marvel-guardians-vol2-sequel-2017",
        "evidence-guardians-vol2-sequel-marvel-2017",
        "review-2026-09-03-guardians-vol2-sequel",
        "confirmed",
    ),
    "work-relation-black-panther-2018-black-panther-wakanda-forever-2022-sequel": (
        "black-panther-2018",
        "black-panther-wakanda-forever-2022",
        "marvel-black-panther-wakanda-forever-sequel-2022",
        "evidence-black-panther-wakanda-forever-sequel-marvel-2022",
        "review-2026-09-03-black-panther-wakanda-forever-sequel",
        "confirmed",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave003Tests(unittest.TestCase):
    def test_five_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relation_rows = {
            row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")
        }
        source_rows = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence_rows = rows(LIB / "evidence.csv")
        review_rows = rows(AUDIT / "reviews.csv")

        source_urls = {
            "disney-avengers-age-of-ultron-sequel-2015": "https://thewaltdisneycompany.com/app/uploads/ir/2015/events/tos-baml-2015-0910-transcript.pdf",
            "disney-captain-america-winter-soldier-sequel-2013": "https://thewaltdisneycompany.com/app/uploads/ir/2013/annual/2013-asm-transcript.pdf",
            "disney-thor-dark-world-sequel-2013": "https://thewaltdisneycompany.com/app/uploads/ir/2013/events/jar-ml-20130912.pdf",
            "marvel-guardians-vol2-sequel-2017": "https://www.marvel.com/articles/movies/marvel-studios-guardians-of-the-galaxy-vol-2-takes-1-at-the-box-office",
            "marvel-black-panther-wakanda-forever-sequel-2022": "https://www.marvel.com/articles/movies/black-panther-wakanda-forever-title?linkId=117963860",
        }
        for source_id, url in source_urls.items():
            self.assertEqual(source_rows[source_id]["url"], url)

        for relation_id, (
            source_work_id,
            target_work_id,
            source_id,
            evidence_id,
            review_id,
            certainty,
        ) in RELATIONS.items():
            relation = relation_rows[relation_id]
            self.assertEqual(relation["verification_status"], "source_verified")
            self.assertEqual(relation["source_work_id"], source_work_id)
            self.assertEqual(relation["target_work_id"], target_work_id)
            self.assertEqual(relation["relation_kind"], "sequel")
            self.assertEqual(relation["directness"], "direct")
            self.assertEqual(relation["certainty"], certainty)

            evidence = [row for row in evidence_rows if row["evidence_id"] == evidence_id]
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["fact_table"], "work_relations.csv")
            self.assertEqual(evidence[0]["fact_id"], relation_id)
            self.assertEqual(evidence[0]["source_id"], source_id)
            self.assertEqual(evidence[0]["evidence_role"], "primary")

            review = [row for row in review_rows if row["review_id"] == review_id]
            self.assertEqual(len(review), 1)
            self.assertEqual(review[0]["fact_table"], "work_relations.csv")
            self.assertEqual(review[0]["fact_id"], relation_id)
            self.assertEqual(review[0]["previous_verification_status"], "legacy_seed")
            self.assertEqual(review[0]["new_verification_status"], "source_verified")
            self.assertEqual(review[0]["review_action"], "verified_source")
            self.assertEqual(review[0]["evidence_ids"], evidence_id)

    def test_existing_pairs_and_explicit_reason_ids_are_preserved(self) -> None:
        edge_rows = rows(DERIVED / "work_edges_all.csv")
        reason_rows = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual(len(edge_rows), 355)
        self.assertEqual(len(reason_rows), 562)

        for relation_id, (source_work_id, target_work_id, *_rest) in RELATIONS.items():
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
