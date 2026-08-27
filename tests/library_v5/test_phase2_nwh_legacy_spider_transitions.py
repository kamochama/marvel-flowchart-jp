from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
NWH = "spider-man-no-way-home-2021"
EARTH_616 = "continuity-earth-616"
RAIMI_CONTINUITY = "continuity-spider-man-raimi"
WEBB_CONTINUITY = "continuity-spider-man-amazing"
RAIMI_ENTITY = "entity-x-f162d4b4b2"
WEBB_ENTITY = "entity-x-f8b1d323de"
RAIMI_EVENT = "event-nwh-raimi-peter-arrival"
WEBB_EVENT = "event-nwh-webb-peter-arrival"
RAIMI_OCCURRENCE = "event-occurrence-nwh-raimi-peter-arrival"
WEBB_OCCURRENCE = "event-occurrence-nwh-webb-peter-arrival"
RAIMI_PARTICIPANT = "transition-participant-nwh-raimi-peter"
WEBB_PARTICIPANT = "transition-participant-nwh-webb-peter"


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class NoWayHomeLegacySpiderTransitionTests(unittest.TestCase):
    def test_two_separate_verified_transition_events_exist(self) -> None:
        events = {row["event_id"]: row for row in _read("events.csv")}
        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}

        expected = {
            RAIMI_EVENT: RAIMI_CONTINUITY,
            WEBB_EVENT: WEBB_CONTINUITY,
        }
        for event_id, source_continuity in expected.items():
            event = events[event_id]
            self.assertEqual(event["event_kind"], "multiverse_transition")
            self.assertEqual(event["primary_continuity_id"], EARTH_616)
            self.assertEqual(event["verification_status"], "source_verified")

            transition = transitions[event_id]
            self.assertEqual(transition["source_continuity_id"], source_continuity)
            self.assertEqual(transition["destination_continuity_id"], EARTH_616)
            self.assertEqual(transition["transition_kind"], "spell_displacement")
            self.assertEqual(transition["direction_certainty"], "confirmed")
            self.assertEqual(transition["verification_status"], "source_verified")

    def test_each_arrival_is_depicted_in_no_way_home(self) -> None:
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        for occurrence_id, event_id in (
            (RAIMI_OCCURRENCE, RAIMI_EVENT),
            (WEBB_OCCURRENCE, WEBB_EVENT),
        ):
            row = occurrences[occurrence_id]
            self.assertEqual(row["event_id"], event_id)
            self.assertEqual(row["work_id"], NWH)
            self.assertEqual(row["occurrence_kind"], "depicted")
            self.assertEqual(row["verification_status"], "source_verified")

    def test_each_transition_has_the_specific_legacy_peter_as_traveler(self) -> None:
        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}
        expected = {
            RAIMI_PARTICIPANT: (RAIMI_EVENT, RAIMI_ENTITY),
            WEBB_PARTICIPANT: (WEBB_EVENT, WEBB_ENTITY),
        }
        for participant_id, (event_id, entity_id) in expected.items():
            row = participants[participant_id]
            self.assertEqual(row["transition_id"], event_id)
            self.assertEqual(row["entity_id"], entity_id)
            self.assertEqual(row["participant_role"], "traveler")
            self.assertEqual(row["identity_certainty"], "confirmed")
            self.assertEqual(row["verification_status"], "source_verified")
            self.assertIn("not MCU Peter", row["notes"])

    def test_crossing_view_keeps_raimi_webb_and_mcu_peter_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT transition_id,source_continuity_id,destination_continuity_id,
                       work_id,participant_entity_id,participant_role,identity_certainty
                FROM v_multiverse_crossings
                WHERE transition_id IN (?,?)
                ORDER BY transition_id
                """,
                (RAIMI_EVENT, WEBB_EVENT),
            ).fetchall()
            connection.close()

        self.assertEqual(len(rows), 2)
        by_id = {row[0]: row for row in rows}
        self.assertEqual(by_id[RAIMI_EVENT][1:], (RAIMI_CONTINUITY, EARTH_616, NWH, RAIMI_ENTITY, "traveler", "confirmed"))
        self.assertEqual(by_id[WEBB_EVENT][1:], (WEBB_CONTINUITY, EARTH_616, NWH, WEBB_ENTITY, "traveler", "confirmed"))
        self.assertNotEqual(RAIMI_ENTITY, "entity-mcu")
        self.assertNotEqual(WEBB_ENTITY, "entity-mcu")
        self.assertNotEqual(RAIMI_ENTITY, WEBB_ENTITY)

    def test_transition_reasons_are_added_only_to_existing_legacy_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT source_work_id,target_work_id,transition_id
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                  AND transition_id IN (?,?)
                ORDER BY transition_id
                """,
                (RAIMI_EVENT, WEBB_EVENT),
            ).fetchall()
            connection.close()

        self.assertEqual({tuple(row) for row in rows}, {
            ("spider-man-3-2007", NWH, RAIMI_EVENT),
            ("the-amazing-spider-man-2-2014", NWH, WEBB_EVENT),
        })

    def test_existing_explicit_relations_are_retained_during_parity_stage(self) -> None:
        active = {
            row["work_relation_id"]: row
            for row in _read("work_relations.csv")
            if row["verification_status"] != "superseded"
        }
        self.assertIn("work-relation-spider-man-3-2007-spider-man-no-way-home-2021-crossover", active)
        self.assertIn("work-relation-the-amazing-spider-man-2-2014-spider-man-no-way-home-2021-crossover", active)


if __name__ == "__main__":
    unittest.main()
