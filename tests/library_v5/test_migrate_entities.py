import unittest


SOURCES = [
    {"source_id": "doomsday-cast", "url": "https://example.test/doomsday"},
    {"source_id": "bnd-cast", "url": "https://example.test/bnd"},
]


class EntityMigrationTests(unittest.TestCase):
    def test_char_links_become_deduplicated_entities_and_appearance_seeds(self):
        from scripts.library_v5.migrate_entities import normalize_entity_seeds

        char_links = [
            {"character": "トニー・スターク／アイアンマン", "work_id": "iron-man-2008", "title_ja": "アイアンマン", "title_en": "Iron Man", "verification_status": "legacy_seed", "legacy_source": "index.html:CHAR_LINKS"},
            {"character": "トニー・スターク／アイアンマン", "work_id": "iron-man-2008", "title_ja": "アイアンマン", "title_en": "Iron Man", "verification_status": "legacy_seed", "legacy_source": "index.html:CHAR_LINKS"},
        ]
        result = normalize_entity_seeds(char_links, [], SOURCES)
        self.assertEqual(len(result["entities"]), 1)
        self.assertEqual(len(result["appearances"]), 1)
        self.assertEqual(result["appearances"][0]["verification_status"], "legacy_seed")
        self.assertEqual(len(result["dispositions"]), 2)

    def test_grouped_return_row_is_split_only_by_explicit_override(self):
        from scripts.library_v5.migrate_entities import normalize_entity_seeds

        returns = [{
            "target_work_id": "avengers-doomsday-2026-12-18",
            "entity": "シュリ／エムバク／ネイモア",
            "representative_prior_work_id": "black-panther-wakanda-forever-2022",
            "evidence": "official Wakanda return teaser / cast",
            "continuity_certainty": "same_or_intended",
            "source_url": "https://example.test/doomsday",
            "verification_status": "legacy_seed",
            "legacy_source": "data/entity_returns.csv",
        }]
        result = normalize_entity_seeds([], returns, SOURCES)
        names = {row["name_ja"] for row in result["entities"]}
        self.assertEqual(names, {"シュリ", "エムバク", "ネイモア"})
        self.assertEqual(len(result["appearances"]), 3)

    def test_parenthetical_performer_creates_portrayal_without_collapsing_identity(self):
        from scripts.library_v5.migrate_entities import normalize_entity_seeds

        returns = [{
            "target_work_id": "spider-man-brand-new-day-2026-07-31",
            "entity": "フランク・キャッスル（Jon Bernthal）",
            "representative_prior_work_id": "the-punisher-one-last-kill-2026-05-12",
            "evidence": "Sony official cast list confirms Jon Bernthal",
            "continuity_certainty": "same_or_intended",
            "source_url": "https://example.test/bnd",
            "verification_status": "legacy_seed",
            "legacy_source": "data/entity_returns.csv",
        }]
        result = normalize_entity_seeds([], returns, SOURCES)
        self.assertEqual([row["name"] for row in result["people"]], ["Jon Bernthal"])
        self.assertEqual(len(result["portrayals"]), 1)
        self.assertNotEqual(result["portrayals"][0]["entity_id"], "")
        self.assertEqual(result["entity_relations"], [])

    def test_unknown_role_records_person_but_does_not_invent_entity(self):
        from scripts.library_v5.migrate_entities import normalize_entity_seeds

        returns = [{
            "target_work_id": "spider-man-brand-new-day-2026-07-31",
            "entity": "Mark Ruffalo（役名は当該Sony資料では明記なし）",
            "representative_prior_work_id": "she-hulk-attorney-at-law-2022",
            "evidence": "Sony official cast list confirms Mark Ruffalo",
            "continuity_certainty": "role_not_explicit_in_source",
            "source_url": "https://example.test/bnd",
            "verification_status": "legacy_seed",
            "legacy_source": "data/entity_returns.csv",
        }]
        result = normalize_entity_seeds([], returns, SOURCES)
        self.assertEqual(result["entities"], [])
        self.assertEqual(result["appearances"], [])
        self.assertEqual(result["people"][0]["name"], "Mark Ruffalo")
        self.assertEqual(result["portrayals"][0]["entity_id"], "")
        self.assertEqual(result["portrayals"][0]["portrayal_kind"], "unknown_role")

    def test_same_performer_different_entities_never_creates_identity_relation(self):
        from scripts.library_v5.migrate_entities import normalize_entity_seeds

        rows = [
            {"target_work_id": "work-a", "entity": "Tony Stark（Robert Downey Jr.）", "representative_prior_work_id": "older-a", "evidence": "cast", "continuity_certainty": "same_or_intended", "source_url": "https://example.test/doomsday", "verification_status": "legacy_seed", "legacy_source": "data/entity_returns.csv"},
            {"target_work_id": "work-b", "entity": "Doctor Doom（Robert Downey Jr.）", "representative_prior_work_id": "older-b", "evidence": "cast", "continuity_certainty": "unknown", "source_url": "https://example.test/doomsday", "verification_status": "legacy_seed", "legacy_source": "data/entity_returns.csv"},
        ]
        result = normalize_entity_seeds([], rows, SOURCES)
        self.assertEqual(len(result["people"]), 1)
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(result["entity_relations"], [])
        self.assertNotEqual(result["portrayals"][0]["entity_id"], result["portrayals"][1]["entity_id"])

    def test_return_evidence_links_to_registered_source(self):
        from scripts.library_v5.migrate_entities import normalize_entity_seeds

        returns = [{
            "target_work_id": "avengers-doomsday-2026-12-18",
            "entity": "サイクロップス",
            "representative_prior_work_id": "x-men-the-last-stand-2006",
            "evidence": "James Marsden cast confirmed",
            "continuity_certainty": "unknown",
            "source_url": "https://example.test/doomsday",
            "verification_status": "legacy_seed",
            "legacy_source": "data/entity_returns.csv",
        }]
        result = normalize_entity_seeds([], returns, SOURCES)
        self.assertTrue(result["evidence"])
        self.assertTrue(all(row["source_id"] == "doomsday-cast" for row in result["evidence"]))


if __name__ == "__main__":
    unittest.main()
