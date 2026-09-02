from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests" / "library_v5" / "runtime_selection_classifier.mjs"


class RuntimeSelectionClassifierTests(unittest.TestCase):
    def test_node_runtime_classifier_contract(self) -> None:
        """Execute the production classifier against independent runtime fixtures."""
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for runtime classifier coverage")
        if node is None:
            return
        result = subprocess.run(
            [node, str(HARNESS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"runtime harness did not emit JSON: {error}: {result.stdout!r}")
        self.assertEqual(
            report,
            {
                "non_traversable": {"site-proposal": {}, "complete": {}},
                "tier_gate": {
                    "site-proposal": {"a->goal": "backhl", "goal->next": "forwardhl"},
                    "complete": {
                        "q->a": "backhl",
                        "a->goal": "backhl",
                        "goal->next": "forwardhl",
                    },
                },
                "scope_and_path": {
                    "previous1": {"a->goal": "backhl"},
                    "or": {
                        "a-goal-or": "backhl",
                        "b-other-or": "backhl",
                        "goal-next-or": "forwardhl",
                        "other-goal-or": "bothhl",
                    },
                    "and": {"c->d": "bothhl"},
                    "path": {"a-goal-sequence": "pathhl"},
                },
                "edge_key": {"edge_id": "a->b", "title_fallback": "a->b"},
                "duplicate_edges": {
                    "a-goal-branch": "backhl",
                    "a-goal-sequence": "backhl",
                },
                "svg_duplicate_edges": {
                    "a-goal-branch": ["backhl", "hl"],
                    "a-goal-sequence": ["backhl", "hl"],
                    "a-goal-display": [],
                },
                "svg_duplicate_path": {
                    "a-goal-branch": ["hl", "pathhl"],
                    "a-goal-sequence": ["hl", "pathhl"],
                    "a-goal-display": [],
                },
                "svg": {
                    "a->goal": ["backhl", "hl"],
                    "false->goal": [],
                },
                "canvas": {
                    "a-goal-branch": "backhl",
                    "a-goal-sequence": "backhl",
                },
                "canvas_path": {
                    "a-goal-branch": "pathhl",
                    "a-goal-sequence": "pathhl",
                },
                "synthetic_relation_guard": {
                    "overview": [{"source": "a", "target": "goal", "category": "backhl", "compressed": False}],
                    "chronology": [],
                },
                "reason_provenance": {
                    "transition_with_explicit_reason": True,
                    "transition_without_explicit_reason": False,
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
