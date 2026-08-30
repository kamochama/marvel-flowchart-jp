import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "release-avengers-doomsday-2026-12-18-primary": {
        "evidence_id": "evidence-release-avengers-doomsday-2026-12-18-primary",
        "source_id": "marvel-movies-current-v4",
        "review_id": "review-2026-08-29-release-avengers-doomsday-2026-12-18-primary",
    },
    "release-spider-man-beyond-the-spider-verse-tba-primary": {
        "evidence_id": "evidence-release-spider-man-beyond-the-spider-verse-tba-primary",
        "source_id": "sony-beyond-2026",
        "review_id": "review-2026-08-29-release-spider-man-beyond-the-spider-verse-tba-primary",
    },
    "release-visionquest-2026-10-14-primary": {
        "evidence_id": "evidence-release-visionquest-2026-10-14-primary",
        "source_id": "visionquest",
        "review_id": "review-2026-08-29-release-visionquest-2026-10-14-primary",
    },
}
BATCH002_TARGET = "release-spider-man-brand-new-day-2026-07-31-primary"
BATCH003_TARGET = "release-avengers-secret-wars-2027-12-17-primary"
BATCH005_TARGET = "release-x-men-97-s2-2026-07-01-primary"
BATCH008_TARGET = "release-the-punisher-one-last-kill-2026-05-12-primary"
BATCH009_TARGET = "release-blade-mcu-tba-tba-primary"
EXPECTED_PROMOTED_RELEASES = set(TARGETS) | {
    BATCH002_TARGET,
    BATCH003_TARGET,
    BATCH005_TARGET,
    BATCH008_TARGET,
    BATCH009_TARGET,
}
EXPECTED_PROMOTED_STATUS_IDS = {
    "production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28",
    "production-status-x-men-97-s2-2026-07-01-snapshot-2026-08-28",
    "production-status-visionquest-2026-10-14-snapshot-2026-08-28",
    "production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28",
    "production-status-the-punisher-one-last-kill-2026-05-12-snapshot-2026-08-28",
    "production-status-blade-mcu-tba-tba-snapshot-2026-08-28",
    "production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28",
    "production-status-spider-man-beyond-the-spider-verse-tba-snapshot-2026-08-28",
    "production-status-the-fantastic-four-first-steps-2025-snapshot-2026-08-28",
    "production-status-daredevil-born-again-s3-tba-snapshot-2026-08-28",
    "production-status-your-friendly-neighborhood-spider-man-s2-2026-snapshot-2026-08-28",
}


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch001Tests(unittest.TestCase):
    def test_only_named_primary_releases_are_promoted(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        promoted = {
            release_id
            for release_id, row in releases.items()
            if row["verification_status"] == "source_verified"
        }
        self.assertEqual(promoted, EXPECTED_PROMOTED_RELEASES)
        for release_id in TARGETS:
            self.assertEqual(releases[release_id]["verification_status"], "source_verified")
            self.assertNotIn("legacy seed", releases[release_id]["notes"])

    def test_promoted_releases_have_matching_primary_evidence_and_review(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        for release_id, expected in TARGETS.items():
            ev = evidence[expected["evidence_id"]]
            self.assertEqual(ev["fact_table"], "releases.csv")
            self.assertEqual(ev["fact_id"], release_id)
            self.assertEqual(ev["source_id"], expected["source_id"])
            self.assertEqual(ev["evidence_role"], "primary")
            review = reviews[expected["review_id"]]
            self.assertEqual(review["fact_table"], "releases.csv")
            self.assertEqual(review["fact_id"], release_id)
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], expected["evidence_id"])

    def test_status_snapshots_and_other_release_rows_remain_legacy_seed(self):
        releases = _rows("data/library/releases.csv")
        statuses = _rows("data/library/production_status_assertions.csv")
        self.assertTrue(
            all(
                row["verification_status"] == "legacy_seed"
                for row in statuses
                if row["production_status_assertion_id"] not in EXPECTED_PROMOTED_STATUS_IDS
            )
        )
        self.assertTrue(
            all(
                row["verification_status"] == "legacy_seed"
                for row in releases
                if row["release_id"] not in EXPECTED_PROMOTED_RELEASES
            )
        )


if __name__ == "__main__":
    unittest.main()

