import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LibraryV5IdsAndSchemaTests(unittest.TestCase):
    def test_slug_id_is_deterministic_and_prefixed(self):
        from scripts.library_v5.ids import slug_id

        self.assertEqual(slug_id("entity", "Tony Stark"), "entity-tony-stark")
        self.assertEqual(slug_id("entity", "  Tony   Stark  "), "entity-tony-stark")
        self.assertTrue(slug_id("entity", "トニー・スターク").startswith("entity-"))
        self.assertNotEqual(slug_id("entity", "トニー・スターク"), "entity-")

    def test_slug_id_falls_back_to_hash_when_ascii_slug_is_empty(self):
        from scripts.library_v5.ids import slug_id

        value = slug_id("entity", "王")
        self.assertRegex(value, r"^entity-x-[0-9a-f]{10}$")
        self.assertEqual(value, slug_id("entity", "王"))

    def test_schema_declares_v5_canonical_tables(self):
        schema_path = ROOT / "data" / "library" / "schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["schema_version"], "5.2")
        expected_tables = {
            "works.csv",
            "entities.csv",
            "entity_relations.csv",
            "appearances.csv",
            "people.csv",
            "portrayals.csv",
            "continuities.csv",
            "work_continuities.csv",
            "chronology_assertions.csv",
            "work_relations.csv",
            "events.csv",
            "event_occurrences.csv",
            "event_participants.csv",
            "event_relations.csv",
            "multiverse_transitions.csv",
            "transition_participants.csv",
            "sources.csv",
            "evidence.csv",
        }
        self.assertTrue(expected_tables.issubset(schema["tables"].keys()))

    def test_schema_keeps_performer_and_character_identity_separate(self):
        schema = json.loads(
            (ROOT / "data" / "library" / "schema.json").read_text(encoding="utf-8")
        )
        portrayal = schema["tables"]["portrayals.csv"]
        self.assertIn("person_id", portrayal["required_columns"])
        self.assertIn("entity_id", portrayal["required_columns"])
        self.assertIn("work_id", portrayal["required_columns"])
        self.assertIn("unknown_role", schema["enums"]["portrayal_kind"])
        self.assertIn("entity_id", portrayal["nullable_columns"])

    def test_schema_uses_design_spec_verification_and_certainty_vocab(self):
        schema = json.loads(
            (ROOT / "data" / "library" / "schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["enums"]["verification_status"],
            ["legacy_seed", "source_verified", "conflicted", "superseded"],
        )
        self.assertEqual(
            schema["enums"]["certainty"],
            ["confirmed", "probable", "uncertain", "unknown"],
        )

    def test_source_auditable_fact_tables_have_verification_status(self):
        schema = json.loads(
            (ROOT / "data" / "library" / "schema.json").read_text(encoding="utf-8")
        )
        fact_tables = {
            "releases.csv",
            "production_status_assertions.csv",
            "entity_relations.csv",
            "appearances.csv",
            "portrayals.csv",
            "continuities.csv",
            "work_continuities.csv",
            "chronology_assertions.csv",
            "work_relations.csv",
            "events.csv",
            "event_occurrences.csv",
            "event_participants.csv",
            "event_relations.csv",
            "multiverse_transitions.csv",
            "transition_participants.csv",
        }
        for table_name in fact_tables:
            with self.subTest(table=table_name):
                self.assertIn(
                    "verification_status",
                    schema["tables"][table_name]["required_columns"],
                )

    def test_release_and_production_status_tables_are_declared(self):
        schema = json.loads(
            (ROOT / "data" / "library" / "schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["tables"]["releases.csv"]["required_columns"],
            [
                "release_id", "work_id", "territory", "release_kind", "release_date",
                "release_precision", "status", "certainty", "verification_status", "notes",
            ],
        )
        self.assertEqual(
            schema["tables"]["production_status_assertions.csv"]["required_columns"],
            [
                "production_status_assertion_id", "work_id", "status", "asserted_at",
                "certainty", "verification_status", "notes",
            ],
        )
        self.assertEqual(schema["tables"]["releases.csv"]["primary_key"], "release_id")
        self.assertEqual(
            schema["tables"]["releases.csv"]["foreign_keys"],
            {"work_id": "works.work_id"},
        )
        self.assertEqual(
            schema["tables"]["production_status_assertions.csv"]["primary_key"],
            "production_status_assertion_id",
        )
        self.assertEqual(
            schema["tables"]["production_status_assertions.csv"]["foreign_keys"],
            {"work_id": "works.work_id"},
        )
        self.assertEqual(
            schema["enums"]["release_kind"],
            [
                "theatrical", "streaming", "broadcast", "festival", "re_release",
                "home_video", "special", "series_start", "imax_series_start", "undated", "other",
            ],
        )
        self.assertEqual(schema["enums"]["release_precision"], ["day", "month", "year", "none"])
        self.assertEqual(
            schema["enums"]["release_status"],
            ["released", "announced", "delayed", "cancelled", "unknown"],
        )
        self.assertEqual(
            schema["enums"]["production_status"],
            ["announced", "in_development", "filming", "completed", "delayed", "cancelled", "released", "unknown"],
        )

    def test_release_status_facts_are_indexed_for_evidence_and_review(self):
        from scripts.library_v5.audit import FACT_ID_COLUMNS as AUDIT_FACT_ID_COLUMNS
        from scripts.library_v5.content_audit import FACT_ID_COLUMNS as REVIEW_FACT_ID_COLUMNS

        expected = {
            "releases.csv": "release_id",
            "production_status_assertions.csv": "production_status_assertion_id",
        }
        for table_name, id_column in expected.items():
            self.assertEqual(AUDIT_FACT_ID_COLUMNS[table_name], id_column)
            self.assertEqual(REVIEW_FACT_ID_COLUMNS[table_name], id_column)


if __name__ == "__main__":
    unittest.main()
