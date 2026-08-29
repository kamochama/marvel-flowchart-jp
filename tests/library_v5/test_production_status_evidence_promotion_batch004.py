import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"
EVIDENCE_ID = "evidence-production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"
REVIEW_ID = "review-2026-08-30-production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ProductionStatusEvidencePromotionBatch004Tests(unittest.TestCase):
    def test_only_brand_new_day_status_is_added_to_verified_status_set(self):
        statuses = {row["production_status_assertion_id"]: row for row in _rows("data/library/production_status_assertions.csv")}
        promoted = {
            status_id
            for status_id, row in statuses.items()
            if row["verification_status"] == "source_verified"
        }
        self.assertEqual(promoted, {TARGET})
        self.assertEqual(statuses[TARGET]["status"], "released")
        self.assertEqual(statuses[TARGET]["asserted_at"], "2026-08-28")
        self.assertEqual(statuses[TARGET]["certainty"], "confirmed")
        self.assertEqual(statuses[TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", statuses[TARGET]["notes"])

    def test_status_has_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "production_status_assertions.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "sony-bnd-current-2026-08")
        self.assertEqual(ev["evidence_role"], "primary")
        self.assertEqual(ev["verified_at"], "2026-08-30")
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "production_status_assertions.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_release_rows_and_other_statuses_remain_legacy_seed(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        statuses = _rows("data/library/production_status_assertions.csv")
        self.assertTrue(
            all(
                row["verification_status"] == "legacy_seed"
                for row in statuses
                if row["production_status_assertion_id"] != TARGET
            )
        )
        self.assertEqual(
            releases["release-spider-man-brand-new-day-2026-07-31-primary"]["verification_status"],
            "source_verified",
        )
        jp = releases["release-spider-man-brand-new-day-2026-07-31-jp"]
        self.assertEqual(jp["verification_status"], "legacy_seed")
        self.assertEqual(jp["release_date"], "")


if __name__ == "__main__":
    unittest.main()
