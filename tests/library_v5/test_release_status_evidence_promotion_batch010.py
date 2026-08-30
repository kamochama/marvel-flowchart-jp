import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "production-status-the-fantastic-four-first-steps-2025-snapshot-2026-08-28": "ff-doomsday",
    "production-status-daredevil-born-again-s3-tba-snapshot-2026-08-28": "tv",
    "production-status-your-friendly-neighborhood-spider-man-s2-2026-snapshot-2026-08-28": "tv",
}


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch010Tests(unittest.TestCase):
    def test_statuses_are_verified_without_changing_snapshot_meaning(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        self.assertEqual(statuses[next(iter(TARGETS))]["status"], "released")
        for target in TARGETS:
            status = statuses[target]
            self.assertEqual(status["asserted_at"], "2026-08-28")
            self.assertEqual(status["certainty"], "confirmed")
            self.assertEqual(status["verification_status"], "source_verified")
            self.assertNotIn("legacy seed", status["notes"])
        self.assertIn("in theaters", statuses[next(iter(TARGETS))]["notes"].lower())
        self.assertIn("listing", statuses["production-status-daredevil-born-again-s3-tba-snapshot-2026-08-28"]["notes"].lower())
        self.assertIn("listing", statuses["production-status-your-friendly-neighborhood-spider-man-s2-2026-snapshot-2026-08-28"]["notes"].lower())

    def test_exact_primary_evidence_and_review_exist_for_each_status(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        for fact_id, source_id in TARGETS.items():
            evidence_id = f"evidence-{fact_id}"
            ev = evidence[evidence_id]
            self.assertEqual(ev["fact_table"], "production_status_assertions.csv")
            self.assertEqual(ev["fact_id"], fact_id)
            self.assertEqual(ev["source_id"], source_id)
            self.assertEqual(ev["evidence_role"], "primary")
            self.assertEqual(ev["verified_at"], "2026-08-30")
            review = reviews[f"review-2026-08-30-{fact_id}"]
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], evidence_id)

    def test_release_rows_and_graph_scope_remain_unchanged(self):
        releases = _rows("data/library/releases.csv")
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in releases), 14)
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in _rows("data/library/production_status_assertions.csv")), 13)


if __name__ == "__main__":
    unittest.main()

