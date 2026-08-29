import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "release-x-men-97-s2-2026-07-01-primary"
STATUS_TARGET = "production-status-x-men-97-s2-2026-07-01-snapshot-2026-08-28"
RELEASE_EVIDENCE_ID = "evidence-release-x-men-97-s2-2026-07-01-primary"
STATUS_EVIDENCE_ID = "evidence-production-status-x-men-97-s2-2026-07-01-snapshot-2026-08-28"
RELEASE_REVIEW_ID = "review-2026-08-30-release-x-men-97-s2-2026-07-01-primary"
STATUS_REVIEW_ID = "review-2026-08-30-production-status-x-men-97-s2-2026-07-01-snapshot-2026-08-28"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch005Tests(unittest.TestCase):
    def test_xmen97_release_and_status_are_the_only_new_promotions(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        self.assertEqual(releases[TARGET]["territory"], "unknown")
        self.assertEqual(releases[TARGET]["release_kind"], "streaming")
        self.assertEqual(releases[TARGET]["release_date"], "2026-07-01")
        self.assertEqual(releases[TARGET]["release_precision"], "day")
        self.assertEqual(releases[TARGET]["status"], "released")
        self.assertEqual(releases[TARGET]["certainty"], "confirmed")
        self.assertEqual(releases[TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", releases[TARGET]["notes"])
        self.assertEqual(statuses[STATUS_TARGET]["status"], "released")
        self.assertEqual(statuses[STATUS_TARGET]["asserted_at"], "2026-08-28")
        self.assertEqual(statuses[STATUS_TARGET]["certainty"], "confirmed")
        self.assertEqual(statuses[STATUS_TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", statuses[STATUS_TARGET]["notes"])

    def test_release_and_status_have_exact_primary_evidence_and_review(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        release_evidence = evidence[RELEASE_EVIDENCE_ID]
        self.assertEqual(release_evidence["fact_table"], "releases.csv")
        self.assertEqual(release_evidence["fact_id"], TARGET)
        self.assertEqual(release_evidence["source_id"], "xmen97-s2")
        self.assertEqual(release_evidence["evidence_role"], "primary")
        self.assertEqual(release_evidence["verified_at"], "2026-08-30")
        status_evidence = evidence[STATUS_EVIDENCE_ID]
        self.assertEqual(status_evidence["fact_table"], "production_status_assertions.csv")
        self.assertEqual(status_evidence["fact_id"], STATUS_TARGET)
        self.assertEqual(status_evidence["source_id"], "xmen97-s2-current-2026-08")
        self.assertEqual(status_evidence["evidence_role"], "primary")
        self.assertEqual(status_evidence["verified_at"], "2026-08-30")
        release_review = reviews[RELEASE_REVIEW_ID]
        self.assertEqual(release_review["fact_table"], "releases.csv")
        self.assertEqual(release_review["fact_id"], TARGET)
        self.assertEqual(release_review["previous_verification_status"], "legacy_seed")
        self.assertEqual(release_review["new_verification_status"], "source_verified")
        self.assertEqual(release_review["review_action"], "verified_source")
        self.assertEqual(release_review["evidence_ids"], RELEASE_EVIDENCE_ID)
        status_review = reviews[STATUS_REVIEW_ID]
        self.assertEqual(status_review["fact_table"], "production_status_assertions.csv")
        self.assertEqual(status_review["fact_id"], STATUS_TARGET)
        self.assertEqual(status_review["previous_verification_status"], "legacy_seed")
        self.assertEqual(status_review["new_verification_status"], "source_verified")
        self.assertEqual(status_review["review_action"], "verified_source")
        self.assertEqual(status_review["evidence_ids"], STATUS_EVIDENCE_ID)

    def test_japanese_release_row_stays_legacy_without_inferred_date(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        jp = releases["release-x-men-97-s2-2026-07-01-jp"]
        self.assertEqual(jp["territory"], "JP")
        self.assertEqual(jp["verification_status"], "legacy_seed")
        self.assertEqual(jp["release_date"], "")


if __name__ == "__main__":
    unittest.main()
