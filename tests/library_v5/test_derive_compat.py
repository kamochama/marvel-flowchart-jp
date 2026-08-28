import unittest


class CompatibilityDerivationTests(unittest.TestCase):
    def test_story_path_is_reproduced_only_when_derived_graph_explains_pair(self):
        from scripts.library_v5.derive_compat import derive_story_path_compat

        legacy = [
            {"path_id": "p", "edge_order": "1", "source_id": "a", "target_id": "b", "edge_id": "a -> b", "label_ja": "本線"},
            {"path_id": "p", "edge_order": "2", "source_id": "b", "target_id": "c", "edge_id": "b -> c", "label_ja": "本線"},
        ]
        derived_edges = [{"edge_id": "edge-a-b", "source_work_id": "a", "target_work_id": "b", "reason_ids": "r1", "reason_count": "1"}]
        result = derive_story_path_compat(legacy, derived_edges)
        self.assertEqual([(r["source_id"], r["target_id"]) for r in result["story_paths"]], [("a", "b")])
        self.assertEqual(result["dispositions"][0]["disposition"], "reproduced_from_v5_graph")
        self.assertEqual(result["dispositions"][1]["disposition"], "unexplained_legacy_path")

    def test_every_legacy_story_path_gets_exactly_one_disposition(self):
        from scripts.library_v5.derive_compat import derive_story_path_compat

        legacy = [{"path_id": "p", "edge_order": str(i), "source_id": f"w{i}", "target_id": f"w{i+1}", "edge_id": f"w{i} -> w{i+1}"} for i in range(4)]
        result = derive_story_path_compat(legacy, [])
        self.assertEqual(len(result["dispositions"]), len(legacy))
        self.assertEqual(len({r["legacy_row_id"] for r in result["dispositions"]}), len(legacy))

    def test_prewatch_edges_are_generated_from_legacy_policy_not_appearance_facts(self):
        from scripts.library_v5.derive_compat import derive_prewatch_compat

        legacy_connections = [
            {"edge_id": "a -> b", "source_id": "a", "target_id": "b", "prewatch_tier": "minimum", "prewatch_reason": "本筋"},
            {"edge_id": "c -> b", "source_id": "c", "target_id": "b", "prewatch_tier": "none", "prewatch_reason": ""},
        ]
        appearances = [{"appearance_id": "ap", "work_id": "a", "entity_id": "hero", "verification_status": "verified"}]
        result = derive_prewatch_compat(legacy_connections, appearances)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_work_id"], "a")
        self.assertEqual(result[0]["tier"], "minimum")
        self.assertNotIn("prewatch_tier", appearances[0])

    def test_flowchart_policy_is_view_only_and_requires_japanese_labels(self):
        from scripts.library_v5.derive_compat import default_flowchart_policy

        policy = default_flowchart_policy()
        self.assertEqual(policy["left_labels_language"], "ja")
        self.assertEqual(policy["default_edge_mode"], "combined_all_pairs")
        self.assertFalse(policy["canonical_fact_source"])
        self.assertIn("line_opacity", policy["view_only_properties"])
        self.assertIn("glow", policy["view_only_properties"])


if __name__ == "__main__":
    unittest.main()
