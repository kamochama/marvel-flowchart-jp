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

        self.assertEqual(schema["schema_version"], "5.0")
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


if __name__ == "__main__":
    unittest.main()
