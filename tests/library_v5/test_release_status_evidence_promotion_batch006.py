import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "production-status-visionquest-2026-10-14-snapshot-2026-08-28"
RELEASE_TARGET = "release-visionquest-2026-10-14-primary"
EVIDENCE_ID = "evidence-production-status-visionquest-2026-10-14-snapshot-2026-08-28"
REVIEW_ID = "review-2026-08-30-production-status-visionquest-2026-10-14-snapshot-2026-08-28"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch006Tests(unittest.TestCase):
    def test_visionquest_status_is_source_verified_without_semantic_drift(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        status = statuses[TARGET]
        self.assertEqual(status["work_id"], "visionquest-2026-10-14")
        self.assertEqual(status["status"], "announced")
        self.assertEqual(status["asserted_at"], "2026-08-28")
        self.assertEqual(status["certainty"], "confirmed")
        self.assertEqual(status["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", status["notes"])
        self.assertIn("2026-10-14", status["notes"])
        self.assertIn("Disney+", status["notes"])

    def test_status_has_exact_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "production_status_assertions.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "visionquest")
        self.assertEqual(ev["evidence_role"], "primary")
        self.assertEqual(ev["verified_at"], "2026-08-30")
        self.assertIn("2026-10-14", ev["quoted_or_paraphrased_note"])
        self.assertIn("Disney+", ev["quoted_or_paraphrased_note"])
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "production_status_assertions.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_release_territory_and_graph_scope_remain_unchanged(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        release = releases[RELEASE_TARGET]
        self.assertEqual(release["territory"], "unknown")
        self.assertEqual(release["release_kind"], "streaming")
        self.assertEqual(release["release_date"], "2026-10-14")
        self.assertEqual(release["status"], "announced")
        self.assertEqual(release["verification_status"], "source_verified")
        promoted_statuses = {
            row["production_status_assertion_id"]
            for row in _rows("data/library/production_status_assertions.csv")
            if row["verification_status"] == "source_verified"
        }
        self.assertEqual(
            promoted_statuses,
            {
                "production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28",
                "production-status-x-men-97-s2-2026-07-01-snapshot-2026-08-28",
                TARGET,
                "production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28",
            },
        )


if __name__ == "__main__":
    unittest.main()

