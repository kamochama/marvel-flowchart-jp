from __future__ import annotations

import inspect
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.library_v5.build as build_module
from scripts.library_v5.canonical_guard import canonical_hashes


ROOT = Path(__file__).resolve().parents[2]


class DbBackedBuildIntegrationTests(unittest.TestCase):
    def _repo_fixture(self, temp: Path) -> Path:
        repo = temp / "repo"
        shutil.copytree(ROOT / "data", repo / "data")
        return repo

    def test_ordinary_build_no_longer_calls_legacy_edge_writer(self) -> None:
        source = inspect.getsource(build_module.build)
        self.assertNotIn("write_derived_edges", source)
        self.assertIn("compile_database", source)
        self.assertIn("export_work_graph", source)

    def test_ordinary_build_emits_db_and_is_logically_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_fixture(Path(tmp))
            before = canonical_hashes(repo)
            reviews_before = (repo / "data/content_audit/reviews.csv").read_bytes()

            first = build_module.build(repo)
            first_db_manifest = (repo / "data/derived/db/library_db_manifest.json").read_bytes()
            first_reasons = (repo / "data/derived/work_pair_reasons.csv").read_bytes()
            first_edges = (repo / "data/derived/work_edges_all.csv").read_bytes()

            second = build_module.build(repo)
            second_db_manifest = (repo / "data/derived/db/library_db_manifest.json").read_bytes()
            second_reasons = (repo / "data/derived/work_pair_reasons.csv").read_bytes()
            second_edges = (repo / "data/derived/work_edges_all.csv").read_bytes()

            self.assertTrue(first["audit_ok"])
            self.assertTrue(second["audit_ok"])
            self.assertIn("database", first)
            self.assertEqual(first["derived_edges"], second["derived_edges"])
            self.assertTrue((repo / "data/derived/db/marvel.sqlite").exists())
            self.assertEqual(first_db_manifest, second_db_manifest)
            self.assertEqual(first_reasons, second_reasons)
            self.assertEqual(first_edges, second_edges)
            self.assertEqual(before, canonical_hashes(repo))
            self.assertEqual(reviews_before, (repo / "data/content_audit/reviews.csv").read_bytes())

    def test_ordinary_build_rejects_persistent_review_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_fixture(Path(tmp))
            original = build_module.write_content_audit_outputs

            def mutate_reviews(repo_root: Path):
                reviews = repo_root / "data/content_audit/reviews.csv"
                reviews.write_bytes(reviews.read_bytes() + b"\n")
                return original(repo_root)

            with mock.patch.object(build_module, "write_content_audit_outputs", side_effect=mutate_reviews):
                with self.assertRaisesRegex(RuntimeError, "protected_input_mutated"):
                    build_module.build(repo)


if __name__ == "__main__":
    unittest.main()
