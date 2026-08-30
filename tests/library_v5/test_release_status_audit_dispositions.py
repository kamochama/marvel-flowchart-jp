import csv
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
APPLIED = ROOT / "data/content_audit/applied/2026-08-30-release-status-audit-dispositions.json"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusAuditDispositionTests(unittest.TestCase):
    def test_all_release_status_facts_have_a_strict_disposition(self):
        inventory = _rows("data/content_audit/release_status_inventory.csv")
        self.assertEqual(len(inventory), 269)
        self.assertEqual({row["disposition"] for row in inventory}, {"promote", "defer", "conflict"})
        self.assertEqual(sum(row["disposition"] == "promote" for row in inventory), 27)
        self.assertEqual(sum(row["disposition"] == "defer" for row in inventory), 240)
        self.assertEqual(sum(row["disposition"] == "conflict" for row in inventory), 2)
        self.assertEqual(
            {row["fact_id"] for row in inventory if row["disposition"] == "conflict"},
            {
                "release-your-friendly-neighborhood-spider-man-s2-2026-primary",
                "production-status-wonder-man-s2-tba-snapshot-2026-08-28",
            },
        )
        for row in inventory:
            self.assertTrue(row["disposition_reason"])
            self.assertTrue(row["next_action"])

    def test_applied_record_matches_inventory_and_verification_boundaries(self):
        record = json.loads(APPLIED.read_text(encoding="utf-8"))
        self.assertEqual(record["batch_id"], "2026-08-30-release-status-audit-dispositions")
        self.assertEqual(record["fact_count"], 269)
        self.assertEqual(record["disposition_counts"], {"promote": 27, "defer": 240, "conflict": 2})
        inventory = _rows("data/content_audit/release_status_inventory.csv")
        self.assertEqual(set(record["promoted_fact_ids"]), {row["fact_id"] for row in inventory if row["disposition"] == "promote"})
        self.assertEqual(set(record["conflict_fact_ids"]), {row["fact_id"] for row in inventory if row["disposition"] == "conflict"})
        self.assertEqual(record["promoted_fact_count"], 27)
        self.assertEqual(record["deferred_fact_count"], 240)
        self.assertEqual(record["conflict_fact_count"], 2)
        self.assertIn("legacy_seed", record["verification_boundary"])
        self.assertIn("evidence", record["verification_boundary"])
        self.assertIn("review", record["verification_boundary"])


if __name__ == "__main__":
    unittest.main()

