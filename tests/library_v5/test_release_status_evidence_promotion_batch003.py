import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "release-avengers-secret-wars-2027-12-17-primary"
EVIDENCE_ID = "evidence-release-avengers-secret-wars-2027-12-17-primary"
REVIEW_ID = "review-2026-08-29-release-avengers-secret-wars-2027-12-17-primary"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseEvidencePromotionBatch003Tests(unittest.TestCase):
    def test_cumulative_promoted_release_set_is_preserved(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        promoted = {
            release_id
            for release_id, row in releases.items()
            if row["verification_status"] == "source_verified"
        }
        expected_existing = {
            "release-avengers-doomsday-2026-12-18-primary",
            "release-spider-man-beyond-the-spider-verse-tba-primary",
            "release-visionquest-2026-10-14-primary",
            "release-spider-man-brand-new-day-2026-07-31-primary",
            "release-x-men-97-s2-2026-07-01-primary",
            "release-the-punisher-one-last-kill-2026-05-12-primary",
            "release-blade-mcu-tba-tba-primary",
        }
        self.assertEqual(promoted, expected_existing | {TARGET})
        self.assertEqual(releases[TARGET]["territory"], "US")
        self.assertEqual(releases[TARGET]["release_kind"], "theatrical")
        self.assertEqual(releases[TARGET]["release_date"], "2027-12-17")
        self.assertEqual(releases[TARGET]["release_precision"], "day")
        self.assertEqual(releases[TARGET]["status"], "announced")
        self.assertEqual(releases[TARGET]["certainty"], "confirmed")
        self.assertEqual(releases[TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", releases[TARGET]["notes"])

    def test_secret_wars_release_has_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "releases.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "marvel-movies-current-v4")
        self.assertEqual(ev["evidence_role"], "primary")
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "releases.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_secret_wars_status_snapshot_is_source_verified(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        snapshot = statuses["production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28"]
        self.assertEqual(snapshot["verification_status"], "source_verified")


if __name__ == "__main__":
    unittest.main()

