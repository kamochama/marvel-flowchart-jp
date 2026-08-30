import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RELEASE_TARGET = "release-thunderbolts-new-avengers-2025-primary"
STATUS_TARGET = "production-status-thunderbolts-new-avengers-2025-snapshot-2026-08-28"
SOURCE_ID = "disney-movies-thunderbolts-2025"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch015Tests(unittest.TestCase):
    def test_thunderbolts_us_release_and_status_are_verified_without_scope_drift(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        release = releases[RELEASE_TARGET]
        self.assertEqual(release["territory"], "US")
        self.assertEqual(release["release_kind"], "theatrical")
        self.assertEqual(release["release_date"], "2025-05-02")
        self.assertEqual(release["release_precision"], "day")
        self.assertEqual(release["status"], "released")
        self.assertEqual(release["verification_status"], "source_verified")
        statuses = {row["production_status_assertion_id"]: row for row in _rows("data/library/production_status_assertions.csv")}
        status = statuses[STATUS_TARGET]
        self.assertEqual(status["status"], "released")
        self.assertEqual(status["asserted_at"], "2026-08-28")
        self.assertEqual(status["certainty"], "confirmed")
        self.assertEqual(status["verification_status"], "source_verified")

    def test_thunderbolts_release_and_status_have_exact_primary_evidence_and_reviews(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        for fact_id, table in ((RELEASE_TARGET, "releases.csv"), (STATUS_TARGET, "production_status_assertions.csv")):
            evidence_id = f"evidence-{fact_id}"
            ev = evidence[evidence_id]
            self.assertEqual(ev["fact_table"], table)
            self.assertEqual(ev["fact_id"], fact_id)
            self.assertEqual(ev["source_id"], SOURCE_ID)
            self.assertEqual(ev["evidence_role"], "primary")
            self.assertEqual(ev["verified_at"], "2026-08-30")
            self.assertIn("2025-05-02", ev["quoted_or_paraphrased_note"])
            review = reviews[f"review-2026-08-30-{fact_id}"]
            self.assertEqual(review["fact_table"], table)
            self.assertEqual(review["fact_id"], fact_id)
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], evidence_id)

    def test_batch_counts_and_source_registration(self):
        releases = _rows("data/library/releases.csv")
        statuses = _rows("data/library/production_status_assertions.csv")
        sources = {row["source_id"]: row for row in _rows("data/library/sources.csv")}
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in releases), 14)
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in statuses), 13)
        self.assertEqual(sources[SOURCE_ID]["official_source"], "Disney Movies")
        self.assertIn("May 2, 2025", sources[SOURCE_ID]["checked_point"])


if __name__ == "__main__":
    unittest.main()

