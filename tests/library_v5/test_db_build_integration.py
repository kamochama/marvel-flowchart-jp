from __future__ import annotations

import json
import inspect
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.library_v5.build as build_module
from scripts.library_v5.canonical_guard import canonical_hashes, protected_input_hashes


ROOT = Path(__file__).resolve().parents[2]


def _normalized_graph_bytes(path: Path) -> bytes:
    """Compare graph text independent of checkout newline conversion."""
    return path.read_bytes().replace(b"\r\n", b"\n")


class DbBackedBuildIntegrationTests(unittest.TestCase):
    def _repo_fixture(self, temp: Path) -> Path:
        repo = temp / "repo"
        shutil.copytree(ROOT / "data", repo / "data")
        return repo

    def test_graph_fixture_comparison_normalizes_platform_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "graph.csv"
            graph.write_bytes(b"source,target\r\niron-man,spider-man\r\n")

            self.assertEqual(
                _normalized_graph_bytes(graph),
                b"source,target\niron-man,spider-man\n",
            )

    def test_ordinary_build_no_longer_calls_legacy_edge_writer(self) -> None:
        source = inspect.getsource(build_module.build)
        self.assertNotIn("write_derived_edges", source)
        self.assertIn("compile_database", source)
        self.assertIn("export_work_graph", source)

    def test_ordinary_build_emits_db_and_is_logically_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_fixture(Path(tmp))
            before = canonical_hashes(repo)
            protected_before = protected_input_hashes(repo)
            reviews_before = (repo / "data/content_audit/reviews.csv").read_bytes()
            legacy_graph_fixture = {
                name: _normalized_graph_bytes(repo / "data" / "derived" / name)
                for name in ("work_edges_all.csv", "prewatch_edges.csv", "story_paths.csv")
            }

            first = build_module.build(repo)
            first_db_manifest = (repo / "data/derived/db/library_db_manifest.json").read_bytes()
            first_reasons = (repo / "data/derived/work_pair_reasons.csv").read_bytes()
            first_edges = (repo / "data/derived/work_edges_all.csv").read_bytes()

            second = build_module.build(repo)
            second_db_manifest = (repo / "data/derived/db/library_db_manifest.json").read_bytes()
            second_reasons = (repo / "data/derived/work_pair_reasons.csv").read_bytes()
            second_edges = (repo / "data/derived/work_edges_all.csv").read_bytes()
            first_fingerprint = json.loads(first_db_manifest.decode("utf-8"))
            second_fingerprint = json.loads(second_db_manifest.decode("utf-8"))

            self.assertTrue(first["audit_ok"])
            self.assertTrue(second["audit_ok"])
            self.assertIn("database", first)
            self.assertEqual(first["derived_edges"], second["derived_edges"])
            self.assertGreater(first["database"]["table_counts"]["releases"], 0)
            self.assertGreater(first["database"]["table_counts"]["production_status_assertions"], 0)
            self.assertEqual(first_fingerprint["equivalence"], second_fingerprint["equivalence"])
            self.assertEqual(first_fingerprint["tables"], second_fingerprint["tables"])
            self.assertTrue((repo / "data/derived/db/marvel.sqlite").exists())
            self.assertEqual(first_db_manifest, second_db_manifest)
            self.assertEqual(first_reasons, second_reasons)
            self.assertEqual(first_edges, second_edges)
            self.assertEqual(
                legacy_graph_fixture,
                {
                    name: _normalized_graph_bytes(repo / "data" / "derived" / name)
                    for name in legacy_graph_fixture
                },
            )
            self.assertEqual(before, canonical_hashes(repo))
            self.assertEqual(protected_before, protected_input_hashes(repo))
            self.assertEqual(reviews_before, (repo / "data/content_audit/reviews.csv").read_bytes())

    def test_release_and_status_rows_do_not_change_legacy_graph_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo_fixture(Path(tmp))
            baseline = build_module.build(repo)
            baseline_graph = {
                name: _normalized_graph_bytes(repo / "data" / "derived" / name)
                for name in ("work_edges_all.csv", "prewatch_edges.csv", "story_paths.csv")
            }

            with (repo / "data/library/releases.csv").open("a", encoding="utf-8", newline="") as handle:
                handle.write(
                    "release-iron-man-2008-compatibility,iron-man-2008,ZZ,other,2099,year,unknown,unknown,legacy_seed,compatibility-only row\n"
                )
            with (repo / "data/library/production_status_assertions.csv").open("a", encoding="utf-8", newline="") as handle:
                handle.write(
                    "production-status-iron-man-2008-compatibility,iron-man-2008,unknown,2099-01-01,unknown,legacy_seed,compatibility-only row\n"
                )

            changed = build_module.build(repo)
            self.assertTrue(baseline["audit_ok"])
            self.assertTrue(changed["audit_ok"])
            self.assertEqual(
                baseline_graph,
                {
                    name: _normalized_graph_bytes(repo / "data" / "derived" / name)
                    for name in baseline_graph
                },
            )

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
