import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "release-avengers-doomsday-2026-12-18-jp": "doomsday-jp",
    "release-the-fantastic-four-first-steps-2025-jp": "marvel-jp-fantastic4-2025",
}


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch011Tests(unittest.TestCase):
    def test_japanese_release_dates_are_completed_only_from_direct_sources(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        expected = {
            "release-avengers-doomsday-2026-12-18-jp": ("2026-12-18", "announced"),
            "release-the-fantastic-four-first-steps-2025-jp": ("2025-07-25", "released"),
        }
        for fact_id, (date, status) in expected.items():
            row = releases[fact_id]
            self.assertEqual(row["territory"], "JP")
            self.assertEqual(row["release_date"], date)
            self.assertEqual(row["release_precision"], "day")
            self.assertEqual(row["status"], status)
            self.assertEqual(row["verification_status"], "source_verified")

    def test_exact_primary_evidence_and_review_exist_for_each_japanese_row(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        for fact_id, source_id in TARGETS.items():
            evidence_id = f"evidence-{fact_id}"
            ev = evidence[evidence_id]
            self.assertEqual(ev["fact_table"], "releases.csv")
            self.assertEqual(ev["fact_id"], fact_id)
            self.assertEqual(ev["source_id"], source_id)
            self.assertEqual(ev["evidence_role"], "primary")
            self.assertEqual(ev["verified_at"], "2026-08-30")
            review = reviews[f"review-2026-08-30-{fact_id}"]
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], evidence_id)

    def test_primary_us_rows_and_graph_scope_remain_unchanged(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        self.assertEqual(releases["release-avengers-doomsday-2026-12-18-primary"]["verification_status"], "source_verified")
        self.assertEqual(releases["release-the-fantastic-four-first-steps-2025-primary"]["verification_status"], "legacy_seed")
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in releases.values()), 14)


if __name__ == "__main__":
    unittest.main()

