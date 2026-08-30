import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28"
RELEASE_TARGET = "release-avengers-doomsday-2026-12-18-primary"
JP_RELEASE = "release-avengers-doomsday-2026-12-18-jp"
EVIDENCE_ID = "evidence-production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28"
REVIEW_ID = "review-2026-08-30-production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ProductionStatusEvidencePromotionBatch007Tests(unittest.TestCase):
    def test_doomsday_status_is_source_verified_without_changing_announced_semantics(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        status = statuses[TARGET]
        self.assertEqual(status["work_id"], "avengers-doomsday-2026-12-18")
        self.assertEqual(status["status"], "announced")
        self.assertEqual(status["asserted_at"], "2026-08-28")
        self.assertEqual(status["certainty"], "confirmed")
        self.assertEqual(status["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", status["notes"])
        self.assertIn("2026-12-18", status["notes"])
        self.assertIn("official", status["notes"])

    def test_status_has_exact_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "production_status_assertions.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "doomsday")
        self.assertEqual(ev["evidence_role"], "primary")
        self.assertEqual(ev["verified_at"], "2026-08-30")
        self.assertIn("2026-12-18", ev["quoted_or_paraphrased_note"])
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "production_status_assertions.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_release_and_japanese_row_remain_unchanged(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        primary = releases[RELEASE_TARGET]
        self.assertEqual(primary["territory"], "US")
        self.assertEqual(primary["release_date"], "2026-12-18")
        self.assertEqual(primary["status"], "announced")
        self.assertEqual(primary["verification_status"], "source_verified")
        jp = releases[JP_RELEASE]
        self.assertEqual(jp["territory"], "JP")
        self.assertEqual(jp["release_date"], "")
        self.assertEqual(jp["verification_status"], "legacy_seed")


if __name__ == "__main__":
    unittest.main()

