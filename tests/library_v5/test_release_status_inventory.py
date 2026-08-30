import csv
import random
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
        self.assertEqual({row["disposition"] for row in rows}, {"promote", "defer", "conflict"})
        self.assertEqual(
            sum(row["disposition"] == "promote" for row in rows),
            21,
        )
        self.assertEqual(
            sum(row["disposition"] == "defer" for row in rows),
            246,
        )
        self.assertEqual(
            sum(row["disposition"] == "conflict" for row in rows),
            2,
        )
        doomsday = next(
            row
            for row in rows
            if row["fact_id"] == "release-avengers-doomsday-2026-12-18-primary"
        )
        self.assertIn("doomsday", doomsday["source_candidates"])
        self.assertIn("marvel-jp-titlelist", doomsday["source_candidates"])
        conflicts = {
            row["fact_id"]
            for row in rows
            if row["disposition"] == "conflict"
        }
        self.assertEqual(
            conflicts,
            {
                "release-your-friendly-neighborhood-spider-man-s2-2026-primary",
                "production-status-wonder-man-s2-tba-snapshot-2026-08-28",
            },
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
            shuffled = list(rows)
            random.Random(7).shuffle(shuffled)
            write_inventory(shuffled, output)
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))
            self.assertEqual(len(written), 269)
            self.assertEqual(written[0]["fact_id"], rows[0]["fact_id"])
            report = Path(tmp) / "inventory.md"
            write_markdown_report(shuffled, report)
            markdown = report.read_text(encoding="utf-8")
        self.assertIn("release facts: 138", markdown)
        self.assertIn("production-status facts: 131", markdown)
        self.assertIn("promote dispositions: 21", markdown)
        self.assertIn("conflict dispositions: 2", markdown)
        self.assertIn("production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28", markdown)

    def test_inventory_writers_reject_canonical_outputs(self):
        from scripts.library_v5.release_status_inventory import write_inventory

        with self.assertRaises(ValueError):
            write_inventory([], ROOT / "data/library/releases.csv")
        with self.assertRaises(ValueError):
            write_inventory([], ROOT / "data/content_audit/reviews.csv")


if __name__ == "__main__":
    unittest.main()

