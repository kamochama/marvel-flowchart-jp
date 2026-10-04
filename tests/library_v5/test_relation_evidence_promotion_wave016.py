from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELATION = "work-relation-the-defenders-2017-luke-cage-s2-2018-story-link"
SOURCE = "marvel-luke-cage-s2-defenders-return-2016"
EVIDENCE = "evidence-defenders-luke-cage-s2-story-link-marvel-2016"
REVIEW = "review-2026-10-04-defenders-luke-cage-s2-story-link"
URL = "https://www.marvel.com/articles/tv-shows/marvel-s-luke-cage-moves-always-forward-with-season-2"


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave016Tests(unittest.TestCase):
    def test_defenders_luke_cage_s2_preserves_tuple_with_exact_provenance(self) -> None:
        relation = next(r for r in rows("data/library/work_relations.csv") if r["work_relation_id"] == RELATION)
        self.assertEqual(
            tuple(relation[key] for key in (
                "source_work_id", "target_work_id", "relation_kind", "relation_scope",
                "directness", "continuity_scope", "certainty", "verification_status",
            )),
            ("the-defenders-2017", "luke-cage-s2-2018", "story_link", "story",
             "strong", "same_or_intended", "probable", "source_verified"),
        )
        sources = [r for r in rows("data/library/sources.csv") if r["source_id"] == SOURCE]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["url"], URL)
        evidence = [r for r in rows("data/library/evidence.csv") if r["evidence_id"] == EVIDENCE]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(tuple(evidence[0][key] for key in ("fact_table", "fact_id", "source_id", "evidence_role")),
                         ("work_relations.csv", RELATION, SOURCE, "primary"))
        reviews = [r for r in rows("data/content_audit/reviews.csv") if r["review_id"] == REVIEW]
        self.assertEqual(len(reviews), 1)
        self.assertEqual(tuple(reviews[0][key] for key in (
            "fact_table", "fact_id", "previous_verification_status", "new_verification_status", "review_action", "evidence_ids",
        )), ("work_relations.csv", RELATION, "legacy_seed", "source_verified", "verified_source", EVIDENCE))


if __name__ == "__main__":
    unittest.main()
