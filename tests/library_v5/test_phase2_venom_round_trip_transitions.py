from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
LTBC = "venom-let-there-be-carnage-2021"
NWH = "spider-man-no-way-home-2021"
SSU = "continuity-ssu"
EARTH_616 = "continuity-earth-616"
EDDIE = "entity-eddie-brock-sony"
LTBC_APPEARANCE = "appearance-venom-let-there-be-carnage-2021-entity-eddie-brock-sony"
NWH_APPEARANCE = "appearance-spider-man-no-way-home-2021-entity-eddie-brock-sony"
ARRIVAL_EVENT = "event-ltbc-eddie-brock-earth616-arrival"
RETURN_EVENT = "event-nwh-eddie-brock-ssu-return"
ARRIVAL_OCCURRENCE = "event-occurrence-ltbc-eddie-brock-earth616-arrival"
RETURN_OCCURRENCE = "event-occurrence-nwh-eddie-brock-ssu-return"
ARRIVAL_PARTICIPANT = "transition-participant-ltbc-eddie-brock"
RETURN_PARTICIPANT = "transition-participant-nwh-eddie-brock-return"
PROXY_RELATION = "work-relation-venom-let-there-be-carnage-2021-spider-man-no-way-home-2021-crossover"


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("rows required")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fixture_with_proxy_superseded(root: Path) -> Path:
    shutil.copytree(ROOT / "data" / "library", root / "data" / "library")
    reviews = root / "data" / "content_audit" / "reviews.csv"
    reviews.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data" / "content_audit" / "reviews.csv", reviews)

    relations_path = root / "data" / "library" / "work_relations.csv"
    with relations_path.open("r", encoding="utf-8-sig", newline="") as handle:
        relations = list(csv.DictReader(handle))
    for row in relations:
        if row["work_relation_id"] == PROXY_RELATION:
            row["verification_status"] = "superseded"
    _write(relations_path, relations)
    return root


