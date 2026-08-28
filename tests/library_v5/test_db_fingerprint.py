from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database
from scripts.library_v5.db_fingerprint import logical_fingerprint, write_db_manifest


ROOT = Path(__file__).resolve().parents[2]


class LibraryDbFingerprintTests(unittest.TestCase):
    def test_two_compiles_have_same_logical_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_a = compile_database(ROOT, temp / "a.sqlite").db_path
            db_b = compile_database(ROOT, temp / "b.sqlite").db_path
            first = logical_fingerprint(db_a, repo_root=ROOT)
            second = logical_fingerprint(db_b, repo_root=ROOT)
            self.assertEqual(first["equivalence"], second["equivalence"])
            self.assertEqual(first["tables"], second["tables"])
            self.assertEqual(first["views"], second["views"])

    def test_fingerprint_contains_schema_tables_views_and_canonical_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            fingerprint = logical_fingerprint(db_path, repo_root=ROOT)
            self.assertEqual(fingerprint["db_schema_version"], "1.2-normalized-releases-status")
            self.assertIn("works", fingerprint["tables"])
            self.assertIn("releases", fingerprint["tables"])
            self.assertIn("production_status_assertions", fingerprint["tables"])
            self.assertIn("reviews", fingerprint["tables"])
            self.assertIn("events", fingerprint["tables"])
            self.assertIn("multiverse_transitions", fingerprint["tables"])
            self.assertIn("v_work_connection_reasons", fingerprint["views"])
            self.assertIn("data/library/works.csv", fingerprint["canonical_inputs"])
            self.assertEqual(len(fingerprint["equivalence"]), 64)

    def test_manifest_writer_is_deterministic_for_same_db_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
            out = temp / "library_db_manifest.json"
            first_path = write_db_manifest(ROOT, db_path, output_path=out)
            first = first_path.read_bytes()
            second_path = write_db_manifest(ROOT, db_path, output_path=out)
            second = second_path.read_bytes()
            self.assertEqual(first, second)
            payload = json.loads(first.decode("utf-8"))
            self.assertEqual(payload["equivalence"], logical_fingerprint(db_path, repo_root=ROOT)["equivalence"])

    def test_fingerprint_changes_when_release_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            shutil.copytree(ROOT / "data", root / "data")
            before_db_path = compile_database(root, Path(tmp) / "before.sqlite").db_path
            before = logical_fingerprint(before_db_path, repo_root=root)

            releases_path = root / "data/library/releases.csv"
            original = releases_path.read_text(encoding="utf-8")
            releases_path.write_text(original.replace("legacy seed; evidence-backed release audit remains pending.", "changed content", 1), encoding="utf-8")

            after_db_path = compile_database(root, Path(tmp) / "after.sqlite").db_path
            after = logical_fingerprint(after_db_path, repo_root=root)
            self.assertNotEqual(
                before["tables"]["releases"]["content_sha256"],
                after["tables"]["releases"]["content_sha256"],
            )
            self.assertNotEqual(before["equivalence"], after["equivalence"])


if __name__ == "__main__":
    unittest.main()
