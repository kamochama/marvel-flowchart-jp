from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def rows(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class FirstStepsContinuityAuditTests(unittest.TestCase):
    def test_legacy_mcu_continuity_membership_is_superseded(self) -> None:
        fact_id = "work-continuity-the-fantastic-four-first-steps-2025-continuity-mcu"
        row = next(row for row in rows("work_continuities.csv") if row["work_continuity_id"] == fact_id)
        self.assertEqual(row["verification_status"], "superseded")

    def test_earth_828_is_verified_setting_universe(self) -> None:
        continuity = next(row for row in rows("continuities.csv") if row["continuity_id"] == "continuity-earth-828")
        self.assertEqual(continuity["verification_status"], "source_verified")
        self.assertEqual(continuity["certainty"], "confirmed")

        fact_id = "work-continuity-the-fantastic-four-first-steps-2025-continuity-earth-828"
        membership = next(row for row in rows("work_continuities.csv") if row["work_continuity_id"] == fact_id)
        self.assertEqual(membership["relation_to_continuity"], "setting_universe")
        self.assertEqual(membership["verification_status"], "source_verified")
        self.assertEqual(membership["certainty"], "confirmed")

        qualifying = {
            evidence["fact_id"]
            for evidence in rows("evidence.csv")
            if evidence["evidence_role"] in {"primary", "supporting"}
        }
        self.assertIn("continuity-earth-828", qualifying)
        self.assertIn(fact_id, qualifying)


if __name__ == "__main__":
    unittest.main()
