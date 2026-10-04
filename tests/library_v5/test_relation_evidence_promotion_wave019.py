from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACT = "work-relation-iron-man-2-2010-iron-man-3-2013-sequel"
SOURCE = "marvel-iron-man-3-first-two-films-sequel-2013"
EVIDENCE = "evidence-iron-man-2-iron-man-3-sequel-marvel-2013"
REVIEW = "review-2026-10-04-iron-man-2-iron-man-3-sequel"


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave019Tests(unittest.TestCase):
    def test_iron_man_sequel_has_exact_provenance_without_tuple_rewrite(self) -> None:
        relation = next(r for r in rows("data/library/work_relations.csv") if r["work_relation_id"] == FACT)
        self.assertEqual(relation["verification_status"], "source_verified")
        self.assertEqual(tuple(relation[k] for k in (
            "source_work_id", "target_work_id", "relation_kind", "relation_scope",
            "directness", "continuity_scope", "certainty", "notes")),
            ("iron-man-2-2010", "iron-man-3-2013", "sequel", "story",
             "direct", "same_or_intended", "confirmed", "Iron Man trilogy direct franchise line."))
        source = [r for r in rows("data/library/sources.csv") if r["source_id"] == SOURCE]
        self.assertEqual(len(source), 1)
        self.assertEqual(source[0]["url"], "https://i.annihil.us/u/prod/avengersmovie/ironman3/fullsite1/pdf/Iron_Man_3_Notes.pdf")
        evidence = [r for r in rows("data/library/evidence.csv") if r["evidence_id"] == EVIDENCE]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(tuple(evidence[0][k] for k in ("fact_table", "fact_id", "source_id", "evidence_role")),
                         ("work_relations.csv", FACT, SOURCE, "primary"))
        review = [r for r in rows("data/content_audit/reviews.csv") if r["review_id"] == REVIEW]
        self.assertEqual(len(review), 1)
        self.assertEqual(tuple(review[0][k] for k in (
            "fact_table", "fact_id", "previous_verification_status", "new_verification_status", "review_action", "evidence_ids")),
            ("work_relations.csv", FACT, "legacy_seed", "source_verified", "verified_source", EVIDENCE))


if __name__ == "__main__":
    unittest.main()
