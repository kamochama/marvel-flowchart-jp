from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
REVIEWS = ROOT / "data" / "content_audit" / "reviews.csv"
HOMECOMING = "spider-man-homecoming-2017"
NWH = "spider-man-no-way-home-2021"
MORBIUS = "morbius-2022"
EARTH_616 = "continuity-earth-616"
SSU = "continuity-ssu"
VULTURE = "entity-adrian-toomes-vulture"
EVENT = "event-morbius-adrian-toomes-ssu-arrival"
OCCURRENCE = "event-occurrence-morbius-adrian-toomes-ssu-arrival"
PARTICIPANT = "transition-participant-morbius-adrian-toomes"
CAUSAL_RELATION = "work-relation-spider-man-no-way-home-2021-morbius-2022-crossover"

REVIEW_FACTS = {
    "review-2026-08-28-vulture-transfer-event": ("events.csv", EVENT),
    "review-2026-08-28-vulture-transfer-occurrence": ("event_occurrences.csv", OCCURRENCE),
    "review-2026-08-28-vulture-transfer-transition": ("multiverse_transitions.csv", EVENT),
    "review-2026-08-28-vulture-transfer-participant": ("transition_participants.csv", PARTICIPANT),
}


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_path(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class VultureTransferTransitionTests(unittest.TestCase):
    def test_morbius_postcredit_is_first_class_vulture_transition(self) -> None:
        events = {row["event_id"]: row for row in _read("events.csv")}
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}
        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}

        event = events[EVENT]
        self.assertEqual(event["event_kind"], "multiverse_transition")
        self.assertEqual(event["primary_continuity_id"], SSU)
        self.assertEqual(event["certainty"], "confirmed")
        self.assertEqual(event["verification_status"], "source_verified")

        occurrence = occurrences[OCCURRENCE]
        self.assertEqual(occurrence["event_id"], EVENT)
        self.assertEqual(occurrence["work_id"], MORBIUS)
        self.assertEqual(occurrence["occurrence_kind"], "post_credit")
        self.assertEqual(occurrence["verification_status"], "source_verified")

        transition = transitions[EVENT]
        self.assertEqual(transition["source_continuity_id"], EARTH_616)
        self.assertEqual(transition["destination_continuity_id"], SSU)
        self.assertEqual(transition["transition_kind"], "unknown")
        self.assertEqual(transition["direction_certainty"], "confirmed")
        self.assertEqual(transition["verification_status"], "source_verified")

        participant = participants[PARTICIPANT]
        self.assertEqual(participant["transition_id"], EVENT)
        self.assertEqual(participant["entity_id"], VULTURE)
        self.assertEqual(participant["participant_role"], "traveler")
        self.assertEqual(participant["identity_certainty"], "confirmed")
        self.assertEqual(participant["verification_status"], "source_verified")

    def test_crossing_view_reports_morbius_as_depiction_work_not_no_way_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT source_continuity_id,destination_continuity_id,work_id,
                       occurrence_kind,participant_entity_id,participant_role,identity_certainty
                FROM v_multiverse_crossings
                WHERE transition_id=?
                """,
                (EVENT,),
            ).fetchall()
            connection.close()

        self.assertEqual(
            [tuple(row) for row in rows],
            [(EARTH_616, SSU, MORBIUS, "post_credit", VULTURE, "traveler", "confirmed")],
        )

    def test_transition_enriches_existing_homecoming_morbius_identity_pair_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT source_work_id,target_work_id,support_fact_ids
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition' AND transition_id=?
                ORDER BY source_work_id,target_work_id
                """,
                (EVENT,),
            ).fetchall()
            connection.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0][:2]), (HOMECOMING, MORBIUS))
        support = set(rows[0][2].split("|"))
        self.assertIn("appearance-spider-man-homecoming-2017-entity-adrian-toomes-vulture", support)
        self.assertIn(PARTICIPANT, support)

    def test_no_way_home_morbius_causal_relation_remains_independent(self) -> None:
        relations = {row["work_relation_id"]: row for row in _read("work_relations.csv")}
        row = relations[CAUSAL_RELATION]
        self.assertEqual(row["verification_status"], "source_verified")
        self.assertEqual(row["relation_kind"], "crossover")
        self.assertEqual(row["continuity_scope"], "multiverse")
        self.assertIn("attributes", row["notes"])

        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT source_work_id,target_work_id
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                  AND transition_id=?
                  AND source_work_id=? AND target_work_id=?
                """,
                (EVENT, NWH, MORBIUS),
            ).fetchall()
            connection.close()

        self.assertEqual(rows, [])

    def test_new_transition_facts_have_primary_evidence_and_created_reviews(self) -> None:
        evidence = _read("evidence.csv")
        primary_by_fact = {
            (row["fact_table"], row["fact_id"])
            for row in evidence
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
