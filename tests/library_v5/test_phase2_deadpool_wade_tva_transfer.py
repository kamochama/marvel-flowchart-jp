from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
REVIEWS = ROOT / "data" / "content_audit" / "reviews.csv"
WORK = "deadpool-wolverine-2024"
EARTH_10005 = "continuity-earth-10005"
TVA = "continuity-tva-outside-timeline"
EVENT = "event-dw-wade-tva-recruitment"
OCCURRENCE = "event-occurrence-dw-wade-tva-recruitment"
WADE = "entity-x-06b270750e"
PARTICIPANT = "transition-participant-dw-wade-tva"
SCREENPLAY = "deadpool-wolverine-screenplay-2024"


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_reviews() -> list[dict[str, str]]:
    with REVIEWS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class DeadpoolWadeTvaTransferTests(unittest.TestCase):
    def test_wade_is_transferred_from_earth10005_to_tva_without_variant_fanout(self) -> None:
        continuities = {row["continuity_id"]: row for row in _read("continuities.csv")}
        self.assertEqual(
            (continuities[EARTH_10005]["label_en"], continuities[EARTH_10005]["continuity_kind"]),
            ("Earth-10005", "universe"),
        )
        self.assertEqual(
            (continuities[TVA]["label_en"], continuities[TVA]["continuity_kind"]),
            ("TVA / outside-timeline context", "outside_timeline"),
        )

        events = {row["event_id"]: row for row in _read("events.csv")}
        self.assertEqual(
            (events[EVENT]["event_kind"], events[EVENT]["primary_continuity_id"], events[EVENT]["verification_status"]),
            ("multiverse_transition", TVA, "source_verified"),
        )
        occurrences = {row["event_occurrence_id"]: row for row in _read("event_occurrences.csv")}
        self.assertEqual(
            (occurrences[OCCURRENCE]["event_id"], occurrences[OCCURRENCE]["work_id"], occurrences[OCCURRENCE]["occurrence_kind"]),
            (EVENT, WORK, "depicted"),
        )

        transitions = {row["transition_id"]: row for row in _read("multiverse_transitions.csv")}
        transition = transitions[EVENT]
        self.assertEqual(
            (transition["source_continuity_id"], transition["destination_continuity_id"], transition["transition_kind"], transition["direction_certainty"]),
            (EARTH_10005, TVA, "tva_transfer", "confirmed"),
        )
        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}
        self.assertEqual(
            (participants[PARTICIPANT]["transition_id"], participants[PARTICIPANT]["entity_id"], participants[PARTICIPANT]["participant_role"], participants[PARTICIPANT]["identity_certainty"]),
            (EVENT, WADE, "traveler", "confirmed"),
        )

        evidence = {(row["fact_table"], row["fact_id"], row["source_id"]): row for row in _read("evidence.csv")}
        for table, fact_id in (
            ("continuities.csv", EARTH_10005),
            ("continuities.csv", TVA),
            ("events.csv", EVENT),
            ("event_occurrences.csv", OCCURRENCE),
            ("multiverse_transitions.csv", EVENT),
            ("transition_participants.csv", PARTICIPANT),
        ):
            self.assertIn((table, fact_id, SCREENPLAY), evidence)
            self.assertEqual(evidence[(table, fact_id, SCREENPLAY)]["evidence_role"], "primary")

        reviews = {row["review_id"]: row for row in _read_reviews()}
        for review_id, table, fact_id in (
            ("review-2026-08-28-dw-earth10005-continuity", "continuities.csv", EARTH_10005),
            ("review-2026-08-28-dw-tva-continuity", "continuities.csv", TVA),
            ("review-2026-08-28-dw-wade-tva-event", "events.csv", EVENT),
            ("review-2026-08-28-dw-wade-tva-occurrence", "event_occurrences.csv", OCCURRENCE),
            ("review-2026-08-28-dw-wade-tva-transition", "multiverse_transitions.csv", EVENT),
            ("review-2026-08-28-dw-wade-tva-participant", "transition_participants.csv", PARTICIPANT),
        ):
            review = reviews[review_id]
            self.assertEqual((review["fact_table"], review["fact_id"], review["review_action"]), (table, fact_id, "created_verified"))
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertTrue(review["evidence_ids"])

        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            crossing = connection.execute(
                """
                SELECT source_continuity_id,destination_continuity_id,work_id,
                       occurrence_kind,participant_entity_id,participant_role
                FROM v_multiverse_crossings
                WHERE transition_id=?
                """,
                (EVENT,),
            ).fetchall()
            reasons = connection.execute(
                """
                SELECT source_work_id,target_work_id
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition' AND transition_id=?
                """,
                (EVENT,),
            ).fetchall()
            connection.close()

        self.assertEqual(
            [tuple(row) for row in crossing],
            [(EARTH_10005, TVA, WORK, "depicted", WADE, "traveler")],
        )
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
