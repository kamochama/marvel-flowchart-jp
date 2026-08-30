from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.apply_review_patch import ALLOWED_PATHS, apply_patch


class ReviewPatchApplierTests(unittest.TestCase):
    def _repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        path = root / "data/library/work_relations.csv"
        path.parent.mkdir(parents=True)
        path.write_text("work_relation_id,certainty,verification_status\nr1,probable,legacy_seed\n", encoding="utf-8")
        return root

    def test_update_and_insert_are_explicit_and_deterministic(self) -> None:
        root = self._repo()
        patch = root / "patch.json"
        patch.write_text(json.dumps({
            "patch_id": "p1",
            "operations": [
                {"table": "work_relations.csv", "action": "update", "key_column": "work_relation_id", "key": "r1", "set": {"certainty": "confirmed"}},
                {"table": "work_relations.csv", "action": "insert", "key_column": "work_relation_id", "key": "r2", "values": {"work_relation_id": "r2", "certainty": "confirmed", "verification_status": "source_verified"}},
            ],
        }), encoding="utf-8")
        apply_patch(root, patch)
        text = (root / "data/library/work_relations.csv").read_text(encoding="utf-8")
        self.assertEqual(text, "work_relation_id,certainty,verification_status\nr1,confirmed,legacy_seed\nr2,confirmed,source_verified\n")

    def test_missing_or_duplicate_keys_are_rejected(self) -> None:
        root = self._repo()
        patch = root / "patch.json"
        patch.write_text(json.dumps({"patch_id": "p", "operations": [
            {"table": "work_relations.csv", "action": "update", "key_column": "work_relation_id", "key": "missing", "set": {"certainty": "confirmed"}}
        ]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            apply_patch(root, patch)

    def test_unapproved_table_is_rejected(self) -> None:
        root = self._repo()
        patch = root / "patch.json"
        patch.write_text(json.dumps({"patch_id": "p", "operations": [
            {"table": "index.html", "action": "update", "key_column": "x", "key": "y", "set": {"x": "z"}}
        ]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            apply_patch(root, patch)

    def test_release_status_tables_are_patchable(self) -> None:
        self.assertEqual(ALLOWED_PATHS["releases.csv"], Path("data/library/releases.csv"))
        self.assertEqual(
            ALLOWED_PATHS["production_status_assertions.csv"],
            Path("data/library/production_status_assertions.csv"),
        )


if __name__ == "__main__":
    unittest.main()
