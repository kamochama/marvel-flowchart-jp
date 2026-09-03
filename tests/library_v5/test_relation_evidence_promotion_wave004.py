from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"


RELATIONS = {
    "work-relation-hawkeye-2021-echo-2024-spinoff": (
        "hawkeye-2021",
        "echo-2024",
        "disney-echo-hawkeye-spinoff-2024",
        "evidence-echo-hawkeye-spinoff-disney-2024",
        "review-2026-09-03-echo-hawkeye-spinoff",
        "spinoff",
        "strong",
        "probable",
    ),
    "work-relation-daredevil-born-again-s1-2025-daredevil-born-again-s2-2026-sequel": (
        "daredevil-born-again-s1-2025",
        "daredevil-born-again-s2-2026",
        "disney-daredevil-born-again-s2-continuation-2025",
        "evidence-daredevil-born-again-s1-s2-sequel-disney-2025",
        "review-2026-09-03-daredevil-born-again-s1-s2-sequel",
        "sequel",
        "direct",
        "confirmed",
    ),
    "work-relation-daredevil-born-again-s2-2026-the-punisher-one-last-kill-2026-05-12-crossover": (
        "daredevil-born-again-s2-2026",
        "the-punisher-one-last-kill-2026-05-12",
        "disneyplus-daredevil-born-again-s2-punisher-crossover-2026",
        "evidence-daredevil-s2-punisher-one-last-kill-crossover-disneyplus-2026",
        "review-2026-09-03-daredevil-s2-punisher-one-last-kill-crossover",
        "crossover",
        "indirect",
        "probable",
    ),
    "work-relation-the-punisher-s1-2017-the-punisher-s2-2019-sequel": (
        "the-punisher-s1-2017",
        "the-punisher-s2-2019",
        "marvel-punisher-s2-renewal-2017",
        "evidence-punisher-s1-s2-sequel-marvel-2017",
        "review-2026-09-03-punisher-s1-s2-sequel",
        "sequel",
        "direct",
        "confirmed",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave004Tests(unittest.TestCase):
    def test_four_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relation_rows = {
            row["work_relation_id"]: row for row in rows(LIB / "work_relations.csv")
        }
        source_rows = {row["source_id"]: row for row in rows(LIB / "sources.csv")}
        evidence_rows = rows(LIB / "evidence.csv")
        review_rows = rows(AUDIT / "reviews.csv")

        source_urls = {
            "disney-echo-hawkeye-spinoff-2024": "https://thewaltdisneycompany.com/news/inside-echo-marvel-studios-gritty-and-grounded-new-series/",
            "disney-daredevil-born-again-s2-continuation-2025": "https://thewaltdisneycompany.com/news/daredevil-born-again-season-2/",
            "disneyplus-daredevil-born-again-s2-punisher-crossover-2026": "https://www.disneyplus.com/explore/articles/daredevil-born-again-season-2",
            "marvel-punisher-s2-renewal-2017": "https://www.marvel.com/articles/tv-shows/marvels-the-punisher-returning-for-season-2",
        }
        for source_id, url in source_urls.items():
            self.assertEqual(source_rows[source_id]["url"], url)

        for relation_id, (
            source_work_id,
            target_work_id,
            source_id,
            evidence_id,
            review_id,
            relation_kind,
            directness,
            certainty,
        ) in RELATIONS.items():
            relation = relation_rows[relation_id]
            self.assertEqual(relation["verification_status"], "source_verified")
            self.assertEqual(relation["source_work_id"], source_work_id)
            self.assertEqual(relation["target_work_id"], target_work_id)
            self.assertEqual(relation["relation_kind"], relation_kind)
            self.assertEqual(relation["directness"], directness)
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
