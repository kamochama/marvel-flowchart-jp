from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_fingerprint import logical_fingerprint
from scripts.library_v5.db_views import PUBLIC_VIEW_NAMES


ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "data" / "library"

HEADERS = {
    "events.csv": ["event_id", "name_ja", "name_en", "event_kind", "primary_continuity_id", "certainty", "verification_status", "notes"],
    "event_occurrences.csv": ["event_occurrence_id", "event_id", "work_id", "occurrence_kind", "certainty", "verification_status", "notes"],
    "event_participants.csv": ["event_participant_id", "event_id", "entity_id", "participant_role", "certainty", "verification_status", "notes"],
    "multiverse_transitions.csv": ["transition_id", "source_continuity_id", "destination_continuity_id", "transition_kind", "direction_certainty", "verification_status", "notes"],
    "transition_participants.csv": ["transition_participant_id", "transition_id", "entity_id", "participant_role", "identity_certainty", "verification_status", "notes"],
}


def _write_rows(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _fixture(root: Path) -> tuple[Path, dict[str, str]]:
    shutil.copytree(LIBRARY, root / "data" / "library")
    reviews = root / "data" / "content_audit" / "reviews.csv"
    reviews.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data" / "content_audit" / "reviews.csv", reviews)

    works = _rows(root / "data/library/works.csv")
    entities = _rows(root / "data/library/entities.csv")
    continuities = _rows(root / "data/library/continuities.csv")
    assert works and entities and len(continuities) >= 2
    work = works[0]
    entity = entities[0]
    source = continuities[0]
    destination = continuities[1]

    _write_rows(root / "data/library/events.csv", HEADERS["events.csv"], [
        {
            "event_id": "event-crossing-with-traveler",
            "name_ja": "旅人ありの世界移動",
            "name_en": "Crossing with traveler",
            "event_kind": "multiverse_transition",
            "primary_continuity_id": destination["continuity_id"],
            "certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "event note",
        },
        {
            "event_id": "event-crossing-without-traveler",
            "name_ja": "旅人不明の世界移動",
            "name_en": "Crossing without known traveler",
            "event_kind": "multiverse_transition",
            "primary_continuity_id": destination["continuity_id"],
            "certainty": "probable",
            "verification_status": "legacy_seed",
            "notes": "event note 2",
        },
    ])
    _write_rows(root / "data/library/event_occurrences.csv", HEADERS["event_occurrences.csv"], [
        {
            "event_occurrence_id": "occurrence-crossing-with-traveler",
            "event_id": "event-crossing-with-traveler",
            "work_id": work["work_id"],
            "occurrence_kind": "depicted",
            "certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "occurrence note",
        },
        {
            "event_occurrence_id": "occurrence-crossing-without-traveler",
            "event_id": "event-crossing-without-traveler",
            "work_id": work["work_id"],
            "occurrence_kind": "post_credit",
            "certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "occurrence note 2",
        },
    ])
    _write_rows(root / "data/library/event_participants.csv", HEADERS["event_participants.csv"], [{
        "event_participant_id": "event-participant-traveler",
        "event_id": "event-crossing-with-traveler",
        "entity_id": entity["entity_id"],
        "participant_role": "traveler",
        "certainty": "confirmed",
        "verification_status": "legacy_seed",
        "notes": "participant note",
    }])
    _write_rows(root / "data/library/multiverse_transitions.csv", HEADERS["multiverse_transitions.csv"], [
        {
            "transition_id": "event-crossing-with-traveler",
            "source_continuity_id": source["continuity_id"],
            "destination_continuity_id": destination["continuity_id"],
            "transition_kind": "physical_crossing",
            "direction_certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "transition note",
        },
        {
            "transition_id": "event-crossing-without-traveler",
            "source_continuity_id": source["continuity_id"],
            "destination_continuity_id": destination["continuity_id"],
            "transition_kind": "portal",
            "direction_certainty": "probable",
            "verification_status": "legacy_seed",
            "notes": "transition note 2",
        },
    ])
    _write_rows(root / "data/library/transition_participants.csv", HEADERS["transition_participants.csv"], [{
        "transition_participant_id": "transition-participant-traveler",
        "transition_id": "event-crossing-with-traveler",
        "entity_id": entity["entity_id"],
        "participant_role": "traveler",
        "identity_certainty": "confirmed",
        "verification_status": "legacy_seed",
        "notes": "transition participant note",
    }])
    return root, {
        "work_id": work["work_id"],
        "work_title_ja": work["title_ja"],
        "entity_id": entity["entity_id"],
        "entity_name_ja": entity["name_ja"],
        "source_continuity_id": source["continuity_id"],
        "source_label_ja": source["label_ja"],
        "destination_continuity_id": destination["continuity_id"],
        "destination_label_ja": destination["label_ja"],
    }


class Phase2DbViewTests(unittest.TestCase):
    def test_public_view_registry_and_fingerprint_include_phase2_views(self) -> None:
        self.assertIn("v_event_history", PUBLIC_VIEW_NAMES)
        self.assertIn("v_multiverse_crossings", PUBLIC_VIEW_NAMES)
        self.assertIn("v_work_releases", PUBLIC_VIEW_NAMES)
        self.assertIn("v_work_production_status", PUBLIC_VIEW_NAMES)
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            fingerprint = logical_fingerprint(db_path, repo_root=root)
            self.assertIn("v_event_history", fingerprint["views"])
            self.assertIn("v_multiverse_crossings", fingerprint["views"])
            self.assertIn("v_work_releases", fingerprint["views"])
            self.assertIn("v_work_production_status", fingerprint["views"])

    def test_event_history_preserves_occurrence_participant_and_verification_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, expected = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            row = connection.execute(
                """
                SELECT event_id,event_name_ja,event_kind,primary_continuity_id,
                       event_occurrence_id,work_id,work_title_ja,occurrence_kind,
                       event_participant_id,participant_entity_id,participant_name_ja,participant_role,
                       event_certainty,event_verification_status,
                       occurrence_certainty,occurrence_verification_status,
                       participant_certainty,participant_verification_status
                FROM v_event_history
                WHERE event_id='event-crossing-with-traveler'
                """
            ).fetchone()
            connection.close()

            self.assertEqual(row, (
                "event-crossing-with-traveler", "旅人ありの世界移動", "multiverse_transition", expected["destination_continuity_id"],
                "occurrence-crossing-with-traveler", expected["work_id"], expected["work_title_ja"], "depicted",
                "event-participant-traveler", expected["entity_id"], expected["entity_name_ja"], "traveler",
                "confirmed", "legacy_seed", "confirmed", "legacy_seed", "confirmed", "legacy_seed",
            ))

    def test_event_history_keeps_occurrence_when_no_participant_is_known(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            row = connection.execute(
                """
                SELECT event_occurrence_id,event_participant_id,participant_entity_id,participant_role
                FROM v_event_history
                WHERE event_id='event-crossing-without-traveler'
                """
            ).fetchone()
            connection.close()
            self.assertEqual(row, ("occurrence-crossing-without-traveler", None, None, None))

    def test_multiverse_crossings_exposes_continuities_occurrence_and_participant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, expected = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            row = connection.execute(
                """
                SELECT transition_id,transition_event_name_ja,
                       source_continuity_id,source_continuity_label_ja,
                       destination_continuity_id,destination_continuity_label_ja,
                       transition_kind,event_occurrence_id,work_id,occurrence_kind,
                       transition_participant_id,participant_entity_id,participant_name_ja,participant_entity_type,
                       participant_role,identity_certainty,
                       transition_verification_status,event_verification_status,
                       occurrence_verification_status,participant_verification_status
                FROM v_multiverse_crossings
                WHERE transition_id='event-crossing-with-traveler'
                """
            ).fetchone()
            connection.close()

            self.assertEqual(row, (
                "event-crossing-with-traveler", "旅人ありの世界移動",
                expected["source_continuity_id"], expected["source_label_ja"],
                expected["destination_continuity_id"], expected["destination_label_ja"],
                "physical_crossing", "occurrence-crossing-with-traveler", expected["work_id"], "depicted",
                "transition-participant-traveler", expected["entity_id"], expected["entity_name_ja"],
                _rows(root / "data/library/entities.csv")[0]["entity_type"], "traveler", "confirmed",
                "legacy_seed", "legacy_seed", "legacy_seed", "legacy_seed",
            ))

    def test_multiverse_crossings_keeps_transition_without_known_participant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT transition_id,event_occurrence_id,transition_participant_id,participant_entity_id,participant_role
                FROM v_multiverse_crossings
                WHERE transition_id='event-crossing-without-traveler'
                ORDER BY transition_id,event_occurrence_id,transition_participant_id
                """
            ).fetchall()
            connection.close()
            self.assertEqual(rows, [(
                "event-crossing-without-traveler",
                "occurrence-crossing-without-traveler",
                None,
                None,
                None,
            )])


if __name__ == "__main__":
    unittest.main()
