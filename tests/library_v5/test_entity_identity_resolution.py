import unittest


class EntityIdentityResolutionTests(unittest.TestCase):
    def test_identity_of_collapses_legacy_alias_for_shared_entity_derivation(self):
        from scripts.library_v5.derive_edges import derive_reasons

        works = [
            {"work_id": "the-punisher-one-last-kill-2026-05-12", "release_sort_date": "2026-05-12"},
            {"work_id": "spider-man-brand-new-day-2026-07-31", "release_sort_date": "2026-07-31"},
        ]
        appearances = [
            {
                "appearance_id": "ap-punisher-canonical",
                "work_id": "the-punisher-one-last-kill-2026-05-12",
                "entity_id": "entity-frank-castle-canonical",
                "appearance_kind": "onscreen",
                "certainty": "confirmed",
                "verification_status": "source_verified",
            },
            {
                "appearance_id": "ap-bnd-legacy-alias",
                "work_id": "spider-man-brand-new-day-2026-07-31",
                "entity_id": "entity-frank-castle-legacy-alias",
                "appearance_kind": "onscreen",
                "certainty": "confirmed",
                "verification_status": "source_verified",
            },
        ]
        identity = [{
            "entity_relation_id": "er-frank-alias-identity",
            "source_entity_id": "entity-frank-castle-legacy-alias",
            "relation_kind": "identity_of",
            "target_entity_id": "entity-frank-castle-canonical",
            "certainty": "confirmed",
            "verification_status": "source_verified",
        }]

        reasons = derive_reasons(works, appearances, [], identity, mode="all_pairs")
        shared = [row for row in reasons if row["reason_kind"] == "shared_entity"]
        self.assertEqual(len(shared), 1)
        self.assertEqual(shared[0]["entity_id"], "entity-frank-castle-canonical")
        self.assertEqual(
            shared[0]["support_fact_ids"],
            "ap-bnd-legacy-alias|ap-punisher-canonical",
        )

    def test_variant_of_does_not_collapse_without_variant_opt_in(self):
        from scripts.library_v5.derive_edges import derive_reasons

        works = [
            {"work_id": "a", "release_sort_date": "2020-01-01"},
            {"work_id": "b", "release_sort_date": "2021-01-01"},
        ]
        appearances = [
            {"appearance_id": "ap-a", "work_id": "a", "entity_id": "e1", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
            {"appearance_id": "ap-b", "work_id": "b", "entity_id": "e2", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
        ]
        relations = [{"entity_relation_id": "er-v", "source_entity_id": "e1", "relation_kind": "variant_of", "target_entity_id": "e2", "certainty": "confirmed", "verification_status": "source_verified"}]
        reasons = derive_reasons(works, appearances, [], relations, mode="all_pairs", include_variants=False)
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
