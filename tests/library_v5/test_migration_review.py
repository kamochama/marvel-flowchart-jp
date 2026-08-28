import unittest


class MigrationReviewTests(unittest.TestCase):
    def test_disposition_summary_is_sorted_and_counts_all_rows(self):
        from scripts.library_v5.review_migration import summarize_dispositions

        rows = [
            {"disposition": "migrated_explicit_relation"},
            {"disposition": "appearance_derived_pending_audit"},
            {"disposition": "migrated_explicit_relation"},
            {"disposition": ""},
        ]
        self.assertEqual(
            summarize_dispositions(rows),
            {
                "<blank>": 1,
                "appearance_derived_pending_audit": 1,
                "migrated_explicit_relation": 2,
            },
        )

    def test_review_marks_pending_audit_and_superseded_as_explicit_backlog(self):
        from scripts.library_v5.review_migration import summarize_review_rows

        summary = summarize_review_rows(
            connection_rows=[
                {"disposition": "migrated_explicit_relation"},
                {"disposition": "appearance_derived_pending_audit"},
                {"disposition": "rejected_superseded"},
            ],
            entity_rows=[
                {"disposition": "migrated_appearance_seed"},
                {"disposition": "decomposed_entity_return_seed"},
            ],
            story_rows=[{"disposition": "reproduced"}],
            chronology_rows=[{"disposition": "legacy_display_placement_seed"}],
        )
        self.assertEqual(summary["connections"]["migrated_explicit_relation"], 1)
        self.assertEqual(summary["content_audit_backlog"]["appearance_derived_pending_audit"], 1)
        self.assertEqual(summary["content_audit_backlog"]["rejected_superseded"], 1)
        self.assertEqual(summary["content_audit_backlog"]["legacy_display_placement_seed"], 1)


if __name__ == "__main__":
    unittest.main()
