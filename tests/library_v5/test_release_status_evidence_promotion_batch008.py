import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RELEASE_TARGET = "release-the-punisher-one-last-kill-2026-05-12-primary"
STATUS_TARGET = "production-status-the-punisher-one-last-kill-2026-05-12-snapshot-2026-08-28"
RELEASE_EVIDENCE = "evidence-release-the-punisher-one-last-kill-2026-05-12-primary"
STATUS_EVIDENCE = "evidence-production-status-the-punisher-one-last-kill-2026-05-12-snapshot-2026-08-28"
RELEASE_REVIEW = "review-2026-08-30-release-the-punisher-one-last-kill-2026-05-12-primary"
STATUS_REVIEW = "review-2026-08-30-production-status-the-punisher-one-last-kill-2026-05-12-snapshot-2026-08-28"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch008Tests(unittest.TestCase):
    def test_punisher_release_is_source_verified_without_semantic_drift(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        release = releases[RELEASE_TARGET]
        self.assertEqual(release["work_id"], "the-punisher-one-last-kill-2026-05-12")
        self.assertEqual(release["territory"], "unknown")
        self.assertEqual(release["release_kind"], "streaming")
        self.assertEqual(release["release_date"], "2026-05-12")
        self.assertEqual(release["release_precision"], "day")
        self.assertEqual(release["status"], "released")
        self.assertEqual(release["certainty"], "confirmed")
        self.assertEqual(release["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", release["notes"])

    def test_punisher_status_is_source_verified_without_milestone_inference(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        status = statuses[STATUS_TARGET]
        self.assertEqual(status["work_id"], "the-punisher-one-last-kill-2026-05-12")
        self.assertEqual(status["status"], "released")
        self.assertEqual(status["asserted_at"], "2026-08-28")
        self.assertEqual(status["certainty"], "confirmed")
        self.assertEqual(status["verification_status"], "source_verified")
        self.assertIn("MAY 12, 2026", status["notes"])
        self.assertIn("snapshot", status["notes"])

    def test_exact_primary_evidence_and_review_transitions_exist(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        for evidence_id, fact_id in (
            (RELEASE_EVIDENCE, RELEASE_TARGET),
            (STATUS_EVIDENCE, STATUS_TARGET),
        ):
            ev = evidence[evidence_id]
            self.assertEqual(ev["fact_id"], fact_id)
            self.assertEqual(ev["source_id"], "tv")
            self.assertEqual(ev["evidence_role"], "primary")
            self.assertEqual(ev["verified_at"], "2026-08-30")
            self.assertIn("MAY 12, 2026", ev["quoted_or_paraphrased_note"])
        for review_id, fact_id, evidence_id in (
            (RELEASE_REVIEW, RELEASE_TARGET, RELEASE_EVIDENCE),
            (STATUS_REVIEW, STATUS_TARGET, STATUS_EVIDENCE),
        ):
            review = reviews[review_id]
            self.assertEqual(review["fact_id"], fact_id)
            self.assertEqual(review["previous_verification_status"], "legacy_seed")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "verified_source")
            self.assertEqual(review["evidence_ids"], evidence_id)

    def test_japanese_row_and_graph_scope_remain_unchanged(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        jp = releases["release-the-punisher-one-last-kill-2026-05-12-jp"]
        self.assertEqual(jp["territory"], "JP")
        self.assertEqual(jp["release_date"], "")
        self.assertEqual(jp["verification_status"], "legacy_seed")
        self.assertEqual(
            sum(row["verification_status"] == "source_verified" for row in releases.values()),
            14,
        )
        statuses = _rows("data/library/production_status_assertions.csv")
        self.assertEqual(
            sum(row["verification_status"] == "source_verified" for row in statuses),
            13,
        )


if __name__ == "__main__":
    unittest.main()

