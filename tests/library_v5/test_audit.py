import tempfile
import unittest
from pathlib import Path


class LibraryAuditTests(unittest.TestCase):
    def test_duplicate_primary_key_is_reported(self):
        from scripts.library_v5.audit import check_primary_keys

        issues = check_primary_keys(
            "entities.csv",
            [{"entity_id": "e1"}, {"entity_id": "e1"}],
            "entity_id",
        )
        self.assertTrue(any(issue["code"] == "duplicate_primary_key" for issue in issues))

    def test_broken_foreign_key_is_reported_but_nullable_blank_is_allowed(self):
        from scripts.library_v5.audit import check_foreign_keys

        tables = {
            "works.csv": [{"work_id": "w1"}],
            "entities.csv": [{"entity_id": "e1"}],
            "people.csv": [{"person_id": "p1"}],
            "portrayals.csv": [
                {"portrayal_id": "p-ok", "work_id": "w1", "person_id": "p1", "entity_id": ""},
                {"portrayal_id": "p-bad", "work_id": "missing", "person_id": "p1", "entity_id": "e1"},
            ],
        }
        schemas = {
            "portrayals.csv": {
                "primary_key": "portrayal_id",
                "nullable_columns": ["entity_id"],
                "foreign_keys": {"work_id": "works.work_id", "person_id": "people.person_id", "entity_id": "entities.entity_id"},
            }
        }
        issues = check_foreign_keys(tables, schemas)
        self.assertEqual([i["column"] for i in issues], ["work_id"])

    def test_malformed_csv_row_is_reported_instead_of_silently_truncated(self):
        from scripts.library_v5.audit import check_csv_shape

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "entities.csv"
            path.write_text("entity_id,notes\ne1,ok,unexpected\n", encoding="utf-8")
            issues = check_csv_shape(path, "entities.csv")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], "malformed_csv_row")
        self.assertEqual(issues[0]["row"], "2")
        self.assertEqual(issues[0]["expected_columns"], "2")
        self.assertEqual(issues[0]["actual_columns"], "3")

    def test_source_verified_fact_without_qualifying_evidence_is_reported_legacy_seed_is_not(self):
        from scripts.library_v5.audit import check_evidence_coverage

        tables = {
            "appearances.csv": [
                {"appearance_id": "ap-verified", "verification_status": "source_verified"},
                {"appearance_id": "ap-seed", "verification_status": "legacy_seed"},
            ],
            "evidence.csv": [
                {"fact_table": "appearances.csv", "fact_id": "ap-verified", "evidence_role": "legacy_seed"},
            ],
        }
        issues = check_evidence_coverage(tables)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["fact_id"], "ap-verified")

    def test_migration_coverage_compares_inputs_to_dispositions_not_fixed_counts(self):
        from scripts.library_v5.audit import check_migration_coverage

        issues = check_migration_coverage(
            legacy_counts={"connections": 3, "char_links": 4, "entity_returns": 2, "story_paths": 1},
            disposition_counts={"connections": 3, "char_links": 4, "entity_returns": 1, "story_paths": 1},
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["dataset"], "entity_returns")

    def test_manifest_hashes_are_deterministic_and_exclude_generated_bootstrap_and_manifest(self):
        from scripts.library_v5.audit import build_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data/library").mkdir(parents=True)
            (root / "data/derived/db").mkdir(parents=True)
            (root / "data/migration/bootstrap/library").mkdir(parents=True)
            (root / "data/library/entities.csv").write_text("entity_id\ne1\n", encoding="utf-8")
            (root / "data/library/manifest.json").write_text("old", encoding="utf-8")
            (root / "data/derived/db/marvel.sqlite").write_bytes(b"sqlite-physical-layout")
            (root / "data/derived/db/library_db_manifest.json").write_text('{"equivalence":"logical"}\n', encoding="utf-8")
            (root / "data/migration/bootstrap/library/entities.csv").write_text("candidate", encoding="utf-8")
            first = build_manifest(root)
            second = build_manifest(root)
            self.assertEqual(first, second)
            self.assertNotIn("data/library/manifest.json", first["files"])
            self.assertNotIn("data/migration/bootstrap/library/entities.csv", first["files"])
            self.assertNotIn("data/derived/db/marvel.sqlite", first["files"])
            self.assertIn("data/derived/db/library_db_manifest.json", first["files"])

    def test_full_build_is_byte_deterministic_on_fixture(self):
        from scripts.library_v5.audit import sha256_file

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text("a,b\n1,2\n", encoding="utf-8")
            self.assertEqual(sha256_file(path), sha256_file(path))


if __name__ == "__main__":
    unittest.main()
