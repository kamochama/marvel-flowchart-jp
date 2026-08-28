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
EARTH_616 = "continuity-earth-616"
EARTH_838 = "continuity-earth-838"
EVENT = "event-mom-doctor-strange-earth838-arrival"
AMERICA = "entity-x-0ba895cd8f"
APPEARANCE = "appearance-doctor-strange-in-the-multiverse-of-madness-2022-entity-x-0ba895cd8f"
PARTICIPANT = "transition-participant-mom-america-chavez-earth838"
SOURCE = "d23-mom-earth838-travel-2024"

REVIEW_FACTS = {
    "review-2026-08-28-mom-america-appearance": ("appearances.csv", APPEARANCE),
    "review-2026-08-28-mom-america-participant": ("transition_participants.csv", PARTICIPANT),
}


def _read(name: str) -> list[dict[str, str]]:
    with (LIB / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_reviews() -> list[dict[str, str]]:
    with REVIEWS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class MultiverseOfMadnessAmericaParticipantTests(unittest.TestCase):
    def test_america_is_a_verified_mom_traveler_without_new_work_pair(self) -> None:
        entities = {row["entity_id"]: row for row in _read("entities.csv")}
        america = entities[AMERICA]
        self.assertEqual((america["name_ja"], america["name_en"], america["entity_type"]), ("アメリカ・チャベス", "America Chavez", "character"))

        appearances = {row["appearance_id"]: row for row in _read("appearances.csv")}
        appearance = appearances[APPEARANCE]
        self.assertEqual((appearance["work_id"], appearance["entity_id"], appearance["appearance_kind"]), (MOM, AMERICA, "onscreen"))
        self.assertEqual((appearance["certainty"], appearance["verification_status"]), ("confirmed", "source_verified"))

        participants = {row["transition_participant_id"]: row for row in _read("transition_participants.csv")}
        participant = participants[PARTICIPANT]
        self.assertEqual((participant["transition_id"], participant["entity_id"], participant["participant_role"]), (EVENT, AMERICA, "traveler"))
        self.assertEqual((participant["identity_certainty"], participant["verification_status"]), ("confirmed", "source_verified"))

        primary_by_fact = {
            (row["fact_table"], row["fact_id"], row["source_id"])
            for row in _read("evidence.csv")
            if row["evidence_role"] == "primary"
        }
        self.assertIn(("appearances.csv", APPEARANCE, SOURCE), primary_by_fact)
        self.assertIn(("transition_participants.csv", PARTICIPANT, SOURCE), primary_by_fact)

        reviews = {row["review_id"]: row for row in _read_reviews()}
        for review_id, fact in REVIEW_FACTS.items():
            review = reviews[review_id]
            self.assertEqual((review["fact_table"], review["fact_id"]), fact)
            self.assertEqual(review["new_verification_status"], "source_verified")
            self.assertEqual(review["review_action"], "created_verified")
            self.assertTrue(review["evidence_ids"])

        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            crossings = connection.execute(
                """
                SELECT source_continuity_id,destination_continuity_id,work_id,
                       occurrence_kind,participant_entity_id,participant_role
                FROM v_multiverse_crossings
                WHERE transition_id=? AND participant_entity_id=?
                """,
                (EVENT, AMERICA),
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
            [tuple(row) for row in crossings],
            [(EARTH_616, EARTH_838, MOM, "depicted", AMERICA, "traveler")],
        )
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
