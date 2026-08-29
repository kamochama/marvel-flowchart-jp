from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


def function_body(source: str, name: str) -> str:
    """Return a balanced-brace JavaScript function body for source assertions."""
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", source)
    if not match:
        raise AssertionError(f"function {name} was not found")
    start = match.end() - 1
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"function {name} has unbalanced braces")


class FlowchartSelectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_overview_materializes_every_exported_edge_once_with_stable_edge_key(self) -> None:
        body = function_body(self.source, "materializeMissingMasterEdges")
        self.assertIn("#overview", body)
        self.assertIn("for(const edge of EDGES)", body)
        self.assertIn("edge.edge_id", body)
        self.assertRegex(body, r"dataset\.edgeKey\s*=\s*edge\.edge_id")
        self.assertRegex(body, r"(?:has|querySelector).*edge\.edge_id")
        self.assertIn("data-master-edge-materialized", body)

    def test_default_all_reference_policy_keeps_reference_edges_visible(self) -> None:
        self.assertIn("policy.default_edge_visibility!=='all'", self.source)
        self.assertIn("policy.default_importance_mode", self.source)
        self.assertIn("defaultTier={core:'minimum',recommended:'recommended',reference:'complete'}", self.source)
        self.assertIn("marvelApplyFlowchartPolicy", self.source)
        self.assertRegex(
            self.source,
            r"default_edge_visibility.*all[\s\S]{0,240}default_importance_mode.*reference",
        )

    def test_selection_and_deselection_only_restyle_existing_edge_groups(self) -> None:
        body = function_body(self.source, "renderSelectionState")
        self.assertIn("classList.add('hl'", body)
        self.assertIn("classList.add('pathhl'", body)
        self.assertNotIn("addMissingDirectedEdges(svg,state)", body)
        self.assertNotIn("drawDynamicEdge(", body)
        self.assertNotIn("createElementNS(NS,'g')", body)
        self.assertNotIn("remove()", body)
        self.assertIn("reason_ids", self.source)

    def test_reason_panel_resolves_reason_ids_without_mutating_edges(self) -> None:
        self.assertIn("reasonsById", self.source)
        self.assertRegex(self.source, r"reason_ids\.map\(id=>reasonsById\[id\]")
        self.assertRegex(self.source, r"reason_ids[\s\S]{0,700}(reason explanation|reasonExplain|根拠)")
        self.assertRegex(self.source, r"edge\.edge_id[\s\S]{0,220}reason_ids")

    def test_multiselect_and_directed_path_style_existing_ids(self) -> None:
        self.assertIn("combineMode==='path' && selectedIds.size>1", self.source)
        state_body = function_body(self.source, "pathSelectionState")
        self.assertIn("shortestDirectedPath", self.source)
        self.assertIn("pathEdges", state_body)
        self.assertIn("selectedIds", self.source)
        self.assertRegex(state_body, r"pathEdges\.add\(k\)")
        render_body = function_body(self.source, "renderSelectionState")
        self.assertRegex(render_body, r"state\.pathEdges\.has\(k\)")

    def test_character_filter_is_visual_only_and_does_not_replace_exported_edges(self) -> None:
        body = function_body(self.source, "applyCharacterHighlight")
        self.assertIn("charhl", body)
        self.assertNotIn("EDGES=", body)
        self.assertNotIn("EDGES =", body)
        self.assertIn("const ids=charWorks[cf.value]||new Set()", body)
        self.assertIn(
            "EDGES.length",
            self.source,
            "the visual-only filter contract should observe the exported edge collection",
        )


if __name__ == "__main__":
    unittest.main()
