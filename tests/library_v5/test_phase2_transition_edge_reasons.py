from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_export import export_work_graph


ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "data" / "library"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _append(path: Path, rows: list[dict[str, str]]) -> None:
    header, existing = _read(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in header})


def _replace(path: Path, rows: list[dict[str, str]]) -> None:
    header, _ = _read(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in header})


def _fixture(root: Path) -> Path:
    shutil.copytree(LIBRARY, root / "data" / "library")
    reviews = root / "data" / "content_audit" / "reviews.csv"
    reviews.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data" / "content_audit" / "reviews.csv", reviews)

    _append(root / "data/library/works.csv", [
        {
            "work_id": "work-transition-origin-context",
            "title_ja": "移動元作品",
            "title_en": "Origin Context Work",
            "format": "film",
            "status": "released",
            "release_sort_date": "2090-01-01",
            "release_display_date": "2090-01-01",
        },
        {
            "work_id": "work-transition-containing",
            "title_ja": "移動描写作品",
            "title_en": "Containing Work",
            "format": "film",
            "status": "released",
            "release_sort_date": "2091-01-01",
            "release_display_date": "2091-01-01",
        },
        {
            "work_id": "work-transition-unrelated",
            "title_ja": "未支持作品",
            "title_en": "Unsupported Work",
            "format": "film",
            "status": "released",
            "release_sort_date": "2092-01-01",
            "release_display_date": "2092-01-01",
        },
    ])
    _append(root / "data/library/entities.csv", [
        {"entity_id": "entity-transition-a", "name_ja": "旅人A", "name_en": "Traveler A", "entity_type": "character", "notes": ""},
        {"entity_id": "entity-transition-b", "name_ja": "旅人B", "name_en": "Traveler B", "entity_type": "character", "notes": ""},
    ])
    _append(root / "data/library/continuities.csv", [
        {"continuity_id": "continuity-transition-origin", "label_ja": "移動元世界", "label_en": "Origin Universe", "continuity_kind": "universe", "certainty": "confirmed", "verification_status": "legacy_seed", "notes": ""},
        {"continuity_id": "continuity-transition-destination", "label_ja": "移動先世界", "label_en": "Destination Universe", "continuity_kind": "universe", "certainty": "confirmed", "verification_status": "legacy_seed", "notes": ""},
    ])
    _append(root / "data/library/work_continuities.csv", [
        {
            "work_continuity_id": "work-continuity-transition-origin-context",
            "work_id": "work-transition-origin-context",
            "continuity_id": "continuity-transition-origin",
            "relation_to_continuity": "setting",
            "certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "",
        },
        {
            "work_continuity_id": "work-continuity-transition-unrelated",
            "work_id": "work-transition-unrelated",
            "continuity_id": "continuity-transition-origin",
            "relation_to_continuity": "setting",
            "certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "",
        },
    ])
    _append(root / "data/library/work_relations.csv", [{
        "work_relation_id": "relation-transition-compatibility",
        "source_work_id": "work-transition-origin-context",
        "target_work_id": "work-transition-containing",
        "relation_kind": "crossover",
        "relation_scope": "crossover",
        "directness": "direct",
        "continuity_scope": "multiverse",
        "certainty": "confirmed",
        "verification_status": "legacy_seed",
        "notes": "compatibility pair",
    }])

    _replace(root / "data/library/events.csv", [{
        "event_id": "event-transition-pilot",
        "name_ja": "パイロット世界移動",
        "name_en": "Pilot crossing",
        "event_kind": "multiverse_transition",
        "primary_continuity_id": "continuity-transition-destination",
        "certainty": "confirmed",
        "verification_status": "legacy_seed",
        "notes": "event note",
    }])
    _replace(root / "data/library/event_occurrences.csv", [{
        "event_occurrence_id": "occurrence-transition-pilot",
        "event_id": "event-transition-pilot",
        "work_id": "work-transition-containing",
        "occurrence_kind": "post_credit",
        "certainty": "confirmed",
        "verification_status": "legacy_seed",
        "notes": "occurrence note",
    }])
    _replace(root / "data/library/event_participants.csv", [])
    _replace(root / "data/library/event_relations.csv", [])
    _replace(root / "data/library/multiverse_transitions.csv", [{
        "transition_id": "event-transition-pilot",
        "source_continuity_id": "continuity-transition-origin",
        "destination_continuity_id": "continuity-transition-destination",
        "transition_kind": "physical_crossing",
        "direction_certainty": "confirmed",
        "verification_status": "legacy_seed",
        "notes": "transition note",
    }])
    _replace(root / "data/library/transition_participants.csv", [
        {
            "transition_participant_id": "transition-participant-a",
            "transition_id": "event-transition-pilot",
            "entity_id": "entity-transition-a",
            "participant_role": "traveler",
            "identity_certainty": "confirmed",
            "verification_status": "legacy_seed",
            "notes": "",
        },
        {
            "transition_participant_id": "transition-participant-b",
            "transition_id": "event-transition-pilot",
            "entity_id": "entity-transition-b",
            "participant_role": "traveler",
            "identity_certainty": "probable",
            "verification_status": "legacy_seed",
            "notes": "",
        },
    ])
    return root


