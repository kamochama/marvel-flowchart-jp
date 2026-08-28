from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_export import export_work_graph
from scripts.library_v5.derive_edges import collapse_reasons_to_edges, derive_reasons


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
LEGACY_REASON_FIELDS = (
    "reason_id",
    "source_work_id",
    "target_work_id",
    "reason_kind",
    "entity_id",
    "relation_id",
    "support_fact_ids",
    "appearance_kinds",
    "verification_statuses",
    "certainty_values",
    "notes",
)
TRANSITION_REASON_FIELDS = (
    "transition_id",
    "event_id",
    "event_occurrence_id",
    "source_continuity_id",
    "destination_continuity_id",
    "participant_fact_ids",
)
LEGACY_EDGE_STABLE_FIELDS = (
    "edge_id",
    "source_work_id",
    "target_work_id",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _old_reason_rows() -> list[dict[str, str]]:
    return derive_reasons(
        _read_csv(LIB / "works.csv"),
        _read_csv(LIB / "appearances.csv"),
        _read_csv(LIB / "work_relations.csv"),
        _read_csv(LIB / "entity_relations.csv"),
        mode="combined_all_pairs",
        portrayals=_read_csv(LIB / "portrayals.csv"),
    )


def _old_semantic_rows() -> set[tuple[str, ...]]:
    return {
        (
            row["source_work_id"],
            row["target_work_id"],
            row["reason_kind"],
            row["entity_id"],
            row["relation_id"],
            row["support_fact_ids"],
            row["appearance_kinds"],
            row["verification_statuses"],
            row["certainty_values"],
            row["notes"],
        )
        for row in _old_reason_rows()
    }


def _db_legacy_semantic_rows(connection) -> set[tuple[str, ...]]:
    return {
        tuple(row)
        for row in connection.execute(
            """
            SELECT source_work_id,target_work_id,reason_kind,
                   canonical_entity_id,relation_id,support_fact_ids,
                   appearance_kinds,verification_statuses,certainty_values,notes
            FROM v_work_connection_reasons
            WHERE reason_kind <> 'multiverse_transition'
            """
        )
    }


def _edge_pairs(rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(row["source_work_id"], row["target_work_id"]) for row in rows}


def _stable_edge_projection(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {field: row[field] for field in LEGACY_EDGE_STABLE_FIELDS}
        for row in rows
    ]


class DbWorkConnectionParityTests(unittest.TestCase):
    def test_sql_reason_view_preserves_legacy_python_oracle_semantics(self) -> None:
        old = _old_semantic_rows()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            new = _db_legacy_semantic_rows(connection)
            connection.close()

        self.assertEqual(old, new)

    def test_sql_edge_view_has_one_row_per_reason_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            duplicates = connection.execute(
                """
                SELECT source_work_id,target_work_id,count(*)
                FROM v_work_connections_all
                GROUP BY source_work_id,target_work_id
                HAVING count(*) > 1
                """
            ).fetchall()
            self.assertEqual(duplicates, [])
            reason_pairs = connection.execute(
                "SELECT count(DISTINCT source_work_id || char(0) || target_work_id) FROM v_work_connection_reasons"
            ).fetchone()[0]
            edge_count = connection.execute("SELECT count(*) FROM v_work_connections_all").fetchone()[0]
            self.assertEqual(edge_count, reason_pairs)
            connection.close()

    def test_db_export_preserves_legacy_projection_and_pair_compatibility(self) -> None:
        oracle_reasons = _old_reason_rows()
        oracle_edges = collapse_reasons_to_edges(oracle_reasons)
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
            counts = export_work_graph(db_path, temp / "derived")
            exported_reasons = _read_csv(temp / "derived" / "work_pair_reasons.csv")
            exported_edges = _read_csv(temp / "derived" / "work_edges_all.csv")

        legacy_exported_reasons = [
            row for row in exported_reasons
            if row["reason_kind"] != "multiverse_transition"
        ]
        legacy_projection = [
            {field: row[field] for field in LEGACY_REASON_FIELDS}
            for row in legacy_exported_reasons
        ]
        self.assertEqual(legacy_projection, oracle_reasons)
        self.assertTrue(
            all(
                all(row[field] == "" for field in TRANSITION_REASON_FIELDS)
                for row in legacy_exported_reasons
            )
        )

        # Phase 2 may add new reasons to an already-supported pair, but the
        # migration must not create/remove graph pairs or change stable edge
        # identity and row ordering inherited from the Phase 1 exporter.
        self.assertEqual(_edge_pairs(exported_edges), _edge_pairs(oracle_edges))
        self.assertEqual(len(exported_edges), len(oracle_edges))
        self.assertEqual(_stable_edge_projection(exported_edges), _stable_edge_projection(oracle_edges))
        self.assertEqual(
            counts,
            {"work_pair_reasons": len(exported_reasons), "work_edges_all": len(exported_edges)},
        )

    def test_db_export_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            db_path = compile_database(ROOT, temp / "marvel.sqlite").db_path
            export_work_graph(db_path, temp / "first")
            export_work_graph(db_path, temp / "second")
            for name in ("work_pair_reasons.csv", "work_edges_all.csv"):
                self.assertEqual((temp / "first" / name).read_bytes(), (temp / "second" / name).read_bytes())

    def test_normalized_release_status_views_do_not_enter_graph_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = compile_database(ROOT, Path(tmp) / "marvel.sqlite").db_path
            connection = open_query_connection(db_path)
            try:
                graph_view_names = (
                    "_v_entity_work_presence",
                    "_v_entity_work_pairs",
                    "v_work_connection_reasons",
                    "v_work_connections_all",
                    "v_flowchart_edge_candidates",
                )
                graph_view_sql = {
                    name: connection.execute(
                        "SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (name,)
                    ).fetchone()[0]
                    for name in graph_view_names
                }
            finally:
                connection.close()

        for name, sql in graph_view_sql.items():
            self.assertNotIn("v_work_releases", sql, name)
            self.assertNotIn("v_work_production_status", sql, name)


if __name__ == "__main__":
    unittest.main()
