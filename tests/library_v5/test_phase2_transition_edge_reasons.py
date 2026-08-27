from __future__ import annotations

import sqlite3
import unittest

from scripts.library_v5.db_schema import create_schema
from scripts.library_v5.db_transition_reasons import install_transition_reason_views
from scripts.library_v5.db_views import install_internal_helpers, install_public_views


def _fixture() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    create_schema(db)
    db.executemany(
        "INSERT INTO works(work_id,title_ja,title_en,format,status,release_sort_date,release_display_date) VALUES(?,?,?,?,?,?,?)",
        [
            ("work-origin", "出発元作品", "Origin Work", "film", "released", "2024-01-01", "2024-01-01"),
            ("work-containing", "越境描写作品", "Containing Work", "film", "released", "2025-01-01", "2025-01-01"),
            ("work-unrelated", "無関係作品", "Unrelated Work", "film", "released", "2023-01-01", "2023-01-01"),
            ("work-same-source-no-relation", "同じ出発宇宙の別作品", "Same-source Work", "film", "released", "2022-01-01", "2022-01-01"),
        ],
    )
    db.executemany(
        "INSERT INTO continuities(continuity_id,label_ja,label_en,continuity_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        [
            ("continuity-source", "出発宇宙", "Source Universe", "universe", "confirmed", "source_verified", ""),
            ("continuity-destination", "到着宇宙", "Destination Universe", "universe", "confirmed", "source_verified", ""),
            ("continuity-other", "別宇宙", "Other Universe", "universe", "confirmed", "source_verified", ""),
        ],
    )
    db.executemany(
        "INSERT INTO work_continuities(work_continuity_id,work_id,continuity_id,relation_to_continuity,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        [
            ("wc-origin", "work-origin", "continuity-source", "setting", "confirmed", "source_verified", ""),
            ("wc-containing", "work-containing", "continuity-destination", "setting", "confirmed", "source_verified", ""),
            ("wc-unrelated", "work-unrelated", "continuity-other", "setting", "confirmed", "source_verified", ""),
            ("wc-same-source", "work-same-source-no-relation", "continuity-source", "setting", "confirmed", "source_verified", ""),
        ],
    )
    db.execute(
        "INSERT INTO entities(entity_id,name_ja,name_en,entity_type,notes) VALUES(?,?,?,?,?)",
        ("entity-traveler", "越境者", "Traveler", "character", ""),
    )
    db.execute(
        "INSERT INTO appearances(appearance_id,work_id,entity_id,appearance_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("appearance-traveler-origin", "work-origin", "entity-traveler", "onscreen", "confirmed", "source_verified", ""),
    )
    db.executemany(
        "INSERT INTO work_relations(work_relation_id,source_work_id,target_work_id,relation_kind,relation_scope,directness,continuity_scope,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",
        [
            ("relation-origin-containing", "work-origin", "work-containing", "crossover", "crossover", "direct", "multiverse", "confirmed", "source_verified", ""),
            ("relation-unrelated-containing", "work-unrelated", "work-containing", "crossover", "crossover", "direct", "multiverse", "confirmed", "legacy_seed", ""),
        ],
    )
    db.execute(
        "INSERT INTO events(event_id,name_ja,name_en,event_kind,primary_continuity_id,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?,?)",
        ("event-crossing", "越境", "Crossing", "multiverse_transition", None, "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO event_occurrences(event_occurrence_id,event_id,work_id,occurrence_kind,certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("occurrence-crossing", "event-crossing", "work-containing", "depicted", "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO multiverse_transitions(transition_id,source_continuity_id,destination_continuity_id,transition_kind,direction_certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("event-crossing", "continuity-source", "continuity-destination", "physical_crossing", "confirmed", "source_verified", ""),
    )
    db.execute(
        "INSERT INTO transition_participants(transition_participant_id,transition_id,entity_id,participant_role,identity_certainty,verification_status,notes) VALUES(?,?,?,?,?,?,?)",
        ("transition-participant-traveler", "event-crossing", "entity-traveler", "traveler", "confirmed", "source_verified", ""),
    )
    install_internal_helpers(db)
    install_public_views(db)
    install_transition_reason_views(db)
    return db


class Phase2TransitionEdgeReasonTests(unittest.TestCase):
    def test_transition_adds_reason_only_to_explainable_existing_multiverse_pair(self) -> None:
        db = _fixture()
        reasons = db.execute(
            """
            SELECT source_work_id,target_work_id,reason_kind,relation_id,support_fact_ids,
                   verification_statuses,certainty_values,notes,reason_discriminator
            FROM v_work_connection_reasons
            WHERE reason_kind='multiverse_transition'
            ORDER BY source_work_id,target_work_id
            """
        ).fetchall()
        self.assertEqual(len(reasons), 1)
        row = reasons[0]
        self.assertEqual(row[0:4], ("work-origin", "work-containing", "multiverse_transition", ""))
        self.assertEqual(set(row[4].split("|")), {"event-crossing", "occurrence-crossing", "transition-participant-traveler"})
        self.assertEqual(row[5], "source_verified")
        self.assertEqual(row[6], "confirmed")
        self.assertIn("continuity-source->continuity-destination", row[7])
        self.assertIn("physical_crossing", row[7])
        self.assertIn("transition-participant-traveler", row[7])
        self.assertEqual(row[8], "event-crossing")
        db.close()

    def test_explicit_relation_reason_is_retained_during_transition_migration(self) -> None:
        db = _fixture()
        kinds = {
            row[0]
            for row in db.execute(
                "SELECT reason_kind FROM v_work_connection_reasons WHERE source_work_id='work-origin' AND target_work_id='work-containing'"
            )
        }
        self.assertIn("explicit_relation", kinds)
        self.assertIn("multiverse_transition", kinds)
        db.close()

    def test_transition_does_not_create_pair_from_shared_continuity_alone(self) -> None:
        db = _fixture()
        row = db.execute(
            """
            SELECT 1 FROM v_work_connection_reasons
            WHERE reason_kind='multiverse_transition'
              AND source_work_id='work-same-source-no-relation'
              AND target_work_id='work-containing'
            """
        ).fetchone()
        self.assertIsNone(row)
        db.close()

    def test_unrelated_active_multiverse_relation_does_not_receive_transition_reason(self) -> None:
        db = _fixture()
        row = db.execute(
            """
            SELECT 1 FROM v_work_connection_reasons
            WHERE reason_kind='multiverse_transition'
              AND source_work_id='work-unrelated'
              AND target_work_id='work-containing'
            """
        ).fetchone()
        self.assertIsNone(row)
        db.close()


if __name__ == "__main__":
    unittest.main()
