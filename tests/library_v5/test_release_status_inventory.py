import csv
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ReleaseStatusInventoryTests(unittest.TestCase):
    def test_inventory_contains_every_release_and_status_fact(self):
        from scripts.library_v5.release_status_inventory import build_inventory

        rows = build_inventory(ROOT)
        self.assertEqual(len(rows), 269)
        self.assertEqual({row["fact_table"] for row in rows}, {
            "releases.csv",
            "production_status_assertions.csv",
        })
        self.assertEqual(sum(row["fact_table"] == "releases.csv" for row in rows), 138)
        self.assertEqual(
            sum(row["fact_table"] == "production_status_assertions.csv" for row in rows),
            131,
        )
        required = {
            "fact_id",
            "fact_table",
            "work_id",
            "verification_status",
            "source_candidates",
            "evidence_count",
            "review_count",
            "disposition",
        }
        self.assertTrue(required <= set(rows[0]))
        self.assertEqual({row["disposition"] for row in rows}, {"verified", "defer"})
        self.assertEqual(
            sum(row["disposition"] == "verified" for row in rows),
            10,
        )
        self.assertEqual(
            sum(row["disposition"] == "defer" for row in rows),
            259,
        )

    def test_inventory_is_stably_sorted_and_can_be_written(self):
        from scripts.library_v5.release_status_inventory import (
            build_inventory,
            write_inventory,
            write_markdown_report,
        )

        rows = build_inventory(ROOT)
        keys = [(row["fact_table"], row["fact_id"]) for row in rows]
        self.assertEqual(keys, sorted(keys))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "inventory.csv"
            write_inventory(rows, output)
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))
        self.assertEqual(len(written), 269)
        self.assertEqual(written[0]["fact_id"], rows[0]["fact_id"])
        report = Path(tmp) / "inventory.md"
        write_markdown_report(rows, report)
        markdown = report.read_text(encoding="utf-8")
        self.assertIn("release facts: 138", markdown)
        self.assertIn("production-status facts: 131", markdown)
        self.assertIn("production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28", markdown)


if __name__ == "__main__":
    unittest.main()

