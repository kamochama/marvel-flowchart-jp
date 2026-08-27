from __future__ import annotations

import csv
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_fingerprint import logical_fingerprint
from scripts.library_v5.db_schema import DB_SCHEMA_VERSION, canonical_table_names


ROOT = Path(__file__).resolve().parents[2]

PHASE2_HEADERS = {
    "events.csv": ["event_id", "name_ja", "name_en", "event_kind", "primary_continuity_id", "certainty", "verification_status", "notes"],
    "event_occurrences.csv": ["event_occurrence_id", "event_id", "work_id", "occurrence_kind", "certainty", "verification_status", "notes"],
    "event_participants.csv": ["event_participant_id", "event_id", "entity_id", "participant_role", "certainty", "verification_status", "notes"],
    "event_relations.csv": ["event_relation_id", "source_event_id", "relation_kind", "target_event_id", "certainty", "verification_status", "notes"],
    "multiverse_transitions.csv": ["transition_id", "source_continuity_id", "destination_continuity_id", "transition_kind", "direction_certainty", "verification_status", "notes"],
    "transition_participants.csv": ["transition_participant_id", "transition_id", "entity_id", "participant_role", "identity_certainty", "verification_status", "notes"],
}


def _copy_canonical_fixture(root: Path) -> Path:
    shutil.copytree(ROOT / "data" / "library", root / "data" / "library")
    reviews = root / "data" / "content_audit" / "reviews.csv"
    reviews.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data" / "content_audit" / "reviews.csv", reviews)
    return root


def _write_rows(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _clear_phase2_fact_rows(library: Path) -> None:
    """Make synthetic Phase 2 fixtures independent of real migrated rows."""
    for name, header in PHASE2_HEADERS.items():
        _write_rows(library / name, header, [])


def _first_continuity_id(root: Path) -> str:
    with (root / "data" / "library" / "continuities.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    return row["continuity_id"]


class Phase2DbCompileTests(unittest.TestCase):
    def test_phase2_schema_version_and_tables_are_compiled(self) -> None:
        self.assertEqual(DB_SCHEMA_VERSION, "1.1-phase2-events")
        expected_tables = {
            "events",
            "event_occurrences",
            "event_participants",
            "event_relations",
            "multiverse_transitions",
            "transition_participants",
        }
        self.assertTrue(expected_tables <= set(canonical_table_names()))

        with tempfile.TemporaryDirectory() as tmp:
            root = _copy_canonical_fixture(Path(tmp))
            result = compile_database(root)
            self.assertTrue(expected_tables <= set(result.table_counts))

            connection = open_query_connection(result.db_path)
            actual_tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            connection.close()
            self.assertTrue(expected_tables <= actual_tables)

            fingerprint = logical_fingerprint(result.db_path, repo_root=root)
            self.assertEqual(fingerprint["db_schema_version"], "1.1-phase2-events")
            self.assertTrue(expected_tables <= set(fingerprint["tables"]))

    def test_blank_transition_endpoints_compile_as_sql_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _copy_canonical_fixture(Path(tmp))
            library = root / "data" / "library"
            _clear_phase2_fact_rows(library)
            _write_rows(library / "events.csv", PHASE2_HEADERS["events.csv"], [{
                "event_id": "event-transition-unknown-endpoints",
                "name_ja": "世界移動",
                "name_en": "Universe transfer",
                "event_kind": "multiverse_transition",
                "primary_continuity_id": "",
                "certainty": "confirmed",
                "verification_status": "legacy_seed",
                "notes": "",
            }])
            _write_rows(library / "multiverse_transitions.csv", PHASE2_HEADERS["multiverse_transitions.csv"], [{
                "transition_id": "event-transition-unknown-endpoints",
                "source_continuity_id": "",
                "destination_continuity_id": "",
                "transition_kind": "physical_crossing",
                "direction_certainty": "unknown",
                "verification_status": "legacy_seed",
                "notes": "",
            }])

            result = compile_database(root)
            connection = open_query_connection(result.db_path)
            row = connection.execute(
                "SELECT primary_continuity_id FROM events WHERE event_id=?",
                ("event-transition-unknown-endpoints",),
            ).fetchone()
            endpoints = connection.execute(
                "SELECT source_continuity_id,destination_continuity_id FROM multiverse_transitions WHERE transition_id=?",
                ("event-transition-unknown-endpoints",),
            ).fetchone()
            connection.close()

            self.assertEqual(row, (None,))
            self.assertEqual(endpoints, (None, None))

    def test_invalid_transition_event_kind_aborts_atomic_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _copy_canonical_fixture(Path(tmp))
            library = root / "data" / "library"
            _clear_phase2_fact_rows(library)
            _write_rows(library / "events.csv", PHASE2_HEADERS["events.csv"], [{
                "event_id": "event-not-transition",
                "name_ja": "戦闘",
                "name_en": "Battle",
                "event_kind": "battle",
                "primary_continuity_id": "",
                "certainty": "confirmed",
                "verification_status": "legacy_seed",
                "notes": "",
            }])
            _write_rows(library / "multiverse_transitions.csv", PHASE2_HEADERS["multiverse_transitions.csv"], [{
                "transition_id": "event-not-transition",
                "source_continuity_id": "",
                "destination_continuity_id": "",
                "transition_kind": "physical_crossing",
                "direction_certainty": "unknown",
                "verification_status": "legacy_seed",
                "notes": "",
            }])
            output = root / "data" / "derived" / "db" / "marvel.sqlite"

            with self.assertRaises(sqlite3.IntegrityError):
                compile_database(root, output)

            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".sqlite.tmp").exists())

    def test_directional_transition_rejects_same_known_continuity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _copy_canonical_fixture(Path(tmp))
            library = root / "data" / "library"
            _clear_phase2_fact_rows(library)
            continuity_id = _first_continuity_id(root)
            _write_rows(library / "events.csv", PHASE2_HEADERS["events.csv"], [{
                "event_id": "event-same-continuity",
                "name_ja": "不正な世界移動",
                "name_en": "Invalid crossing",
                "event_kind": "multiverse_transition",
                "primary_continuity_id": continuity_id,
                "certainty": "confirmed",
                "verification_status": "legacy_seed",
                "notes": "",
            }])
            _write_rows(library / "multiverse_transitions.csv", PHASE2_HEADERS["multiverse_transitions.csv"], [{
                "transition_id": "event-same-continuity",
                "source_continuity_id": continuity_id,
                "destination_continuity_id": continuity_id,
                "transition_kind": "physical_crossing",
                "direction_certainty": "confirmed",
                "verification_status": "legacy_seed",
                "notes": "",
            }])

            with self.assertRaises(sqlite3.IntegrityError):
                compile_database(root)


if __name__ == "__main__":
    unittest.main()
