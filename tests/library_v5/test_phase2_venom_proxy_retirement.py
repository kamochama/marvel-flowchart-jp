from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
REVIEWS = ROOT / "data" / "content_audit" / "reviews.csv"
PROXY_RELATION = "work-relation-venom-let-there-be-carnage-2021-spider-man-no-way-home-2021-crossover"
REVIEW_ID = "review-2026-08-28-venom-nwh-proxy-relation-retired"

CREATED_REVIEW_FACTS = {
    "review-2026-08-28-venom-eddie-ltbc-appearance": ("appearances.csv", "appearance-venom-let-there-be-carnage-2021-entity-eddie-brock-sony"),
    "review-2026-08-28-venom-eddie-nwh-appearance": ("appearances.csv", "appearance-spider-man-no-way-home-2021-entity-eddie-brock-sony"),
    "review-2026-08-28-venom-arrival-event": ("events.csv", "event-ltbc-eddie-brock-earth616-arrival"),
    "review-2026-08-28-venom-return-event": ("events.csv", "event-nwh-eddie-brock-ssu-return"),
    "review-2026-08-28-venom-arrival-occurrence": ("event_occurrences.csv", "event-occurrence-ltbc-eddie-brock-earth616-arrival"),
    "review-2026-08-28-venom-return-occurrence": ("event_occurrences.csv", "event-occurrence-nwh-eddie-brock-ssu-return"),
    "review-2026-08-28-venom-arrival-transition": ("multiverse_transitions.csv", "event-ltbc-eddie-brock-earth616-arrival"),
    "review-2026-08-28-venom-return-transition": ("multiverse_transitions.csv", "event-nwh-eddie-brock-ssu-return"),
    "review-2026-08-28-venom-arrival-participant": ("transition_participants.csv", "transition-participant-ltbc-eddie-brock"),
    "review-2026-08-28-venom-return-participant": ("transition_participants.csv", "transition-participant-nwh-eddie-brock-return"),
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class VenomProxyRetirementTests(unittest.TestCase):
    def test_created_verified_facts_have_review_history(self) -> None:
        reviews = {row["review_id"]: row for row in _rows(REVIEWS)}
        for review_id, (fact_table, fact_id) in CREATED_REVIEW_FACTS.items():
            review = reviews[review_id]
            self.assertEqual(review["fact_table"], fact_table)
            self.assertEqual(review["fact_id"], fact_id)
            self.assertEqual(review["previous_verification_status"], "")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "created_verified")
            self.assertTrue(review["evidence_ids"])

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
