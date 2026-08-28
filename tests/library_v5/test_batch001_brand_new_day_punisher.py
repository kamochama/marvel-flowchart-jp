from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def rows(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class BrandNewDayPunisherAuditTests(unittest.TestCase):
    def test_frank_castle_appearance_is_source_verified(self) -> None:
        fact_id = "appearance-spider-man-brand-new-day-2026-07-31-entity-x-797ce92fcd"
        row = next(row for row in rows("appearances.csv") if row["appearance_id"] == fact_id)
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["appearance_kind"], "onscreen")

    def test_jon_bernthal_portrayal_is_source_verified_with_evidence(self) -> None:
        fact_id = "portrayal-spider-man-brand-new-day-2026-07-31-person-jon-bernthal-entity-x-797ce92fcd"
        row = next(row for row in rows("portrayals.csv") if row["portrayal_id"] == fact_id)
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["portrayal_kind"], "same_character")

        qualifying = {
            evidence["fact_id"]
            for evidence in rows("evidence.csv")
            if evidence["evidence_role"] in {"primary", "supporting"}
        }
        self.assertIn(fact_id, qualifying)


if __name__ == "__main__":
    unittest.main()
