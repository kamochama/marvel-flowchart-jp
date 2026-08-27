from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.canonical_guard import canonical_hashes
from scripts.library_v5.db_compile import compile_database, open_query_connection


HEADERS = {
    "works.csv": ["work_id", "title_ja", "title_en", "title_official", "release", "release_raw", "format", "status", "classification", "ja_status", "japan_date", "japan_type", "source_url", "source_note", "notes", "release_sort_date", "release_display_date", "release_kind", "release_certainty", "release_precision", "release_source_note", "aliases_ja", "title_audit_status", "title_audit_source_url", "title_last_verified", "title_management_note", "stable_id_note"],
    "entities.csv": ["entity_id", "name_ja", "name_en", "entity_type", "notes"],
    "entity_relations.csv": ["entity_relation_id", "source_entity_id", "relation_kind", "target_entity_id", "certainty", "verification_status", "notes"],
    "appearances.csv": ["appearance_id", "work_id", "entity_id", "appearance_kind", "certainty", "verification_status", "notes"],
    "people.csv": ["person_id", "name", "notes"],
    "portrayals.csv": ["portrayal_id", "work_id", "person_id", "entity_id", "portrayal_kind", "certainty", "verification_status", "notes"],
    "continuities.csv": ["continuity_id", "label_ja", "label_en", "continuity_kind", "certainty", "verification_status", "notes"],
    "work_continuities.csv": ["work_continuity_id", "work_id", "continuity_id", "relation_to_continuity", "certainty", "verification_status", "notes"],
    "chronology_assertions.csv": ["chronology_assertion_id", "continuity_id", "earlier_work_id", "later_work_id", "certainty", "verification_status", "notes"],
    "work_relations.csv": ["work_relation_id", "source_work_id", "target_work_id", "relation_kind", "relation_scope", "directness", "continuity_scope", "certainty", "verification_status", "notes"],
    "events.csv": ["event_id", "name_ja", "name_en", "event_kind", "primary_continuity_id", "certainty", "verification_status", "notes"],
    "event_occurrences.csv": ["event_occurrence_id", "event_id", "work_id", "occurrence_kind", "certainty", "verification_status", "notes"],
    "event_participants.csv": ["event_participant_id", "event_id", "entity_id", "participant_role", "certainty", "verification_status", "notes"],
    "event_relations.csv": ["event_relation_id", "source_event_id", "relation_kind", "target_event_id", "certainty", "verification_status", "notes"],
    "multiverse_transitions.csv": ["transition_id", "source_continuity_id", "destination_continuity_id", "transition_kind", "direction_certainty", "verification_status", "notes"],
    "transition_participants.csv": ["transition_participant_id", "transition_id", "entity_id", "participant_role", "identity_certainty", "verification_status", "notes"],
    "sources.csv": ["source_id", "purpose", "official_source", "checked_point", "url"],
    "evidence.csv": ["evidence_id", "fact_table", "fact_id", "source_id", "evidence_role", "quoted_or_paraphrased_note", "verified_at"],
}
REVIEW_HEADER = ["review_id", "fact_table", "fact_id", "previous_verification_status", "new_verification_status", "review_action", "evidence_ids", "reviewed_at", "notes"]


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_minimal_repo(root: Path) -> Path:
    library = root / "data" / "library"
    for name, header in HEADERS.items():
        _write_csv(library / name, header, [])
    _write_csv(root / "data" / "content_audit" / "reviews.csv", REVIEW_HEADER, [])

    _write_csv(library / "works.csv", HEADERS["works.csv"], [
        {"work_id": "work-a", "title_ja": "作品A", "title_en": "Work A", "format": "film", "status": "released", "release_sort_date": "2020-01-01", "release_display_date": "2020-01-01"},
        {"work_id": "work-b", "title_ja": "作品B", "title_en": "Work B", "format": "film", "status": "released", "release_sort_date": "2021-01-01", "release_display_date": "2021-01-01"},
    ])
    _write_csv(library / "entities.csv", HEADERS["entities.csv"], [
        {"entity_id": "entity-a", "name_ja": "人物A", "name_en": "Entity A", "entity_type": "character", "notes": ""},
    ])
    _write_csv(library / "appearances.csv", HEADERS["appearances.csv"], [
        {"appearance_id": "appearance-a", "work_id": "work-a", "entity_id": "entity-a", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified", "notes": ""},
    ])
    return root


class LibraryDbCompileTests(unittest.TestCase):
    def test_compile_loads_rows_without_mutating_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_minimal_repo(Path(tmp))
            before = canonical_hashes(root)
            result = compile_database(root)
            after = canonical_hashes(root)

            self.assertEqual(before, after)
            self.assertTrue(result.db_path.exists())
            self.assertEqual(result.table_counts["works"], 2)
            self.assertEqual(result.table_counts["appearances"], 1)
            self.assertEqual(result.table_counts["events"], 0)
            self.assertEqual(result.table_counts["multiverse_transitions"], 0)

            connection = open_query_connection(result.db_path)
            self.assertEqual(connection.execute("SELECT count(*) FROM works").fetchone()[0], 2)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            connection.close()

    def test_compile_is_atomic_on_foreign_key_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_minimal_repo(Path(tmp))
            _write_csv(root / "data/library/appearances.csv", HEADERS["appearances.csv"], [
                {"appearance_id": "appearance-bad", "work_id": "missing-work", "entity_id": "entity-a", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified", "notes": ""},
            ])
            output = root / "data/derived/db/marvel.sqlite"

            with self.assertRaises(sqlite3.IntegrityError):
                compile_database(root, output)

            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".sqlite.tmp").exists())


if __name__ == "__main__":
    unittest.main()
