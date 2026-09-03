from __future__ import annotations

import unittest
from pathlib import Path

from scripts.library_v5.connectivity_audit import audit_inputs, audit_repository


ROOT = Path(__file__).resolve().parents[2]


class ConnectivityAuditOracleTests(unittest.TestCase):
    def test_current_main_has_no_structural_connectivity_failures(self) -> None:
        report = audit_repository(ROOT)

        self.assertEqual(report["counts"]["works"], 131)
        # The D&W Wolverine variant boundary removes six unsupported pair
        # projections while retaining the explicit Logan story-link pair.
        self.assertEqual(report["counts"]["edges"], 355)
        self.assertEqual(report["counts"]["reasons"], 562)
        self.assertEqual(report["summary"]["verdicts"].get("fail", 0), 0)
        self.assertEqual(report["summary"]["projection"]["edge_pair_mismatches"], 0)
        self.assertEqual(report["summary"]["projection"]["reason_orphans"], 0)
        self.assertEqual(len(report["work_inventory"]), 131)
        self.assertEqual(len({row["work_id"] for row in report["work_inventory"]}), 131)
        self.assertEqual(len(report["edge_inventory"]), 355)
        self.assertEqual(
            len({(row["source_work_id"], row["target_work_id"]) for row in report["edge_inventory"]}),
            355,
        )

        zero_degree = {
            row["source_work_id"]
            for row in report["records"]
            if row["domain"] == "P" and row["case_id"].startswith("work-degree-0:")
        }
        self.assertEqual(len(zero_degree), 8)

    def test_missing_explicit_relation_projection_is_a_failure(self) -> None:
        tables = {
            "works.csv": [
                {"work_id": "work-a", "release_sort_date": "2020-01-01"},
                {"work_id": "work-b", "release_sort_date": "2021-01-01"},
            ],
            "work_relations.csv": [
                {
                    "work_relation_id": "relation-a-b",
                    "source_work_id": "work-a",
                    "target_work_id": "work-b",
                    "relation_kind": "sequel",
                    "relation_scope": "story",
                    "directness": "direct",
                    "continuity_scope": "same_or_intended",
                    "certainty": "confirmed",
                    "verification_status": "source_verified",
                    "notes": "fixture",
                }
            ],
            "appearances.csv": [],
            "entity_relations.csv": [],
            "entities.csv": [],
            "events.csv": [],
            "event_occurrences.csv": [],
            "event_participants.csv": [],
            "multiverse_transitions.csv": [],
            "transition_participants.csv": [],
            "chronology_assertions.csv": [],
            "work_continuities.csv": [],
        }
        derived = {"work_edges_all.csv": [], "work_pair_reasons.csv": []}

        report = audit_inputs(tables, derived, html="", flowchart={"nodes": [], "edges": []})

        failures = [row for row in report["records"] if row["verdict"] == "fail"]
        self.assertTrue(any(row["case_id"] == "relation-a-b" for row in failures))

    def test_missing_shared_appearance_projection_is_a_failure(self) -> None:
        tables = {
            "works.csv": [
                {"work_id": "work-a", "release_sort_date": "2020-01-01"},
                {"work_id": "work-b", "release_sort_date": "2021-01-01"},
            ],
            "work_relations.csv": [],
            "appearances.csv": [
                {
                    "appearance_id": "appearance-a",
                    "work_id": "work-a",
                    "entity_id": "entity-e",
                    "verification_status": "source_verified",
                    "appearance_kind": "onscreen",
                    "certainty": "confirmed",
                },
                {
                    "appearance_id": "appearance-b",
                    "work_id": "work-b",
                    "entity_id": "entity-e",
                    "verification_status": "source_verified",
                    "appearance_kind": "onscreen",
                    "certainty": "confirmed",
                },
            ],
            "entity_relations.csv": [],
            "entities.csv": [{"entity_id": "entity-e"}],
            "events.csv": [],
            "event_occurrences.csv": [],
            "event_participants.csv": [],
            "multiverse_transitions.csv": [],
            "transition_participants.csv": [],
            "chronology_assertions.csv": [],
            "work_continuities.csv": [],
        }
        derived = {"work_edges_all.csv": [], "work_pair_reasons.csv": []}

        report = audit_inputs(tables, derived, html="", flowchart={"nodes": [], "edges": []})

        failures = [row for row in report["records"] if row["verdict"] == "fail"]
        self.assertTrue(any(row["case_id"] == "shared-entity:entity-e:work-a->work-b" for row in failures))

    def test_legacy_shared_appearance_is_deferred_even_when_projected(self) -> None:
        tables = {
            "works.csv": [
                {"work_id": "work-a", "release_sort_date": "2020-01-01"},
                {"work_id": "work-b", "release_sort_date": "2021-01-01"},
            ],
            "work_relations.csv": [],
            "appearances.csv": [
                {
                    "appearance_id": "appearance-a",
                    "work_id": "work-a",
                    "entity_id": "entity-e",
                    "verification_status": "legacy_seed",
                },
                {
                    "appearance_id": "appearance-b",
                    "work_id": "work-b",
                    "entity_id": "entity-e",
                    "verification_status": "legacy_seed",
                },
            ],
            "entity_relations.csv": [],
            "entities.csv": [{"entity_id": "entity-e"}],
            "events.csv": [],
            "event_occurrences.csv": [],
            "event_participants.csv": [],
            "multiverse_transitions.csv": [],
            "transition_participants.csv": [],
            "chronology_assertions.csv": [],
            "work_continuities.csv": [],
        }
        derived = {
            "work_edges_all.csv": [
                {"source_work_id": "work-a", "target_work_id": "work-b"}
            ],
            "work_pair_reasons.csv": [
                {
                    "reason_id": "reason-shared",
                    "source_work_id": "work-a",
                    "target_work_id": "work-b",
                    "reason_kind": "shared_entity",
                    "entity_id": "entity-e",
                    "support_fact_ids": "appearance-a|appearance-b",
                }
            ],
        }

        report = audit_inputs(
            tables,
            derived,
            flowchart={"nodes": [], "edges": []},
        )

        row = next(
            item
            for item in report["records"]
            if item["case_id"] == "shared-entity:entity-e:work-a->work-b"
        )
        self.assertEqual(row["verdict"], "deferred")
        self.assertEqual(row["disposition"], "needs-source")

    def test_transition_without_independent_pair_is_deferred_not_invented(self) -> None:
        report = audit_repository(ROOT)

        self.assertGreaterEqual(
            report["summary"]["coverage"].get("not_materialized", 0),
            3,
        )
        self.assertEqual(report["summary"]["transition"]["unsupported_pair_edges"], 0)

    def test_directed_relation_cycle_is_a_failure(self) -> None:
        tables = {
            "works.csv": [
                {"work_id": "work-a"},
                {"work_id": "work-b"},
            ],
            "work_relations.csv": [
                {
                    "work_relation_id": "relation-a-b",
                    "source_work_id": "work-a",
                    "target_work_id": "work-b",
                    "verification_status": "legacy_seed",
                },
                {
                    "work_relation_id": "relation-b-a",
                    "source_work_id": "work-b",
                    "target_work_id": "work-a",
                    "verification_status": "legacy_seed",
                },
            ],
            "appearances.csv": [],
            "entity_relations.csv": [],
            "entities.csv": [],
            "events.csv": [],
            "event_occurrences.csv": [],
            "event_participants.csv": [],
            "multiverse_transitions.csv": [],
            "transition_participants.csv": [],
            "chronology_assertions.csv": [],
            "work_continuities.csv": [],
        }
        report = audit_inputs(
            tables,
            {
                "work_edges_all.csv": [],
                "work_pair_reasons.csv": [],
            },
            flowchart={"nodes": [], "edges": []},
        )
        self.assertTrue(
            any(
                row["case_id"] == "relation-cycle:work-a->work-b"
                for row in report["records"]
                if row["verdict"] == "fail"
            )
        )


if __name__ == "__main__":
    unittest.main()