class Phase2TransitionEdgeReasonTests(unittest.TestCase):
    def test_transition_adds_one_reason_only_to_already_supported_context_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            reasons = connection.execute(
                """
                SELECT source_work_id,target_work_id,reason_kind,reason_discriminator
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                ORDER BY source_work_id,target_work_id,reason_discriminator
                """
            ).fetchall()
            connection.close()

            self.assertEqual(reasons, [(
                "work-transition-origin-context",
                "work-transition-containing",
                "multiverse_transition",
                "event-transition-pilot:occurrence-transition-pilot",
            )])

    def test_transition_reason_preserves_traceable_semantic_fact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            row = connection.execute(
                """
                SELECT transition_id,event_id,event_occurrence_id,
                       source_continuity_id,destination_continuity_id,
                       participant_fact_ids,support_fact_ids,
                       verification_statuses,certainty_values,notes
                FROM v_work_connection_reasons
                WHERE source_work_id='work-transition-origin-context'
                  AND target_work_id='work-transition-containing'
                  AND reason_kind='multiverse_transition'
                """
            ).fetchone()
            connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0:5], (
                "event-transition-pilot",
                "event-transition-pilot",
                "occurrence-transition-pilot",
                "continuity-transition-origin",
                "continuity-transition-destination",
            ))
            self.assertEqual(row[5], "transition-participant-a|transition-participant-b")
            support_ids = set(row[6].split("|"))
            self.assertTrue({
                "event-transition-pilot",
                "occurrence-transition-pilot",
                "work-continuity-transition-origin-context",
                "transition-participant-a",
                "transition-participant-b",
            } <= support_ids)
            self.assertIn("legacy_seed", row[7].split("|"))
            self.assertTrue({"confirmed", "probable"} <= set(row[8].split("|")))
            self.assertIn("physical_crossing", row[9])
            self.assertIn("continuity-transition-origin", row[9])
            self.assertIn("continuity-transition-destination", row[9])

    def test_export_keeps_transition_metadata_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _fixture(Path(tmp))
            temp = Path(tmp)
            db_path = compile_database(root).db_path
            export_work_graph(db_path, temp / "export-a")
            export_work_graph(db_path, temp / "export-b")

            first = (temp / "export-a/work_pair_reasons.csv").read_bytes()
            second = (temp / "export-b/work_pair_reasons.csv").read_bytes()
            self.assertEqual(first, second)

            with (temp / "export-a/work_pair_reasons.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            transition = next(row for row in rows if row["reason_kind"] == "multiverse_transition")
            self.assertEqual(transition["transition_id"], "event-transition-pilot")
            self.assertEqual(transition["event_id"], "event-transition-pilot")
            self.assertEqual(transition["event_occurrence_id"], "occurrence-transition-pilot")
            self.assertEqual(transition["source_continuity_id"], "continuity-transition-origin")
            self.assertEqual(transition["destination_continuity_id"], "continuity-transition-destination")
            self.assertEqual(transition["participant_fact_ids"], "transition-participant-a|transition-participant-b")

    def test_transition_does_not_create_pair_from_shared_continuity_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _fixture(Path(tmp))
            db_path = compile_database(root).db_path
            connection = open_query_connection(db_path)
            count = connection.execute(
                """
                SELECT count(*)
                FROM v_work_connection_reasons
                WHERE reason_kind='multiverse_transition'
                  AND (
                    source_work_id='work-transition-unrelated'
                    OR target_work_id='work-transition-unrelated'
                  )
                """
            ).fetchone()[0]
            connection.close()
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
