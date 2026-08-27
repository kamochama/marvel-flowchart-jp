from __future__ import annotations

import sqlite3
import unittest

from scripts.library_v5.db_schema import create_schema
from scripts.library_v5.db_views import PUBLIC_VIEW_NAMES, install_internal_helpers, install_public_views


def _phase2_fixture() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    create_schema(db)
    db.execute(
        "INSERT INTO works(work_id,title_ja,title_en,format,status,release_sort_date,release_display_date) VALUES(?,?,?,?,?,?,?)",
        ("work-thunderbolts", "サンダーボルツ*", "Thunderbolts*", "film", "released", "2025-05-02", "2025-05-02"),
    )
    db.executemany(
        "INSERT INTO continuities(continuity_id,label_ja,label_en,continuity_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        [
            ("continuity-earth-828", "Earth-828", "Earth-828", "universe", "confirmed", "source_verified", ""),
            ("continuity-earth-616", "MCU本流", "Earth-616 / MCU main", "universe", "confirmed", "source_verified", ""),
        ],
    )
    db.execute(
        "INSERT INTO entities(entity_id,name_ja,name_en,entity_type,notes) VALUES(?,?,?,?,?)",
        ("entity-f4-ship", "ファンタスティック・フォーの宇宙船", "Fantastic Four ship", "vehicle", ""),
    )
    db.execute(
        "INSERT INTO events(event_id,name_ja,name_en,event_kind,primary_continuity_id,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?,?)",
        ("event-f4-arrival", "F4船の到着", "Fantastic Four ship arrival", "multiverse_transition", None, "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO event_occurrences(event_occurrence_id,event_id,work_id,occurrence_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("occurrence-f4-arrival", "event-f4-arrival", "work-thunderbolts", "post_credit", "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO event_participants(event_participant_id,event_id,entity_id,participant_role,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("event-participant-f4-ship", "event-f4-arrival", "entity-f4-ship", "vehicle", "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO multiverse_transitions(transition_id,source_continuity_id,destination_continuity_id,transition_kind,direction_certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("event-f4-arrival", "continuity-earth-828", "continuity-earth-616", "physical_crossing", "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO transition_participants(transition_participant_id,transition_id,entity_id,participant_role,identity_certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("transition-participant-f4-ship", "event-f4-arrival", "entity-f4-ship", "vehicle", "confirmed", "source_verified", ""),
    )
    install_internal_helpers(db)
    install_public_views(db)
    return db


class Phase2PublicViewTests(unittest.TestCase):
    def test_public_view_registry_includes_event_and_crossing_views(self) -> None:
        self.assertIn("v_event_history", PUBLIC_VIEW_NAMES)
        self.assertIn("v_multiverse_crossings", PUBLIC_VIEW_NAMES)

    def test_event_history_preserves_occurrence_participant_and_verification_metadata(self) -> None:
        db = _phase2_fixture()
        row = db.execute(
            """
            SELECT event_id,event_name_en,event_kind,containing_work_id,occurrence_kind,
                   participant_entity_id,participant_role,event_verification_status,
                   occurrence_verification_status,participant_verification_status
            FROM v_event_history
            WHERE event_id='event-f4-arrival'
            """
        ).fetchone()
        self.assertEqual(row, (
            "event-f4-arrival", "Fantastic Four ship arrival", "multiverse_transition",
            "work-thunderbolts", "post_credit", "entity-f4-ship", "vehicle",
            "source_verified", "source_verified", "source_verified",
        ))
        db.close()

    def test_multiverse_crossing_view_preserves_direction_context_and_participant(self) -> None:
        db = _phase2_fixture()
        row = db.execute(
            """
            SELECT transition_id,source_continuity_id,source_continuity_label_en,
                   destination_continuity_id,destination_continuity_label_en,transition_kind,
                   containing_work_id,occurrence_kind,participant_entity_id,participant_entity_type,
                   participant_role,identity_certainty,transition_verification_status
            FROM v_multiverse_crossings
            WHERE transition_id='event-f4-arrival'
            """
        ).fetchone()
        self.assertEqual(row, (
            "event-f4-arrival", "continuity-earth-828", "Earth-828",
            "continuity-earth-616", "Earth-616 / MCU main", "physical_crossing",
            "work-thunderbolts", "post_credit", "entity-f4-ship", "vehicle", "vehicle",
            "confirmed", "source_verified",
        ))
        db.close()

    def test_transition_without_known_participant_still_appears(self) -> None:
        db = _phase2_fixture()
        db.execute(
            "INSERT INTO events(event_id,name_ja,name_en,event_kind,primary_continuity_id,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?,?)",
            ("event-unknown-traveler", "参加者不明の越境", "Crossing with unknown traveler", "multiverse_transition", None, "confirmed", "legacy_seed", ""),
        )
        db.execute(
            "INSERT INTO multiverse_transitions(transition_id,source_continuity_id,destination_continuity_id,transition_kind,direction_certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
            ("event-unknown-traveler", "continuity-earth-828", "continuity-earth-616", "portal", "probable", "legacy_seed", ""),
        )
        row = db.execute(
            "SELECT transition_id,participant_entity_id,participant_role,containing_work_id FROM v_multiverse_crossings WHERE transition_id='event-unknown-traveler'"
        ).fetchone()
        self.assertEqual(row, ("event-unknown-traveler", None, None, None))
        db.close()


if __name__ == "__main__":
    unittest.main()
