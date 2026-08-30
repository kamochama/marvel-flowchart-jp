import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RELEASE_TARGET = "release-wonder-man-s1-2026-jp"
STATUS_TARGET = "production-status-wonder-man-s1-2026-snapshot-2026-08-28"
SOURCE_ID = "marvel-jp-wonder-man-s1-2026"
RELEASE_EVIDENCE = f"evidence-{RELEASE_TARGET}"
RELEASE_REVIEW = f"review-2026-08-30-{RELEASE_TARGET}"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch013Tests(unittest.TestCase):
    def test_wonder_man_jp_release_date_is_completed_without_status_inference(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        row = releases[RELEASE_TARGET]
        self.assertEqual(row["territory"], "JP")
        self.assertEqual(row["release_kind"], "streaming")
        self.assertEqual(row["release_date"], "2026-01-28")
        self.assertEqual(row["release_precision"], "day")
        self.assertEqual(row["status"], "released")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")
        primary = releases["release-wonder-man-s1-2026-primary"]
        self.assertEqual(primary["release_date"], "2026-01-27")
        self.assertEqual(primary["territory"], "unknown")
        self.assertEqual(primary["verification_status"], "legacy_seed")
        statuses = {row["production_status_assertion_id"]: row for row in _rows("data/library/production_status_assertions.csv")}
        self.assertEqual(statuses[STATUS_TARGET]["verification_status"], "legacy_seed")

    def test_wonder_man_jp_release_has_exact_source_evidence_and_review(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[RELEASE_EVIDENCE]
        self.assertEqual(ev["fact_table"], "releases.csv")
        self.assertEqual(ev["fact_id"], RELEASE_TARGET)
        self.assertEqual(ev["source_id"], SOURCE_ID)
        self.assertEqual(ev["evidence_role"], "primary")
        self.assertEqual(ev["verified_at"], "2026-08-30")
        self.assertIn("2026-01-28", ev["quoted_or_paraphrased_note"])
        review = reviews[RELEASE_REVIEW]
        self.assertEqual(review["fact_table"], "releases.csv")
        self.assertEqual(review["fact_id"], RELEASE_TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], RELEASE_EVIDENCE)

    def test_batch_counts_and_source_registration(self):
        releases = _rows("data/library/releases.csv")
        statuses = _rows("data/library/production_status_assertions.csv")
        sources = {row["source_id"]: row for row in _rows("data/library/sources.csv")}
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in releases), 14)
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in statuses), 13)
        self.assertEqual(sources[SOURCE_ID]["official_source"], "Marvel Japan")
        self.assertIn("2026-01-28", sources[SOURCE_ID]["checked_point"])


if __name__ == "__main__":
    unittest.main()

