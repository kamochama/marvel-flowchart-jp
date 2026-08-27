from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.library_v5.apply_review_patch import ALLOWED_PATHS


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


EXPECTED = {
    "events.csv": ["event_id", "name_ja", "name_en", "event_kind", "primary_continuity_id", "certainty", "verification_status", "notes"],
    "event_occurrences.csv": ["event_occurrence_id", "event_id", "work_id", "occurrence_kind", "certainty", "verification_status", "notes"],
    "event_participants.csv": ["event_participant_id", "event_id", "entity_id", "participant_role", "certainty", "verification_status", "notes"],
    "event_relations.csv": ["event_relation_id", "source_event_id", "relation_kind", "target_event_id", "certainty", "verification_status", "notes"],
    "multiverse_transitions.csv": ["transition_id", "source_continuity_id", "destination_continuity_id", "transition_kind", "direction_certainty", "verification_status", "notes"],
    "transition_participants.csv": ["transition_participant_id", "transition_id", "entity_id", "participant_role", "identity_certainty", "verification_status", "notes"],
}


class Phase2EventCanonicalSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads((LIB / "schema.json").read_text(encoding="utf-8"))

    def test_schema_version_and_new_tables(self) -> None:
        self.assertEqual(self.schema["schema_version"], "5.1")
        for table_name, columns in EXPECTED.items():
            with self.subTest(table=table_name):
                self.assertEqual(self.schema["tables"][table_name]["required_columns"], columns)
                path = LIB / table_name
                self.assertTrue(path.exists())
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    self.assertEqual(next(csv.reader(handle)), columns)

    def test_foreign_keys_and_nullable_transition_endpoints(self) -> None:
        tables = self.schema["tables"]
        self.assertEqual(tables["events.csv"]["foreign_keys"]["primary_continuity_id"], "continuities.continuity_id")
        self.assertIn("primary_continuity_id", tables["events.csv"]["nullable_columns"])
        self.assertEqual(tables["event_occurrences.csv"]["foreign_keys"], {"event_id": "events.event_id", "work_id": "works.work_id"})
        self.assertEqual(tables["event_participants.csv"]["foreign_keys"], {"event_id": "events.event_id", "entity_id": "entities.entity_id"})
        self.assertEqual(tables["event_relations.csv"]["foreign_keys"], {"source_event_id": "events.event_id", "target_event_id": "events.event_id"})
        transitions = tables["multiverse_transitions.csv"]
        self.assertEqual(transitions["foreign_keys"], {
            "transition_id": "events.event_id",
            "source_continuity_id": "continuities.continuity_id",
            "destination_continuity_id": "continuities.continuity_id",
        })
        self.assertEqual(set(transitions["nullable_columns"]), {"source_continuity_id", "destination_continuity_id"})
        self.assertEqual(tables["transition_participants.csv"]["foreign_keys"], {"transition_id": "multiverse_transitions.transition_id", "entity_id": "entities.entity_id"})

    def test_event_and_transition_vocabulary_is_explicit(self) -> None:
        enums = self.schema["enums"]
        self.assertIn("multiverse_transition", enums["event_kind"])
        self.assertIn("post_credit", enums["event_occurrence_kind"])
        self.assertIn("physical_crossing", enums["transition_kind"])
        self.assertIn("spell_displacement", enums["transition_kind"])
        self.assertIn("tva_transfer", enums["transition_kind"])
        self.assertIn("vehicle", enums["transition_participant_role"])
        self.assertIn("traveler", enums["transition_participant_role"])
        self.assertIn("vehicle", enums["entity_type"])

    def test_all_new_fact_tables_are_patchable(self) -> None:
        self.assertTrue(set(EXPECTED) <= set(ALLOWED_PATHS))

    def test_all_new_fact_tables_are_source_auditable(self) -> None:
        for table_name in EXPECTED:
            with self.subTest(table=table_name):
                self.assertIn("verification_status", self.schema["tables"][table_name]["required_columns"])


if __name__ == "__main__":
    unittest.main()
