import unittest


class WorkRelationMigrationTests(unittest.TestCase):
    def test_work_ids_are_preserved_and_view_placement_fields_are_removed(self):
        from scripts.library_v5.migrate_works_relations import migrate_works

        rows = [
            {
                "work_id": "iron-man-2008",
                "title_ja": "アイアンマン",
                "title_en": "Iron Man",
                "title_official": "アイアンマン",
                "format": "film",
                "status": "released",
                "release_sort_date": "2008-05-02",
                "release_display_date": "2008.05.02",
                "chronology_lane": "mcu-main",
                "chronology_order": "30",
                "priority": "MAIN",
                "classification": "Phase 1",
            }
        ]
        migrated = migrate_works(rows)
        self.assertEqual([row["work_id"] for row in migrated], ["iron-man-2008"])
        self.assertNotIn("chronology_lane", migrated[0])
        self.assertNotIn("chronology_order", migrated[0])
        self.assertNotIn("priority", migrated[0])
        self.assertEqual(migrated[0]["classification"], "Phase 1")

    def test_direct_sequel_becomes_explicit_work_relation_seed(self):
        from scripts.library_v5.migrate_works_relations import migrate_connections

        rows = [{
            "edge_id": "a -> b",
            "source_id": "a",
            "target_id": "b",
            "relation_scope": "story",
            "relation_kind": "sequel",
            "directness": "direct",
            "continuity_scope": "same_or_intended",
            "audit_confidence": "high",
            "reason": "direct sequel",
            "prewatch_tier": "minimum",
        }]
        result = migrate_connections(rows)
        self.assertEqual(len(result["work_relations"]), 1)
        self.assertEqual(result["work_relations"][0]["relation_kind"], "sequel")
        self.assertEqual(result["work_relations"][0]["verification_status"], "legacy_seed")
        self.assertNotIn("prewatch_tier", result["work_relations"][0])
        self.assertEqual(result["dispositions"][0]["disposition"], "migrated_explicit_relation")

    def test_character_only_connection_is_not_duplicated_as_explicit_relation(self):
        from scripts.library_v5.migrate_works_relations import migrate_connections

        rows = [{
            "edge_id": "a -> b",
            "source_id": "a",
            "target_id": "b",
            "relation_scope": "character",
            "relation_kind": "character_continuity",
            "directness": "proxy",
            "continuity_scope": "same_or_intended",
            "audit_confidence": "medium",
            "reason": "same character returns",
        }]
        result = migrate_connections(rows)
        self.assertEqual(result["work_relations"], [])
        self.assertEqual(result["dispositions"][0]["disposition"], "appearance_derived_pending_audit")

    def test_promotion_is_preserved_as_promotion_seed_not_prewatch_policy(self):
        from scripts.library_v5.migrate_works_relations import migrate_connections

        rows = [{
            "edge_id": "a -> b",
            "source_id": "a",
            "target_id": "b",
            "relation_scope": "promotion",
            "relation_kind": "promotion",
            "directness": "promotional",
            "continuity_scope": "promotional",
            "audit_confidence": "high",
            "reason": "official related-title campaign",
            "prewatch_tier": "complete",
        }]
        result = migrate_connections(rows)
        self.assertEqual(len(result["work_relations"]), 1)
        self.assertEqual(result["work_relations"][0]["relation_scope"], "promotion")
        self.assertEqual(result["work_relations"][0]["verification_status"], "legacy_seed")
        self.assertEqual(result["dispositions"][0]["disposition"], "migrated_promotion_fact")

    def test_cancelled_wonder_man_s2_edge_is_explicitly_rejected(self):
        from scripts.library_v5.migrate_works_relations import migrate_connections

        rows = [{
            "edge_id": "wonder-man-s1-2026 -> wonder-man-s2-2027",
            "source_id": "wonder-man-s1-2026",
            "target_id": "wonder-man-s2-2027",
            "relation_scope": "story",
            "relation_kind": "sequel",
            "directness": "direct",
            "continuity_scope": "same_or_intended",
            "audit_confidence": "medium",
            "reason": "legacy planned season",
        }]
        result = migrate_connections(rows)
        self.assertEqual(result["work_relations"], [])
        self.assertEqual(result["dispositions"][0]["disposition"], "rejected_superseded")
        self.assertIn("cancel", result["dispositions"][0]["migration_note"].lower())

    def test_chronology_display_rows_do_not_become_unverified_order_assertions(self):
        from scripts.library_v5.migrate_works_relations import migrate_chronology

        rows = [
            {"work_id": "x-men-2000", "world_group": "FOX X-MEN", "lane": "fox-xmen", "order": "30", "track": "original", "certainty": "confirmed", "note": "旧系列。"},
            {"work_id": "x2-x-men-united-2003", "world_group": "FOX X-MEN", "lane": "fox-xmen", "order": "40", "track": "original", "certainty": "confirmed", "note": "旧系列。"},
        ]
        result = migrate_chronology(rows)
        self.assertEqual(len(result["continuities"]), 1)
        self.assertEqual(len(result["work_continuities"]), 2)
        self.assertEqual(result["chronology_assertions"], [])
        self.assertTrue(all(row["disposition"] == "legacy_display_placement_seed" for row in result["dispositions"]))


if __name__ == "__main__":
    unittest.main()
