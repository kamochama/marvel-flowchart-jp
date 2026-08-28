import tempfile
import unittest
from pathlib import Path


class ContentAuditTests(unittest.TestCase):
    def test_review_validation_rejects_missing_fact_evidence_and_duplicate_id(self):
        from scripts.library_v5.content_audit import validate_reviews

        tables = {
            "appearances.csv": [{"appearance_id": "ap-1", "verification_status": "source_verified"}],
        }
        evidence = [{"evidence_id": "ev-1"}]
        reviews = [
            {"review_id": "r1", "fact_table": "appearances.csv", "fact_id": "ap-1", "previous_verification_status": "legacy_seed", "new_verification_status": "source_verified", "review_action": "promoted", "evidence_ids": "ev-1"},
            {"review_id": "r1", "fact_table": "appearances.csv", "fact_id": "missing", "previous_verification_status": "legacy_seed", "new_verification_status": "source_verified", "review_action": "promoted", "evidence_ids": "ev-missing"},
        ]
        issues = validate_reviews(tables, evidence, reviews)
        codes = {issue["code"] for issue in issues}
        self.assertIn("duplicate_review_id", codes)
        self.assertIn("review_missing_fact", codes)
        self.assertIn("review_missing_evidence", codes)

    def test_review_validation_rejects_status_mismatch_and_invalid_transition(self):
        from scripts.library_v5.content_audit import validate_reviews

        tables = {
            "work_relations.csv": [{"work_relation_id": "wr-1", "verification_status": "legacy_seed"}],
        }
        reviews = [{"review_id": "r1", "fact_table": "work_relations.csv", "fact_id": "wr-1", "previous_verification_status": "source_verified", "new_verification_status": "source_verified", "review_action": "promoted", "evidence_ids": ""}]
        issues = validate_reviews(tables, [], reviews)
        codes = {issue["code"] for issue in issues}
        self.assertIn("invalid_review_transition", codes)
        self.assertIn("review_current_status_mismatch", codes)

    def test_verified_rechecked_allows_source_verified_status_to_stay_verified(self):
        from scripts.library_v5.content_audit import validate_reviews

        tables = {
            "work_relations.csv": [{"work_relation_id": "wr-1", "verification_status": "source_verified"}],
        }
        evidence = [{"evidence_id": "ev-1"}]
        reviews = [
            {
                "review_id": "r1",
                "fact_table": "work_relations.csv",
                "fact_id": "wr-1",
                "previous_verification_status": "source_verified",
                "new_verification_status": "source_verified",
                "review_action": "verified_rechecked",
                "evidence_ids": "ev-1",
            }
        ]
        issues = validate_reviews(tables, evidence, reviews)
        self.assertEqual(issues, [])

    def test_queue_is_deterministic_and_prioritizes_high_impact_then_high_degree(self):
        from scripts.library_v5.content_audit import build_review_queue

        tables = {
            "appearances.csv": [
                {"appearance_id": "ap-old", "work_id": "iron-man-2008", "entity_id": "e1", "verification_status": "legacy_seed"},
                {"appearance_id": "ap-doom", "work_id": "avengers-doomsday-2026-12-18", "entity_id": "e2", "verification_status": "legacy_seed"},
                {"appearance_id": "ap-degree", "work_id": "the-avengers-2012", "entity_id": "e3", "verification_status": "legacy_seed"},
            ],
            "work_relations.csv": [],
            "portrayals.csv": [],
            "continuities.csv": [],
            "work_continuities.csv": [],
            "chronology_assertions.csv": [],
            "entity_relations.csv": [],
        }
        first = build_review_queue(tables, high_degree_work_ids={"the-avengers-2012"})
        second = build_review_queue(tables, high_degree_work_ids={"the-avengers-2012"})
        self.assertEqual(first, second)
        self.assertEqual([row["fact_id"] for row in first], ["ap-doom", "ap-degree", "ap-old"])
        self.assertEqual(first[0]["priority_reason"], "high_impact_current_cluster")
        self.assertEqual(first[1]["priority_reason"], "high_degree_work")

    def test_source_verified_facts_are_not_queued(self):
        from scripts.library_v5.content_audit import build_review_queue

        tables = {
            "appearances.csv": [
                {"appearance_id": "ap-seed", "work_id": "x", "entity_id": "e", "verification_status": "legacy_seed"},
                {"appearance_id": "ap-ok", "work_id": "y", "entity_id": "e", "verification_status": "source_verified"},
            ],
            "work_relations.csv": [], "portrayals.csv": [], "continuities.csv": [], "work_continuities.csv": [], "chronology_assertions.csv": [], "entity_relations.csv": [],
        }
        queue = build_review_queue(tables)
        self.assertEqual([row["fact_id"] for row in queue], ["ap-seed"])

    def test_release_status_facts_are_reviewable(self):
        from scripts.library_v5.content_audit import build_review_queue

        tables = {
            "releases.csv": [{
                "release_id": "release-seed",
                "work_id": "iron-man-2008",
                "verification_status": "legacy_seed",
                "certainty": "unknown",
            }],
            "production_status_assertions.csv": [{
                "production_status_assertion_id": "production-status-seed",
                "work_id": "iron-man-2008",
                "verification_status": "legacy_seed",
                "certainty": "unknown",
            }],
        }
        queue = build_review_queue(tables)
        self.assertEqual(
            [row["queue_id"] for row in queue],
            ["production_status_assertions.csv:production-status-seed", "releases.csv:release-seed"],
        )

    def test_ordinary_content_audit_refuses_to_create_persistent_review_ledger(self):
        from scripts.library_v5.content_audit import write_content_audit_outputs

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data/library").mkdir(parents=True)
            (root / "data/derived").mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, "missing_content_review_ledger"):
                write_content_audit_outputs(root)
            self.assertFalse((root / "data/content_audit/reviews.csv").exists())


if __name__ == "__main__":
    unittest.main()
