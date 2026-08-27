from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_export import export_work_graph


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
EVENT_ID = "event-thunderbolts-f4-excelsior-arrival"
OCCURRENCE_ID = "event-occurrence-thunderbolts-f4-excelsior-arrival"
PARTICIPANT_ID = "transition-participant-thunderbolts-f4-excelsior"
SHIP_ID = "entity-fantastic-four-excelsior"
EARTH_616 = "continuity-earth-616"
EARTH_828 = "continuity-earth-828"
THUNDERBOLTS = "thunderbolts-new-avengers-2025"
FIRST_STEPS = "the-fantastic-four-first-steps-2025"
DOOMSDAY = "avengers-doomsday-2026-12-18"


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ThunderboltsF4TransitionMigrationTests(unittest.TestCase):
    def test_earth_616_is_a_verified_universe_not_a_legacy_mcu_group_alias(self) -> None:
        rows = {row["continuity_id"]: row for row in _read("continuities.csv")}
        self.assertIn(EARTH_616, rows)
        row = rows[EARTH_616]
        self.assertEqual(row["continuity_kind"], "universe")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertIn("MCU", row["notes"])
        self.assertNotEqual(EARTH_616, "continuity-mcu")

    def test_event_occurrence_and_transition_are_source_verified(self) -> None:
        events = {row["event_id"]: row for row in _read("events.csv")}
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}

        event = events[EVENT_ID]
        self.assertEqual(event["event_kind"], "multiverse_transition")
        self.assertEqual(event["primary_continuity_id"], EARTH_616)
        self.assertEqual(event["verification_status"], "source_verified")

        occurrence = occurrences[OCCURRENCE_ID]
        self.assertEqual(occurrence["event_id"], EVENT_ID)
        self.assertEqual(occurrence["work_id"], THUNDERBOLTS)
        self.assertEqual(occurrence["occurrence_kind"], "post_credit")
        self.assertEqual(occurrence["verification_status"], "source_verified")
        self.assertIn("does not assert First Steps film chronology", occurrence["notes"])

        transition = transitions[EVENT_ID]
        self.assertEqual(transition["source_continuity_id"], EARTH_828)
        self.assertEqual(transition["destination_continuity_id"], EARTH_616)
        self.assertEqual(transition["transition_kind"], "physical_crossing")
        self.assertEqual(transition["direction_certainty"], "confirmed")
        self.assertEqual(transition["verification_status"], "source_verified")

    def test_only_confirmed_ship_is_recorded_as_transition_participant(self) -> None:
        entities = {row["entity_id"]: row for row in _read("entities.csv")}
        participants = [
            row for row in _read("transition_participants.csv")
            if row["transition_id"] == EVENT_ID and row["verification_status"] != "superseded"
        ]
        self.assertEqual(len(participants), 1)
        participant = participants[0]
        self.assertEqual(participant["transition_participant_id"], PARTICIPANT_ID)
        self.assertEqual(participant["entity_id"], SHIP_ID)
        self.assertEqual(participant["participant_role"], "vehicle")
        self.assertEqual(participant["identity_certainty"], "confirmed")
        self.assertEqual(participant["verification_status"], "source_verified")
        self.assertEqual(entities[SHIP_ID]["entity_type"], "vehicle")
        self.assertIn("Excelsior", entities[SHIP_ID]["name_en"])

    def test_multiverse_crossing_view_reports_the_post_credit_ship_arrival(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            row = connection.execute(
                """
                SELECT transition_id,source_continuity_id,destination_continuity_id,
                       work_id,occurrence_kind,participant_entity_id,participant_role,
                       identity_certainty,transition_verification_status,
                       occurrence_verification_status,participant_verification_status
                FROM v_multiverse_crossings
                WHERE transition_id=?
                """,
                (EVENT_ID,),
            ).fetchone()
            connection.close()

        self.assertEqual(row, (
            EVENT_ID,
            EARTH_828,
            EARTH_616,
            THUNDERBOLTS,
            "post_credit",
            SHIP_ID,
            "vehicle",
            "confirmed",
            "source_verified",
            "source_verified",
            "source_verified",
        ))

    def test_transition_reason_coexists_with_legacy_pair_until_independent_derivation_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            kinds = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT reason_kind
                    FROM v_work_connection_reasons
                    WHERE source_work_id=? AND target_work_id=?
                    """,
                    (THUNDERBOLTS, FIRST_STEPS),
                )
            }
            connection.close()
        self.assertIn("explicit_relation", kinds)
        self.assertIn("multiverse_transition", kinds)

    def test_export_reason_explains_depiction_without_reversing_film_chronology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
            export_work_graph(db_path, temp / "derived")
            with (temp / "derived/work_pair_reasons.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

        transition = next(
            row for row in rows
            if row["source_work_id"] == THUNDERBOLTS
            and row["target_work_id"] == FIRST_STEPS
            and row["reason_kind"] == "multiverse_transition"
        )
        self.assertIn("post-credit arrival depicted in Thunderbolts*", transition["notes"])
        self.assertIn("does not assert First Steps film chronology", transition["notes"])

    def test_first_steps_to_doomsday_lead_in_is_unchanged(self) -> None:
        relation = next(
            row for row in _read("work_relations.csv")
            if row["source_work_id"] == FIRST_STEPS
            and row["target_work_id"] == DOOMSDAY
            and row["relation_kind"] == "lead_in"
        )
        self.assertEqual(relation["verification_status"], "source_verified")
        self.assertEqual(relation["directness"], "direct")
        self.assertEqual(relation["certainty"], "confirmed")


if __name__ == "__main__":
    unittest.main()
