import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RELEASE_TARGET = "release-daredevil-born-again-s2-2026-jp"
STATUS_TARGET = "production-status-daredevil-born-again-s2-2026-snapshot-2026-08-28"
SOURCE_ID = "disneyplus-jp-daredevil-born-again-s2-2026"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch012Tests(unittest.TestCase):
    def test_daredevil_s2_jp_release_and_status_are_directly_verified(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        release = releases[RELEASE_TARGET]
        self.assertEqual(release["territory"], "JP")
        self.assertEqual(release["release_date"], "2026-03-25")
        self.assertEqual(release["release_precision"], "day")
        self.assertEqual(release["status"], "released")
        self.assertEqual(release["verification_status"], "source_verified")
        statuses = {row["production_status_assertion_id"]: row for row in _rows("data/library/production_status_assertions.csv")}
        status = statuses[STATUS_TARGET]
        self.assertEqual(status["status"], "released")
        self.assertEqual(status["asserted_at"], "2026-08-28")
        self.assertEqual(status["verification_status"], "source_verified")
        self.assertIn("2026-03-25", status["notes"])

    def test_exact_evidence_and_reviews_use_the_new_disneyplus_source(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        for fact_id, table in ((RELEASE_TARGET, "releases.csv"), (STATUS_TARGET, "production_status_assertions.csv")):
            evidence_id = f"evidence-{fact_id}"
            self.assertEqual(evidence[evidence_id]["fact_table"], table)
            self.assertEqual(evidence[evidence_id]["fact_id"], fact_id)
            self.assertEqual(evidence[evidence_id]["source_id"], SOURCE_ID)
            self.assertEqual(evidence[evidence_id]["evidence_role"], "primary")
            review = reviews[f"review-2026-08-30-{fact_id}"]
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], evidence_id)

    def test_primary_row_date_and_jp_scope_are_not_rewritten(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        primary = releases["release-daredevil-born-again-s2-2026-primary"]
        self.assertEqual(primary["verification_status"], "legacy_seed")
        self.assertEqual(primary["release_date"], "2026-03-24")
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in releases.values()), 14)


if __name__ == "__main__":
    unittest.main()

