import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RELEASE_TARGETS = {
    "release-blade-mcu-tba-tba-primary": "evidence-release-blade-mcu-tba-tba-primary",
}
STATUS_TARGETS = {
    "production-status-blade-mcu-tba-tba-snapshot-2026-08-28": "evidence-production-status-blade-mcu-tba-tba-snapshot-2026-08-28",
    "production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28": "evidence-production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28",
    "production-status-spider-man-beyond-the-spider-verse-tba-snapshot-2026-08-28": "evidence-production-status-spider-man-beyond-the-spider-verse-tba-snapshot-2026-08-28",
}


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch009Tests(unittest.TestCase):
    def test_blade_undated_release_and_status_preserve_unknown_semantics(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        release = releases["release-blade-mcu-tba-tba-primary"]
        self.assertEqual(
            (release["territory"], release["release_kind"], release["release_date"], release["release_precision"], release["status"], release["certainty"]),
            ("unknown", "undated", "", "none", "announced", "unknown"),
        )
        self.assertEqual(release["verification_status"], "source_verified")
        status = statuses["production-status-blade-mcu-tba-tba-snapshot-2026-08-28"]
        self.assertEqual(
            (status["status"], status["asserted_at"], status["certainty"], status["verification_status"]),
            ("announced", "2026-08-28", "unknown", "source_verified"),
        )
        self.assertIn("undated", release["notes"].lower())
        self.assertIn("listing", status["notes"].lower())

    def test_secret_wars_and_beyond_statuses_keep_announced_snapshot(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        for target in STATUS_TARGETS:
            status = statuses[target]
            self.assertEqual(status["status"], "announced")
            self.assertEqual(status["asserted_at"], "2026-08-28")
            self.assertEqual(status["verification_status"], "source_verified")
        self.assertEqual(statuses["production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28"]["certainty"], "confirmed")
        self.assertEqual(statuses["production-status-spider-man-beyond-the-spider-verse-tba-snapshot-2026-08-28"]["certainty"], "confirmed")

    def test_each_fact_has_exact_primary_evidence_and_review(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        expected_sources = {
            "release-blade-mcu-tba-tba-primary": "movies",
            "production-status-blade-mcu-tba-tba-snapshot-2026-08-28": "movies",
            "production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28": "marvel-movies-current-v4",
            "production-status-spider-man-beyond-the-spider-verse-tba-snapshot-2026-08-28": "sony-beyond-2026",
        }
        fact_ids = list(RELEASE_TARGETS) + list(STATUS_TARGETS)
        for fact_id in fact_ids:
            evidence_id = RELEASE_TARGETS.get(fact_id, STATUS_TARGETS.get(fact_id))
            ev = evidence[evidence_id]
            self.assertEqual(ev["fact_id"], fact_id)
            self.assertEqual(ev["source_id"], expected_sources[fact_id])
            self.assertEqual(ev["evidence_role"], "primary")
            self.assertEqual(ev["verified_at"], "2026-08-30")
            review = reviews[f"review-2026-08-30-{fact_id}"]
            self.assertEqual(review["fact_id"], fact_id)
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], evidence_id)

    def test_japanese_and_unrelated_rows_remain_legacy_seed(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        self.assertEqual(releases["release-avengers-doomsday-2026-12-18-jp"]["verification_status"], "legacy_seed")
        self.assertEqual(releases["release-avengers-doomsday-2026-12-18-jp"]["release_date"], "")
        statuses = _rows("data/library/production_status_assertions.csv")
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in releases.values()), 8)
        self.assertEqual(sum(row["verification_status"] == "source_verified" for row in statuses), 11)


if __name__ == "__main__":
    unittest.main()

