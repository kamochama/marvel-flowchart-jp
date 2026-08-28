from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
REVIEWS = ROOT / "data" / "content_audit" / "reviews.csv"
THE_MARVELS = "the-marvels-2023"
DOOMSDAY = "avengers-doomsday-2026-12-18"
EARTH_616 = "continuity-earth-616"
DEST = "continuity-the-marvels-alternate-xmen-context"
MONICA = "entity-x-06c4fa169e"
EVENT = "event-the-marvels-monica-alternate-universe-arrival"
OCCURRENCE = "event-occurrence-the-marvels-monica-alternate-universe-arrival"
PARTICIPANT = "transition-participant-the-marvels-monica"
DOOMSDAY_RELATION = "work-relation-the-marvels-2023-avengers-doomsday-2026-12-18-story-link"

REVIEW_FACTS = {
    "review-2026-08-28-the-marvels-monica-destination-continuity": ("continuities.csv", DEST),
    "review-2026-08-28-the-marvels-monica-transition-event": ("events.csv", EVENT),
    "review-2026-08-28-the-marvels-monica-transition-occurrence": ("event_occurrences.csv", OCCURRENCE),
    "review-2026-08-28-the-marvels-monica-transition": ("multiverse_transitions.csv", EVENT),
    "review-2026-08-28-the-marvels-monica-transition-participant": ("transition_participants.csv", PARTICIPANT),
}


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_path(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class TheMarvelsMonicaTransitionTests(unittest.TestCase):
    def test_destination_is_descriptive_verified_universe_without_invented_earth_number(self) -> None:
        continuities = {row["continuity_id"]: row for row in _read("continuities.csv")}
        row = continuities[DEST]
        self.assertEqual(row["continuity_kind"], "universe")
        self.assertEqual(row["certainty"], "confirmed")
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertNotIn("Earth-", row["label_en"])
        self.assertNotEqual(DEST, "continuity-fox-x-men")
        self.assertIn("alternate", row["label_en"].lower())

    def test_monicas_the_marvels_crossing_is_first_class_and_depicted_in_the_marvels(self) -> None:
        events = {row["event_id"]: row for row in _read("events.csv")}
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}
        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}

        event = events[EVENT]
        self.assertEqual(event["event_kind"], "multiverse_transition")
        self.assertEqual(event["primary_continuity_id"], DEST)
        self.assertEqual((event["certainty"], event["verification_status"]), ("confirmed", "source_verified"))

        occurrence = occurrences[OCCURRENCE]
        self.assertEqual((occurrence["event_id"], occurrence["work_id"]), (EVENT, THE_MARVELS))
        self.assertEqual(occurrence["occurrence_kind"], "post_credit")
        self.assertEqual(occurrence["verification_status"], "source_verified")

        transition = transitions[EVENT]
        self.assertEqual((transition["source_continuity_id"], transition["destination_continuity_id"]), (EARTH_616, DEST))
        self.assertEqual(transition["transition_kind"], "unknown")
        self.assertEqual((transition["direction_certainty"], transition["verification_status"]), ("confirmed", "source_verified"))

        participant = participants[PARTICIPANT]
        self.assertEqual((participant["transition_id"], participant["entity_id"]), (EVENT, MONICA))
        self.assertEqual(participant["participant_role"], "traveler")
        self.assertEqual((participant["identity_certainty"], participant["verification_status"]), ("confirmed", "source_verified"))

    def test_crossing_view_reports_only_supported_descriptive_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT source_continuity_id,destination_continuity_id,work_id,
                       occurrence_kind,participant_entity_id,participant_role
                FROM v_multiverse_crossings
                WHERE transition_id=?
                """,
                (EVENT,),
            ).fetchall()
            connection.close()

        self.assertEqual(
            [tuple(row) for row in rows],
            [(EARTH_616, DEST, THE_MARVELS, "post_credit", MONICA, "traveler")],
        )

    def test_transition_does_not_invent_xmen_or_doomsday_work_pair(self) -> None:
        relations = {row["work_relation_id"]: row for row in _read("work_relations.csv")}
        relation = relations[DOOMSDAY_RELATION]
        self.assertEqual(relation["verification_status"], "legacy_seed")
        self.assertEqual(relation["continuity_scope"], "uncertain_return_continuity")

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
