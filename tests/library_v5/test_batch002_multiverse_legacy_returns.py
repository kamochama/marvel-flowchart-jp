from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def rows(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def relation(fact_id: str) -> dict[str, str]:
    return next(row for row in rows("work_relations.csv") if row["work_relation_id"] == fact_id)


class MultiverseLegacyReturnAuditTests(unittest.TestCase):
    def test_morbius_vulture_is_verified_same_mcu_toomes_crossing(self) -> None:
        fact_id = "work-relation-spider-man-no-way-home-2021-morbius-2022-crossover"
        row = relation(fact_id)
        self.assertEqual(row["relation_kind"], "crossover")
        self.assertEqual(row["directness"], "direct")
        self.assertEqual(row["continuity_scope"], "multiverse")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")

    def test_deadpool_wolverine_legacy_cameos_do_not_claim_exact_old_film_continuity(self) -> None:
        for fact_id in (
            "work-relation-blade-trinity-2004-deadpool-wolverine-2024-crossover",
            "work-relation-elektra-2005-deadpool-wolverine-2024-crossover",
            "work-relation-fantastic-four-rise-of-the-silver-surfer-2007-deadpool-wolverine-2024-crossover",
        ):
            row = relation(fact_id)
            self.assertEqual(row["directness"], "indirect")
            self.assertEqual(row["continuity_scope"], "uncertain_return_continuity")
            self.assertEqual(row["certainty"], "probable")
            self.assertEqual(row["verification_status"], "legacy_seed")

    def test_inhumans_black_bolt_to_mom_is_verified_variant_callback_not_identity(self) -> None:
        fact_id = "work-relation-inhumans-2017-doctor-strange-in-the-multiverse-of-madness-2022-variant-callback"
        row = relation(fact_id)
        self.assertEqual(row["relation_kind"], "variant_callback")
        self.assertEqual(row["relation_scope"], "variant_meta")
        self.assertEqual(row["directness"], "proxy")
        self.assertEqual(row["continuity_scope"], "variant")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")

    def test_new_source_verified_relations_have_evidence(self) -> None:
        expected = {
            "work-relation-spider-man-no-way-home-2021-morbius-2022-crossover",
            "work-relation-inhumans-2017-doctor-strange-in-the-multiverse-of-madness-2022-variant-callback",
        }
        qualifying = {
            row["fact_id"] for row in rows("evidence.csv")
            if row["evidence_role"] in {"primary", "supporting"}
        }
        self.assertTrue(expected <= qualifying)


if __name__ == "__main__":
    unittest.main()