class VenomRoundTripTransitionTests(unittest.TestCase):
    def test_eddie_brock_is_distinct_entity_with_verified_ltbc_and_nwh_appearances(self) -> None:
        entities = {row["entity_id"]: row for row in _read("entities.csv")}
        appearances = {row["appearance_id"]: row for row in _read("appearances.csv")}

        self.assertEqual(entities[EDDIE]["name_en"], "Eddie Brock")
        self.assertEqual(entities[EDDIE]["entity_type"], "character")

        expected = {
            LTBC_APPEARANCE: (LTBC, "onscreen"),
            NWH_APPEARANCE: (NWH, "post_credit"),
        }
        for appearance_id, (work_id, appearance_kind) in expected.items():
            row = appearances[appearance_id]
            self.assertEqual(row["work_id"], work_id)
            self.assertEqual(row["entity_id"], EDDIE)
            self.assertEqual(row["appearance_kind"], appearance_kind)
            self.assertEqual(row["certainty"], "confirmed")
            self.assertEqual(row["verification_status"], "source_verified")

    def test_two_verified_events_model_the_round_trip_without_inventing_ssu_earth_number(self) -> None:
        events = {row["event_id"]: row for row in _read("events.csv")}
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}
        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}

        expected = {
            ARRIVAL_EVENT: (SSU, EARTH_616, ARRIVAL_OCCURRENCE, LTBC, ARRIVAL_PARTICIPANT),
            RETURN_EVENT: (EARTH_616, SSU, RETURN_OCCURRENCE, NWH, RETURN_PARTICIPANT),
        }
        for event_id, (source, destination, occurrence_id, work_id, participant_id) in expected.items():
            event = events[event_id]
            self.assertEqual(event["event_kind"], "multiverse_transition")
            self.assertEqual(event["primary_continuity_id"], destination)
            self.assertEqual(event["certainty"], "confirmed")
            self.assertEqual(event["verification_status"], "source_verified")

            transition = transitions[event_id]
            self.assertEqual(transition["source_continuity_id"], source)
            self.assertEqual(transition["destination_continuity_id"], destination)
            self.assertEqual(transition["transition_kind"], "unknown")
            self.assertEqual(transition["direction_certainty"], "confirmed")
            self.assertEqual(transition["verification_status"], "source_verified")

            occurrence = occurrences[occurrence_id]
            self.assertEqual(occurrence["event_id"], event_id)
            self.assertEqual(occurrence["work_id"], work_id)
            self.assertEqual(occurrence["occurrence_kind"], "post_credit")
            self.assertEqual(occurrence["verification_status"], "source_verified")

            participant = participants[participant_id]
            self.assertEqual(participant["transition_id"], event_id)
            self.assertEqual(participant["entity_id"], EDDIE)
            self.assertEqual(participant["participant_role"], "traveler")
            self.assertEqual(participant["identity_certainty"], "confirmed")
            self.assertEqual(participant["verification_status"], "source_verified")

        self.assertEqual({row["continuity_id"] for row in _read("continuities.csv") if row["continuity_id"].startswith("continuity-ssu")}, {SSU})

    def test_crossing_view_reports_both_directions_for_the_same_eddie(self) -> None:
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
                (ARRIVAL_EVENT, RETURN_EVENT),
            ).fetchall()
            connection.close()

        by_id = {row[0]: tuple(row[1:]) for row in rows}
        self.assertEqual(by_id[ARRIVAL_EVENT], (SSU, EARTH_616, LTBC, EDDIE, "traveler", "confirmed"))
        self.assertEqual(by_id[RETURN_EVENT], (EARTH_616, SSU, NWH, EDDIE, "traveler", "confirmed"))

    def test_transition_reason_accepts_verified_traveler_appearance_in_the_other_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT transition_id,support_fact_ids
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                  AND source_work_id=?
                  AND target_work_id=?
                  AND transition_id IN (?,?)
                ORDER BY transition_id
                """,
                (LTBC, NWH, ARRIVAL_EVENT, RETURN_EVENT),
            ).fetchall()
            connection.close()

        by_id = {row[0]: set(row[1].split("|")) for row in rows}
        self.assertEqual(set(by_id), {ARRIVAL_EVENT, RETURN_EVENT})
        self.assertIn(NWH_APPEARANCE, by_id[ARRIVAL_EVENT])
        self.assertIn(LTBC_APPEARANCE, by_id[RETURN_EVENT])
        self.assertIn(ARRIVAL_PARTICIPANT, by_id[ARRIVAL_EVENT])
        self.assertIn(RETURN_PARTICIPANT, by_id[RETURN_EVENT])

    def test_venom_transitions_do_not_spread_to_other_supported_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT transition_id,source_work_id,target_work_id
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                  AND transition_id IN (?,?)
                ORDER BY transition_id,source_work_id,target_work_id
                """,
                (ARRIVAL_EVENT, RETURN_EVENT),
            ).fetchall()
            connection.close()

        self.assertEqual(
            [tuple(row) for row in rows],
            sorted(
                [
                    (ARRIVAL_EVENT, LTBC, NWH),
                    (RETURN_EVENT, LTBC, NWH),
                ]
            ),
        )

    def test_round_trip_semantics_survive_when_the_old_proxy_relation_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _fixture_with_proxy_superseded(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            transition_rows = connection.execute(
                """
                SELECT transition_id
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                  AND source_work_id=?
                  AND target_work_id=?
                  AND transition_id IN (?,?)
                ORDER BY transition_id
                """,
                (LTBC, NWH, ARRIVAL_EVENT, RETURN_EVENT),
            ).fetchall()
            proxy_rows = connection.execute(
                """
                SELECT relation_id
                FROM v_work_connection_reasons
                WHERE reason_kind='explicit_relation'
                  AND relation_id=?
                """,
                (PROXY_RELATION,),
            ).fetchall()
            edge_rows = connection.execute(
                """
                SELECT source_work_id,target_work_id
                FROM v_work_connections_all
                WHERE source_work_id=? AND target_work_id=?
                """,
                (LTBC, NWH),
            ).fetchall()
            connection.close()

        self.assertEqual([row[0] for row in transition_rows], sorted([ARRIVAL_EVENT, RETURN_EVENT]))
        self.assertEqual(proxy_rows, [])
        self.assertEqual([tuple(row) for row in edge_rows], [(LTBC, NWH)])


if __name__ == "__main__":
    unittest.main()
