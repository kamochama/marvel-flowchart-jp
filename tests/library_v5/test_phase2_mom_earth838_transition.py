from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
REVIEWS = ROOT / "data" / "content_audit" / "reviews.csv"
MOM = "doctor-strange-in-the-multiverse-of-madness-2022"
NWH = "spider-man-no-way-home-2021"
EARTH_616 = "continuity-earth-616"
EARTH_838 = "continuity-earth-838"
STRANGE = "entity-x-c8ead423cc"
EVENT = "event-mom-doctor-strange-earth838-arrival"
OCCURRENCE = "event-occurrence-mom-doctor-strange-earth838-arrival"
PARTICIPANT = "transition-participant-mom-doctor-strange-earth838"
SOURCE = "d23-mom-earth838-travel-2024"
NWH_MOM_RELATION = "work-relation-spider-man-no-way-home-2021-doctor-strange-in-the-multiverse-of-madness-2022-crossover"

REVIEW_FACTS = {
    "review-2026-08-28-mom-earth838-continuity": ("continuities.csv", EARTH_838),
    "review-2026-08-28-mom-strange-earth838-event": ("events.csv", EVENT),
    "review-2026-08-28-mom-strange-earth838-occurrence": ("event_occurrences.csv", OCCURRENCE),
    "review-2026-08-28-mom-strange-earth838-transition": ("multiverse_transitions.csv", EVENT),
    "review-2026-08-28-mom-strange-earth838-participant": ("transition_participants.csv", PARTICIPANT),
}


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_path(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class MultiverseOfMadnessEarth838TransitionTests(unittest.TestCase):
    def test_d23_source_and_earth838_continuity_are_source_verified(self) -> None:
        sources = {row["source_id"]: row for row in _read("sources.csv")}
        source = sources[SOURCE]
        self.assertIn("D23", source["official_source"])
        self.assertIn("Earth-838", source["checked_point"])
        self.assertIn("616 Steven Strange", source["checked_point"])
        self.assertEqual(source["url"], "https://d23.com/can-you-find-these-23s-in-disney-movies-and-series/")

        continuities = {row["continuity_id"]: row for row in _read("continuities.csv")}
        continuity = continuities[EARTH_838]
        self.assertEqual(continuity["label_en"], "Earth-838")
        self.assertEqual(continuity["continuity_kind"], "universe")
        self.assertEqual((continuity["certainty"], continuity["verification_status"]), ("confirmed", "source_verified"))

    def test_strange_earth838_crossing_is_first_class_and_depicted_in_mom(self) -> None:
        events = {row["event_id"]: row for row in _read("events.csv")}
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}
        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}

        event = events[EVENT]
        self.assertEqual(event["event_kind"], "multiverse_transition")
        self.assertEqual(event["primary_continuity_id"], EARTH_838)
        self.assertEqual((event["certainty"], event["verification_status"]), ("confirmed", "source_verified"))

        occurrence = occurrences[OCCURRENCE]
        self.assertEqual((occurrence["event_id"], occurrence["work_id"]), (EVENT, MOM))
        self.assertEqual(occurrence["occurrence_kind"], "depicted")
        self.assertEqual(occurrence["verification_status"], "source_verified")

        transition = transitions[EVENT]
        self.assertEqual((transition["source_continuity_id"], transition["destination_continuity_id"]), (EARTH_616, EARTH_838))
        self.assertEqual(transition["transition_kind"], "unknown")
        self.assertEqual((transition["direction_certainty"], transition["verification_status"]), ("confirmed", "source_verified"))

        participant = participants[PARTICIPANT]
        self.assertEqual((participant["transition_id"], participant["entity_id"]), (EVENT, STRANGE))
        self.assertEqual(participant["participant_role"], "traveler")
        self.assertEqual((participant["identity_certainty"], participant["verification_status"]), ("confirmed", "source_verified"))

    def test_crossing_view_reports_earth616_to_earth838_for_strange(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT source_continuity_id,destination_continuity_id,work_id,
                       occurrence_kind,participant_entity_id,participant_role
                FROM v_multiverse_crossings
                WHERE transition_id=? AND participant_entity_id=?
                """,
                (EVENT, STRANGE),
            ).fetchall()
            connection.close()

        self.assertEqual(
            [tuple(row) for row in rows],
            [(EARTH_616, EARTH_838, MOM, "depicted", STRANGE, "traveler")],
        )

    def test_earth838_transition_does_not_relabel_nwh_mom_relation_or_create_work_reason(self) -> None:
        relations = {row["work_relation_id"]: row for row in _read("work_relations.csv")}
        relation = relations[NWH_MOM_RELATION]
        self.assertEqual(relation["verification_status"], "source_verified")
        self.assertEqual(relation["relation_kind"], "crossover")
        self.assertEqual(relation["continuity_scope"], "multiverse")

        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            reasons = connection.execute(
                """
                SELECT source_work_id,target_work_id
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition' AND transition_id=?
                """,
                (EVENT,),
            ).fetchall()
            connection.close()

        self.assertEqual(reasons, [])

    def test_new_verified_facts_have_primary_evidence_and_created_reviews(self) -> None:
        primary_by_fact = {
            (row["fact_table"], row["fact_id"])
            for row in _read("evidence.csv")
            if row["evidence_role"] == "primary"
        }
        reviews = {row["review_id"]: row for row in _read_path(REVIEWS)}

        for review_id, fact in REVIEW_FACTS.items():
            self.assertIn(fact, primary_by_fact)
            review = reviews[review_id]
            self.assertEqual((review["fact_table"], review["fact_id"]), fact)
            self.assertEqual(review["previous_verification_status"], "")
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "created_verified")
            self.assertTrue(review["evidence_ids"])


if __name__ == "__main__":
    unittest.main()
