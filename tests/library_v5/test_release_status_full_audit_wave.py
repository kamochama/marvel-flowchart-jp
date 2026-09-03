import csv
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusFullAuditWaveTests(unittest.TestCase):
    def test_every_promoted_fact_has_evidence_and_review(self):
        inventory = _rows("data/content_audit/release_status_inventory.csv")
        promoted = [row for row in inventory if row["disposition"] == "promote"]
        self.assertEqual(len(promoted), 27)
        self.assertTrue(all(int(row["evidence_count"]) >= 1 for row in promoted))
        self.assertTrue(all(int(row["review_count"]) >= 1 for row in promoted))
        self.assertTrue(all(row["verification_status"] == "source_verified" for row in promoted))

    def test_conflicts_and_deferred_facts_are_not_promoted(self):
        inventory = _rows("data/content_audit/release_status_inventory.csv")
        for row in inventory:
            if row["disposition"] in {"defer", "conflict"}:
                self.assertNotEqual(row["verification_status"], "source_verified")

    def test_release_status_audit_does_not_change_graph_export_shape(self):
        export = json.loads((ROOT / "data/derived/flowchart.json").read_text(encoding="utf-8"))
        self.assertEqual(len(export["nodes"]), 131)
        self.assertEqual(len(export["edges"]), 355)
        self.assertEqual(len(export["reasons"]), 562)


if __name__ == "__main__":
    unittest.main()

