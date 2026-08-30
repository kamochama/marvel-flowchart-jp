import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "release-spider-man-brand-new-day-2026-07-31-primary"
EVIDENCE_ID = "evidence-release-spider-man-brand-new-day-2026-07-31-primary"
REVIEW_ID = "review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch002Tests(unittest.TestCase):
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
        }
        self.assertEqual(
            promoted,
            expected_existing
            | {
                TARGET,
                "release-avengers-secret-wars-2027-12-17-primary",
                "release-x-men-97-s2-2026-07-01-primary",
                "release-the-punisher-one-last-kill-2026-05-12-primary",
                "release-blade-mcu-tba-tba-primary",
                "release-avengers-doomsday-2026-12-18-jp",
                "release-the-fantastic-four-first-steps-2025-jp",
                "release-daredevil-born-again-s2-2026-jp",
                "release-wonder-man-s1-2026-jp",
                "release-x-men-97-s2-2026-07-01-jp",
                "release-thunderbolts-new-avengers-2025-primary",
            },
        )
        self.assertEqual(releases[TARGET]["territory"], "US")
        self.assertEqual(releases[TARGET]["release_date"], "2026-07-31")
        self.assertEqual(releases[TARGET]["release_precision"], "day")
        self.assertEqual(releases[TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", releases[TARGET]["notes"])

    def test_brand_new_day_release_has_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "releases.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "sony-bnd-2026-07-03")
        self.assertEqual(ev["evidence_role"], "primary")
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "releases.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_japanese_release_remains_legacy_seed_and_status_snapshot_is_verified(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        jp = releases["release-spider-man-brand-new-day-2026-07-31-jp"]
        self.assertEqual(jp["verification_status"], "legacy_seed")
        self.assertEqual(jp["release_date"], "")
        snapshot = statuses["production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"]
        self.assertEqual(snapshot["verification_status"], "source_verified")


if __name__ == "__main__":
    unittest.main()

