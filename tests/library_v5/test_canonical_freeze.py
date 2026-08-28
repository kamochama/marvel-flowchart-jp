import tempfile
import unittest
from pathlib import Path
from unittest import mock


class CanonicalFreezeTests(unittest.TestCase):
    def test_canonical_hashes_detect_mutation(self):
        from scripts.library_v5.canonical_guard import canonical_hashes, assert_canonical_unchanged

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = root / "data" / "library"
            library.mkdir(parents=True)
            (library / "works.csv").write_text("work_id\nw1\n", encoding="utf-8")
            before = canonical_hashes(root)
            (library / "works.csv").write_text("work_id\nw2\n", encoding="utf-8")
            after = canonical_hashes(root)
            with self.assertRaisesRegex(RuntimeError, "canonical_input_mutated"):
                assert_canonical_unchanged(before, after)

    def test_clean_generated_preserves_library_and_reviews(self):
        from scripts.library_v5.build import clean_generated

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data/library").mkdir(parents=True)
            (root / "data/library/works.csv").write_text("canonical", encoding="utf-8")
            (root / "data/library/manifest.json").write_text("legacy-generated", encoding="utf-8")
            (root / "data/content_audit").mkdir(parents=True)
            (root / "data/content_audit/reviews.csv").write_text("persistent", encoding="utf-8")
            (root / "data/content_audit/queue.csv").write_text("generated", encoding="utf-8")
            (root / "data/derived").mkdir(parents=True)
            (root / "data/derived/x.csv").write_text("generated", encoding="utf-8")

            clean_generated(root)

            self.assertEqual((root / "data/library/works.csv").read_text(), "canonical")
            self.assertEqual((root / "data/content_audit/reviews.csv").read_text(), "persistent")
            self.assertFalse((root / "data/derived").exists())
            self.assertFalse((root / "data/content_audit/queue.csv").exists())

    def test_ordinary_build_does_not_call_migration_writers(self):
        import scripts.library_v5.build as build_module

        with mock.patch.object(build_module, "write_legacy_seeds", side_effect=AssertionError("legacy extraction called"), create=True), \
             mock.patch.object(build_module, "write_entity_seed_tables", side_effect=AssertionError("entity migration called"), create=True), \
             mock.patch.object(build_module, "write_work_relation_tables", side_effect=AssertionError("work migration called"), create=True):
            # Structural contract: ordinary build module must not expose migration writer calls in build().
            names = set(build_module.build.__code__.co_names)
            self.assertNotIn("write_legacy_seeds", names)
            self.assertNotIn("write_entity_seed_tables", names)
            self.assertNotIn("write_work_relation_tables", names)

    def test_manifest_is_derived_not_canonical(self):
        from scripts.library_v5.audit import manifest_output_path

        root = Path("/repo")
        self.assertEqual(manifest_output_path(root), root / "data" / "derived" / "library_manifest.json")


if __name__ == "__main__":
    unittest.main()
