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


class MultiverseRelationAuditTests(unittest.TestCase):
    def test_no_way_home_legacy_spider_men_are_verified_cross_universe_arrivals(self) -> None:
        transitions = {row["transition_id"]: row for row in rows("multiverse_transitions.csv")}
        participants = {row["transition_id"]: row for row in rows("transition_participants.csv")}
        expected = {
            "event-nwh-raimi-peter-arrival": ("continuity-spider-man-raimi", "entity-x-f162d4b4b2"),
            "event-nwh-webb-peter-arrival": ("continuity-spider-man-amazing", "entity-x-f8b1d323de"),
        }
        for transition_id, (source_continuity, entity_id) in expected.items():
            transition = transitions[transition_id]
            self.assertEqual(transition["source_continuity_id"], source_continuity)
            self.assertEqual(transition["destination_continuity_id"], "continuity-earth-616")
            self.assertEqual(transition["transition_kind"], "spell_displacement")
            self.assertEqual(transition["direction_certainty"], "confirmed")
            self.assertEqual(transition["verification_status"], "source_verified")
            participant = participants[transition_id]
            self.assertEqual(participant["entity_id"], entity_id)
            self.assertEqual(participant["participant_role"], "traveler")
            self.assertEqual(participant["identity_certainty"], "confirmed")
            self.assertEqual(participant["verification_status"], "source_verified")

        for fact_id in (
            "work-relation-spider-man-3-2007-spider-man-no-way-home-2021-crossover",
            "work-relation-the-amazing-spider-man-2-2014-spider-man-no-way-home-2021-crossover",
        ):
            self.assertEqual(relation(fact_id)["verification_status"], "superseded")

    def test_venom_crossing_into_no_way_home_is_verified_as_first_class_round_trip(self) -> None:
        transitions = {row["transition_id"]: row for row in rows("multiverse_transitions.csv")}
        participants = {row["transition_id"]: row for row in rows("transition_participants.csv")}
        expected = {
            "event-ltbc-eddie-brock-earth616-arrival": ("continuity-ssu", "continuity-earth-616"),
            "event-nwh-eddie-brock-ssu-return": ("continuity-earth-616", "continuity-ssu"),
        }
        for transition_id, (source_continuity, destination_continuity) in expected.items():
            transition = transitions[transition_id]
            self.assertEqual(transition["source_continuity_id"], source_continuity)
            self.assertEqual(transition["destination_continuity_id"], destination_continuity)
            self.assertEqual(transition["transition_kind"], "unknown")
            self.assertEqual(transition["direction_certainty"], "confirmed")
            self.assertEqual(transition["verification_status"], "source_verified")
            participant = participants[transition_id]
            self.assertEqual(participant["entity_id"], "entity-eddie-brock-sony")
            self.assertEqual(participant["participant_role"], "traveler")
            self.assertEqual(participant["identity_certainty"], "confirmed")
            self.assertEqual(participant["verification_status"], "source_verified")

        proxy = relation("work-relation-venom-let-there-be-carnage-2021-spider-man-no-way-home-2021-crossover")
        self.assertEqual(proxy["directness"], "direct")
        self.assertEqual(proxy["continuity_scope"], "multiverse")
        self.assertEqual(proxy["certainty"], "confirmed")
        self.assertEqual(proxy["verification_status"], "superseded")

    def test_no_way_home_to_multiverse_of_madness_is_verified_fallout(self) -> None:
        row = relation("work-relation-spider-man-no-way-home-2021-doctor-strange-in-the-multiverse-of-madness-2022-crossover")
        self.assertEqual(row["directness"], "direct")
        self.assertEqual(row["continuity_scope"], "multiverse")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")

    def test_loki_tva_to_deadpool_wolverine_is_direct_multiverse_connection(self) -> None:
        row = relation("work-relation-loki-s2-2023-deadpool-wolverine-2024-crossover")
        self.assertEqual(row["directness"], "direct")
        self.assertEqual(row["continuity_scope"], "multiverse")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")

    def test_logan_death_is_explicit_story_premise_for_deadpool_wolverine(self) -> None:
        row = relation("work-relation-logan-2017-deadpool-wolverine-2024-story-link")
        self.assertEqual(row["relation_kind"], "story_link")
        self.assertEqual(row["directness"], "direct")
        self.assertEqual(row["continuity_scope"], "same_or_intended")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertIn("different-universe", row["notes"])

    def test_deadpool_wolverine_to_doomsday_is_not_claimed_as_confirmed_physical_crossing(self) -> None:
        row = relation("work-relation-deadpool-wolverine-2024-avengers-doomsday-2026-12-18-crossover")
        self.assertEqual(row["directness"], "indirect")
        self.assertEqual(row["continuity_scope"], "uncertain_return_continuity")
        self.assertEqual(row["certainty"], "probable")
        self.assertEqual(row["verification_status"], "legacy_seed")

    def test_the_marvels_to_doomsday_does_not_equate_alternate_xmen_universe_with_returning_cast(self) -> None:
        row = relation("work-relation-the-marvels-2023-avengers-doomsday-2026-12-18-story-link")
        self.assertEqual(row["directness"], "indirect")
        self.assertEqual(row["continuity_scope"], "uncertain_return_continuity")
        self.assertEqual(row["certainty"], "probable")
        self.assertEqual(row["verification_status"], "legacy_seed")

    def test_verified_promotions_have_qualifying_evidence(self) -> None:
        expected = {
            "work-relation-spider-man-3-2007-spider-man-no-way-home-2021-crossover",
            "work-relation-the-amazing-spider-man-2-2014-spider-man-no-way-home-2021-crossover",
            "work-relation-venom-let-there-be-carnage-2021-spider-man-no-way-home-2021-crossover",
            "work-relation-spider-man-no-way-home-2021-doctor-strange-in-the-multiverse-of-madness-2022-crossover",
            "work-relation-loki-s2-2023-deadpool-wolverine-2024-crossover",
            "work-relation-logan-2017-deadpool-wolverine-2024-story-link",
        }
        qualifying = {
            row["fact_id"]
            for row in rows("evidence.csv")
            if row["evidence_role"] in {"primary", "supporting"}
        }
        self.assertTrue(expected <= qualifying)


if __name__ == "__main__":
    unittest.main()
