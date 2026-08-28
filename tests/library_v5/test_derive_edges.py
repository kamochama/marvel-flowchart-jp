import unittest


WORKS = [
    {"work_id": "a", "release_sort_date": "2008-01-01"},
    {"work_id": "b", "release_sort_date": "2010-01-01"},
    {"work_id": "c", "release_sort_date": "2012-01-01"},
    {"work_id": "d", "release_sort_date": "2014-01-01"},
]
APPEARANCES = [
    {"appearance_id": "ap-a", "work_id": "a", "entity_id": "entity-hero", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
    {"appearance_id": "ap-b", "work_id": "b", "entity_id": "entity-hero", "appearance_kind": "post_credit", "certainty": "confirmed", "verification_status": "source_verified"},
    {"appearance_id": "ap-c", "work_id": "c", "entity_id": "entity-hero", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
    {"appearance_id": "ap-d", "work_id": "d", "entity_id": "entity-hero", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
]


class EdgeDerivationTests(unittest.TestCase):
    def test_all_pairs_yields_every_shared_entity_work_pair(self):
        from scripts.library_v5.derive_edges import derive_reasons

        reasons = derive_reasons(WORKS, APPEARANCES, [], [], mode="all_pairs")
        pairs = {(row["source_work_id"], row["target_work_id"]) for row in reasons}
        self.assertEqual(pairs, {("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("b", "d"), ("c", "d")})
        self.assertTrue(all(row["reason_kind"] == "shared_entity" for row in reasons))

    def test_shared_entity_reason_preserves_source_fact_ids_kinds_and_statuses(self):
        from scripts.library_v5.derive_edges import derive_reasons

        reasons = derive_reasons(WORKS[:2], APPEARANCES[:2], [], [], mode="all_pairs")
        self.assertEqual(len(reasons), 1)
        reason = reasons[0]
        self.assertEqual(reason["support_fact_ids"], "ap-a|ap-b")
        self.assertEqual(reason["appearance_kinds"], "onscreen|post_credit")
        self.assertEqual(reason["verification_statuses"], "source_verified")
        self.assertEqual(reason["certainty_values"], "confirmed")

    def test_adjacent_release_yields_only_consecutive_appearances(self):
        from scripts.library_v5.derive_edges import derive_reasons

        reasons = derive_reasons(WORKS, APPEARANCES, [], [], mode="adjacent_release")
        pairs = [(row["source_work_id"], row["target_work_id"]) for row in reasons]
        self.assertEqual(pairs, [("a", "b"), ("b", "c"), ("c", "d")])

    def test_explicit_relation_and_shared_entity_reasons_coexist(self):
        from scripts.library_v5.derive_edges import derive_reasons, collapse_reasons_to_edges

        explicit = [{
            "work_relation_id": "wr-a-b",
            "source_work_id": "a",
            "target_work_id": "b",
            "relation_kind": "sequel",
            "relation_scope": "story",
            "directness": "direct",
            "continuity_scope": "same_or_intended",
            "certainty": "confirmed",
            "verification_status": "source_verified",
        }]
        reasons = derive_reasons(WORKS[:2], APPEARANCES[:2], explicit, [], mode="combined_all_pairs")
        ab = [r for r in reasons if r["source_work_id"] == "a" and r["target_work_id"] == "b"]
        self.assertEqual({r["reason_kind"] for r in ab}, {"shared_entity", "explicit_relation"})
        explicit_reason = next(r for r in ab if r["reason_kind"] == "explicit_relation")
        self.assertEqual(explicit_reason["support_fact_ids"], "wr-a-b")
        self.assertEqual(explicit_reason["verification_statuses"], "source_verified")
        self.assertEqual(explicit_reason["certainty_values"], "confirmed")
        edges = collapse_reasons_to_edges(reasons)
        self.assertEqual(len(edges), 1)
        self.assertEqual(len(edges[0]["reason_ids"].split("|")), 2)

    def test_same_performer_different_entities_never_creates_character_reason(self):
        from scripts.library_v5.derive_edges import derive_reasons

        appearances = [
            {"appearance_id": "ap-tony", "work_id": "a", "entity_id": "entity-tony-stark", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
            {"appearance_id": "ap-doom", "work_id": "b", "entity_id": "entity-doctor-doom", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
        ]
        portrayals = [
            {"work_id": "a", "person_id": "person-rdj", "entity_id": "entity-tony-stark"},
            {"work_id": "b", "person_id": "person-rdj", "entity_id": "entity-doctor-doom"},
        ]
        reasons = derive_reasons(WORKS[:2], appearances, [], [], mode="all_pairs", portrayals=portrayals)
        self.assertEqual(reasons, [])

    def test_variant_relation_is_opt_in(self):
        from scripts.library_v5.derive_edges import derive_reasons

        appearances = [
            {"appearance_id": "ap-main", "work_id": "a", "entity_id": "entity-prof-x-main", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
            {"appearance_id": "ap-variant", "work_id": "b", "entity_id": "entity-prof-x-variant", "appearance_kind": "onscreen", "certainty": "confirmed", "verification_status": "source_verified"},
        ]
        entity_relations = [{
            "entity_relation_id": "er-1",
            "source_entity_id": "entity-prof-x-variant",
            "relation_kind": "variant_of",
            "target_entity_id": "entity-prof-x-main",
            "certainty": "confirmed",
            "verification_status": "source_verified",
        }]
        self.assertEqual(derive_reasons(WORKS[:2], appearances, [], entity_relations, mode="all_pairs"), [])
        reasons = derive_reasons(WORKS[:2], appearances, [], entity_relations, mode="all_pairs", include_variants=True)
        self.assertEqual(len(reasons), 1)
        self.assertEqual(reasons[0]["reason_kind"], "variant_entity")

    def test_distinct_sources_into_same_target_remain_distinct_edges(self):
        from scripts.library_v5.derive_edges import collapse_reasons_to_edges

        reasons = [
            {"reason_id": "r1", "source_work_id": "a", "target_work_id": "d", "reason_kind": "shared_entity", "entity_id": "e1", "relation_id": "", "notes": ""},
            {"reason_id": "r2", "source_work_id": "b", "target_work_id": "d", "reason_kind": "shared_entity", "entity_id": "e2", "relation_id": "", "notes": ""},
            {"reason_id": "r3", "source_work_id": "c", "target_work_id": "d", "reason_kind": "explicit_relation", "entity_id": "", "relation_id": "wr", "notes": ""},
        ]
        edges = collapse_reasons_to_edges(reasons)
        self.assertEqual({(e["source_work_id"], e["target_work_id"]) for e in edges}, {("a", "d"), ("b", "d"), ("c", "d")})

    def test_target_centric_returns_all_prior_shared_entity_sources_for_target(self):
        from scripts.library_v5.derive_edges import derive_reasons

        reasons = derive_reasons(WORKS, APPEARANCES, [], [], mode="target_centric", target_work_id="d")
        self.assertEqual({(r["source_work_id"], r["target_work_id"]) for r in reasons}, {("a", "d"), ("b", "d"), ("c", "d")})

    def test_output_order_and_ids_are_deterministic(self):
        from scripts.library_v5.derive_edges import derive_reasons

        forward = derive_reasons(WORKS, APPEARANCES, [], [], mode="all_pairs")
        reverse = derive_reasons(list(reversed(WORKS)), list(reversed(APPEARANCES)), [], [], mode="all_pairs")
        self.assertEqual(forward, reverse)
        self.assertEqual(len({r["reason_id"] for r in forward}), len(forward))


if __name__ == "__main__":
    unittest.main()
