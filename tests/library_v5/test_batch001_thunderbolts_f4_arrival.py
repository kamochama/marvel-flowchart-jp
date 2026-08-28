from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def rows(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ThunderboltsFantasticFourArrivalAuditTests(unittest.TestCase):
    def test_thunderbolts_postcredit_establishes_multiverse_crossover(self) -> None:
        fact_id = "work-relation-thunderbolts-new-avengers-2025-the-fantastic-four-first-steps-2025-crossover"
        row = next(row for row in rows("work_relations.csv") if row["work_relation_id"] == fact_id)
        self.assertEqual(row["relation_kind"], "crossover")
        self.assertEqual(row["relation_scope"], "crossover")
        self.assertEqual(row["directness"], "direct")
        self.assertEqual(row["continuity_scope"], "multiverse")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertIn("Earth-616", row["notes"])
        self.assertIn("post-credit", row["notes"].lower())

        qualifying = {
            evidence["fact_id"]
            for evidence in rows("evidence.csv")
            if evidence["evidence_role"] in {"primary", "supporting"}
        }
        self.assertIn(fact_id, qualifying)


if __name__ == "__main__":
    unittest.main()
