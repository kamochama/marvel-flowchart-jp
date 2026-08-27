import unittest


class MigrationReviewTests(unittest.TestCase):
    def test_disposition_summary_is_sorted_and_counts_all_rows(self):
        from scripts.library_v5.audit import summarize_dispositions

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


if __name__ == "__main__":
    unittest.main()
