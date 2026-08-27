from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.derive_edges import derive_reasons


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _old_semantic_rows() -> set[tuple[str, ...]]:
    reasons = derive_reasons(
        _read_csv(LIB / "works.csv"),
        _read_csv(LIB / "appearances.csv"),
        _read_csv(LIB / "work_relations.csv"),
        _read_csv(LIB / "entity_relations.csv"),
        mode="combined_all_pairs",
        portrayals=_read_csv(LIB / "portrayals.csv"),
    )
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
        for row in reasons
    }


def _db_semantic_rows(connection) -> set[tuple[str, ...]]:
    return {
        tuple(row)
        for row in connection.execute(
            """
            SELECT source_work_id,target_work_id,reason_kind,
                   canonical_entity_id,relation_id,support_fact_ids,
                   appearance_kinds,verification_statuses,certainty_values,notes
            FROM v_work_connection_reasons
            """
        )
    }


class DbWorkConnectionParityTests(unittest.TestCase):
    def test_sql_reason_view_matches_current_python_oracle_semantics(self) -> None:
        old = _old_semantic_rows()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            new = _db_semantic_rows(connection)
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


if __name__ == "__main__":
    unittest.main()
