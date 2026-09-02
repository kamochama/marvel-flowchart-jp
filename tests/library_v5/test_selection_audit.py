from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLOWCHART = ROOT / "data" / "derived" / "flowchart.json"


try:
    from tests.library_v5.selection_audit_oracle import SelectionAuditOracle
except ImportError:  # The RED state before the audit oracle is implemented.
    SelectionAuditOracle = None  # type: ignore[assignment,misc]


class SelectionAuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(FLOWCHART.read_text(encoding="utf-8"))

    def test_independent_oracle_is_available(self) -> None:
        """The exhaustive selection audit must not derive expectations from production JS."""
        self.assertIsNotNone(SelectionAuditOracle)

    def test_complete_oracle_covers_every_exported_work(self) -> None:
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(self.payload)
        edge_ids = {oracle.edge_key(edge) for edge in oracle.edges}
        self.assertEqual(set(oracle.work_ids), {row["work_id"] for row in self.payload["nodes"]})
        for work_id in oracle.work_ids:
            expectation = oracle.expected_main_selection(work_id, tier="complete")
            classes = (set(expectation.back_edges), set(expectation.forward_edges), set(expectation.context_edges))
            self.assertEqual(set().union(*classes), set(expectation.all_edges), work_id)
            self.assertEqual(set(), classes[0] & classes[1], work_id)
            self.assertEqual(set(), classes[0] & classes[2], work_id)
            self.assertEqual(set(), classes[1] & classes[2], work_id)
            self.assertTrue(set(expectation.all_edges) <= edge_ids, work_id)

    def test_site_proposal_oracle_covers_every_exported_work(self) -> None:
        """The public tier has a complete expectation for every work, including empty ones."""
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(self.payload)
        for work_id in oracle.work_ids:
            expectation = oracle.expected_main_selection(work_id, tier="site-proposal")
            classes = (set(expectation.back_edges), set(expectation.forward_edges), set(expectation.context_edges))
            self.assertEqual(set(), classes[0] & classes[1], work_id)
            self.assertEqual(set(), classes[0] & classes[2], work_id)
            self.assertEqual(set(), classes[1] & classes[2], work_id)
            self.assertEqual(set(expectation.all_edges), set().union(*classes), work_id)

    def test_site_proposal_context_is_outgoing_only(self) -> None:
        """Site proposal keeps direct context after a goal, not weak incoming fan-in."""
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(
            {
                "nodes": [{"work_id": work_id} for work_id in ("prev", "goal", "next")],
                "edges": [
                    {
                        "edge_id": "edge-prev-goal",
                        "source_work_id": "prev",
                        "target_work_id": "goal",
                        "type_en": "shared character/entity",
                        "strength": "weak",
                    },
                    {
                        "edge_id": "edge-goal-next",
                        "source_work_id": "goal",
                        "target_work_id": "next",
                        "type_en": "shared character/entity",
                        "strength": "weak",
                    },
                ],
            }
        )
        site = oracle.expected_main_selection("goal", tier="site-proposal")
        complete = oracle.expected_main_selection("goal", tier="complete")
        self.assertEqual(site.context_edges, frozenset({"goal->next"}))
        self.assertEqual(complete.context_edges, frozenset({"prev->goal", "goal->next"}))

    def test_site_proposal_keeps_every_explicit_predecessor(self) -> None:
        """Every exported explicit story predecessor remains a backward selection edge."""
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(self.payload)
        for reason in self.payload["reasons"]:
            if reason["reason_kind"] != "explicit_relation":
                continue
            pair = (reason["source_work_id"], reason["target_work_id"])
            edge = next(
                (edge for edge in oracle.edges if (edge["source_work_id"], edge["target_work_id"]) == pair),
                None,
            )
            self.assertIsNotNone(edge, pair)
            if edge is None:
                continue
            expectation = oracle.expected_main_selection(edge["target_work_id"], tier="site-proposal")
            key = oracle.edge_key(edge)
            self.assertIn(key, expectation.back_edges, key)

    def test_canonical_relation_ids_and_pairs_match_export_reasons(self) -> None:
        """Explicit predecessor expectations come from canonical relation facts, not edge labels."""
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(self.payload)
        with (ROOT / "data" / "library" / "work_relations.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            canonical_rows = [
                row for row in csv.DictReader(handle)
                if row["verification_status"] != "superseded"
            ]
        canonical = {
            row["work_relation_id"]: (row["source_work_id"], row["target_work_id"])
            for row in canonical_rows
        }
        explicit_reasons = {
            reason["relation_id"]: (reason["source_work_id"], reason["target_work_id"])
            for reason in self.payload["reasons"]
            if reason["reason_kind"] == "explicit_relation"
        }
        self.assertEqual(len(canonical), len(canonical_rows))
        self.assertEqual(
            len(explicit_reasons),
            sum(1 for reason in self.payload["reasons"] if reason["reason_kind"] == "explicit_relation"),
        )
        self.assertEqual(set(canonical), set(explicit_reasons))
        self.assertEqual(set(canonical.values()), set(explicit_reasons.values()))
        exported_by_pair = {
            (edge["source_work_id"], edge["target_work_id"]): edge
            for edge in self.payload["edges"]
        }
        for reason in self.payload["reasons"]:
            if reason["reason_kind"] != "explicit_relation":
                continue
            pair = (reason["source_work_id"], reason["target_work_id"])
            edge = exported_by_pair.get(pair)
            self.assertIsNotNone(edge, pair)
            if edge is not None:
                self.assertIn(reason["reason_id"], edge["reason_ids"], reason["reason_id"])

    def test_canonical_active_pairs_have_an_exported_selection_edge(self) -> None:
        """Canonical facts are checked before selection expectations are evaluated."""
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(self.payload)
        exported_pairs = {
            (edge["source_work_id"], edge["target_work_id"])
            for edge in oracle.edges
        }
        with (ROOT / "data" / "library" / "work_relations.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        active_pairs = {
            (row["source_work_id"], row["target_work_id"])
            for row in rows
            if row["verification_status"] != "superseded"
        }
        self.assertTrue(active_pairs <= exported_pairs)

    def test_structural_chronology_negatives_are_never_traversed(self) -> None:
        """Display-only chronology rows remain unlit in both public tiers."""
        self.assertIsNotNone(SelectionAuditOracle)
        oracle = SelectionAuditOracle(self.payload)
        records = [
            {"key": "morbius-2022->madame-web-2024", "source": "morbius-2022", "target": "madame-web-2024", "traversable": False},
            {"key": "madame-web-2024->kraven-the-hunter-2024", "source": "madame-web-2024", "target": "kraven-the-hunter-2024", "traversable": False},
            {"key": "deadpool-2016->logan-2017", "source": "deadpool-2016", "target": "logan-2017", "traversable": False},
        ]
        for tier in ("site-proposal", "complete"):
            self.assertEqual(oracle.expected_chronology(records, "madame-web-2024", tier=tier), {})
            self.assertEqual(oracle.expected_chronology(records, "logan-2017", tier=tier), {})


if __name__ == "__main__":
    unittest.main()
