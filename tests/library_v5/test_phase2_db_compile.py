from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database
from scripts.library_v5.db_schema import DB_SCHEMA_VERSION, canonical_table_names


ROOT = Path(__file__).resolve().parents[2]
PHASE2_TABLES = (
    "events",
    "event_occurrences",
    "event_participants",
    "event_relations",
    "multiverse_transitions",
    "transition_participants",
)


def _copy_repo_inputs(destination: Path) -> Path:
    repo = destination / "repo"
    shutil.copytree(ROOT / "data" / "library", repo / "data" / "library")
    (repo / "data" / "content_audit").mkdir(parents=True)
    shutil.copy2(ROOT / "data" / "content_audit" / "reviews.csv", repo / "data" / "content_audit" / "reviews.csv")
    return repo


def _first_two_continuities(repo: Path) -> tuple[str, str]:
    with (repo / "data" / "library" / "continuities.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 2:
        raise AssertionError("fixture needs at least two continuities")
    return rows[0]["continuity_id"], rows[1]["continuity_id"]


class Phase2DbCompileTests(unittest.TestCase):
    def test_schema_version_and_phase2_tables_are_compiled(self) -> None:
        self.assertEqual(DB_SCHEMA_VERSION, "1.1-phase2-events")
        names = set(canonical_table_names())
        self.assertTrue(set(PHASE2_TABLES) <= names)

        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo_inputs(Path(tmp))
            result = compile_database(repo, repo / "data" / "derived" / "db" / "marvel.sqlite")
            for table_name in PHASE2_TABLES:
                self.assertIn(table_name, result.table_counts)
                self.assertEqual(result.table_counts[table_name], 0)

    def test_transition_event_kind_mismatch_aborts_atomic_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo_inputs(Path(tmp))
            source_continuity, destination_continuity = _first_two_continuities(repo)
            events = repo / "data" / "library" / "events.csv"
            transitions = repo / "data" / "library" / "multiverse_transitions.csv"

            with events.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(["event-invalid-transition", "不正な越境", "Invalid crossing", "battle", "", "confirmed", "legacy_seed", "fixture"])
            with transitions.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(["event-invalid-transition", source_continuity, destination_continuity, "physical_crossing", "confirmed", "legacy_seed", "fixture"])

            output = repo / "data" / "derived" / "db" / "marvel.sqlite"
            with self.assertRaisesRegex(ValueError, "transition_event_kind_mismatch"):
                compile_database(repo, output)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(output.suffix + ".tmp").exists())

    def test_directional_transition_same_continuity_aborts_atomic_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo_inputs(Path(tmp))
            source_continuity, _ = _first_two_continuities(repo)
            events = repo / "data" / "library" / "events.csv"
            transitions = repo / "data" / "library" / "multiverse_transitions.csv"

            with events.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(["event-same-continuity", "同一宇宙越境", "Same-continuity crossing", "multiverse_transition", "", "confirmed", "legacy_seed", "fixture"])
            with transitions.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(["event-same-continuity", source_continuity, source_continuity, "physical_crossing", "confirmed", "legacy_seed", "fixture"])

            output = repo / "data" / "derived" / "db" / "marvel.sqlite"
            with self.assertRaisesRegex(ValueError, "transition_same_continuity"):
                compile_database(repo, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
