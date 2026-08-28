from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
REVIEWS = ROOT / "data" / "content_audit" / "reviews.csv"
PROXY_RELATION = "work-relation-venom-let-there-be-carnage-2021-spider-man-no-way-home-2021-crossover"
REVIEW_ID = "review-2026-08-28-venom-nwh-proxy-relation-retired"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class VenomProxyRetirementTests(unittest.TestCase):
    def test_proxy_relation_is_superseded_with_review_history_after_parity(self) -> None:
        relations = {row["work_relation_id"]: row for row in _rows(LIB / "work_relations.csv")}
        reviews = {row["review_id"]: row for row in _rows(REVIEWS)}

        self.assertEqual(relations[PROXY_RELATION]["verification_status"], "superseded")
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "work_relations.csv")
        self.assertEqual(review["fact_id"], PROXY_RELATION)
        self.assertEqual(review["previous_verification_status"], "source_verified")
        self.assertEqual(review["new_verification_status"], "superseded")
        self.assertEqual(review["review_action"], "superseded_proxy")
        self.assertIn("evidence-venom-arrival-transition-film-2021", review["evidence_ids"])
        self.assertIn("evidence-venom-return-transition-film-2021", review["evidence_ids"])


if __name__ == "__main__":
    unittest.main()
