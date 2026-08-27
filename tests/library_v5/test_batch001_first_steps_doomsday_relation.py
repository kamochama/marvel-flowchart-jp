from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def rows(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class FirstStepsDoomsdayRelationAuditTests(unittest.TestCase):
    def test_direct_lead_in_is_source_verified(self) -> None:
        fact_id = "work-relation-the-fantastic-four-first-steps-2025-avengers-doomsday-2026-12-18-lead-in"
        row = next(row for row in rows("work_relations.csv") if row["work_relation_id"] == fact_id)
        self.assertEqual(row["relation_kind"], "lead_in")
        self.assertEqual(row["directness"], "direct")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")

        qualifying = {
            evidence["fact_id"]
            for evidence in rows("evidence.csv")
            if evidence["evidence_role"] in {"primary", "supporting"}
        }
        self.assertIn(fact_id, qualifying)


if __name__ == "__main__":
    unittest.main()
