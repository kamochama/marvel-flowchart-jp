from __future__ import annotations

import sqlite3
import unittest

from scripts.library_v5.db_schema import DB_SCHEMA_VERSION, canonical_table_names, create_schema


class LibraryDbSchemaTests(unittest.TestCase):
    def test_phase1_schema_has_current_canonical_tables_and_reviews(self) -> None:
        self.assertEqual(DB_SCHEMA_VERSION, "1.0-phase1")
        self.assertEqual(
            canonical_table_names(),
            (
                "works",
                "entities",
                "entity_relations",
                "appearances",
                "people",
                "portrayals",
                "continuities",
                "work_continuities",
                "chronology_assertions",
                "work_relations",
                "sources",
                "evidence",
                "reviews",
            ),
        )

    def test_schema_enables_foreign_keys(self) -> None:
        connection = sqlite3.connect(":memory:")
        create_schema(connection)
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_schema_rejects_invalid_verification_status(self) -> None:
        connection = sqlite3.connect(":memory:")
        create_schema(connection)
        connection.execute(
            "INSERT INTO works(work_id,title_ja,title_en,format,status,release_sort_date,release_display_date) VALUES(?,?,?,?,?,?,?)",
            ("work-a", "作品A", "Work A", "film", "released", "2020-01-01", "2020-01-01"),
        )
        connection.execute(
            "INSERT INTO entities(entity_id,name_ja,name_en,entity_type,notes) VALUES(?,?,?,?,?)",
            ("entity-a", "人物A", "Entity A", "character", ""),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO appearances(appearance_id,work_id,entity_id,appearance_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
                ("appearance-a", "work-a", "entity-a", "onscreen", "confirmed", "not-a-status", ""),
            )


if __name__ == "__main__":
    unittest.main()
