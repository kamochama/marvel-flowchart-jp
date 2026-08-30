from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_schema import create_schema
from scripts.library_v5.db_views import install_internal_helpers


ROOT = Path(__file__).resolve().parents[2]


class MultiverseIdentityHelperTests(unittest.TestCase):
    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        create_schema(connection)
        for entity_id in ("frank-canonical", "frank-alias", "strange-616", "strange-838", "other-target"):
            connection.execute(
                "INSERT INTO entities(entity_id,name_ja,name_en,entity_type,notes) VALUES(?,?,?,?,?)",
                (entity_id, entity_id, entity_id, "character", ""),
            )
        return connection

    def test_identity_of_alias_collapses_but_variant_does_not(self) -> None:
        connection = self._connection()
        connection.execute(
            "INSERT INTO entity_relations VALUES(?,?,?,?,?,?,?)",
            ("identity-frank", "frank-alias", "identity_of", "frank-canonical", "confirmed", "source_verified", ""),
        )
        connection.execute(
            "INSERT INTO entity_relations VALUES(?,?,?,?,?,?,?)",
            ("variant-strange", "strange-838", "variant_of", "strange-616", "confirmed", "source_verified", ""),
        )

        install_internal_helpers(connection)
        identity = dict(connection.execute("SELECT raw_entity_id, canonical_entity_id FROM _entity_identity_map"))

        self.assertEqual(identity["frank-alias"], "frank-canonical")
        self.assertEqual(identity["frank-canonical"], "frank-canonical")
        self.assertEqual(identity["strange-838"], "strange-838")
        self.assertEqual(identity["strange-616"], "strange-616")

    def test_conflicting_identity_targets_abort_helper_install(self) -> None:
        connection = self._connection()
        connection.execute(
            "INSERT INTO entity_relations VALUES(?,?,?,?,?,?,?)",
            ("identity-a", "frank-alias", "identity_of", "frank-canonical", "confirmed", "source_verified", ""),
        )
        connection.execute(
            "INSERT INTO entity_relations VALUES(?,?,?,?,?,?,?)",
            ("identity-b", "frank-alias", "identity_of", "other-target", "confirmed", "source_verified", ""),
        )

        with self.assertRaisesRegex(ValueError, "conflicting identity_of"):
            install_internal_helpers(connection)

    def test_superseded_identity_relation_does_not_collapse(self) -> None:
        connection = self._connection()
        connection.execute(
            "INSERT INTO entity_relations VALUES(?,?,?,?,?,?,?)",
            ("identity-old", "frank-alias", "identity_of", "frank-canonical", "confirmed", "superseded", ""),
        )

        install_internal_helpers(connection)
        identity = dict(connection.execute("SELECT raw_entity_id, canonical_entity_id FROM _entity_identity_map"))
        self.assertEqual(identity["frank-alias"], "frank-alias")


class PublicViewContractTests(unittest.TestCase):
    def test_flowchart_nodes_expose_complete_work_contract_in_work_id_order(self) -> None:
        expected_columns = (
            "work_id", "title_ja", "title_en", "title_official", "release", "release_raw",
            "format", "status", "classification", "ja_status", "japan_date", "japan_type",
            "source_url", "source_note", "notes", "release_sort_date", "release_display_date",
            "release_kind", "release_certainty", "release_precision", "release_source_note",
            "aliases_ja", "title_audit_status", "title_audit_source_url", "title_last_verified",
            "title_management_note", "stable_id_note",
        )
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            try:
                columns = tuple(
                    row[1]
                    for row in connection.execute("PRAGMA table_info(v_flowchart_nodes)")
                )
                rows = connection.execute(
                    "SELECT * FROM v_flowchart_nodes ORDER BY work_id"
                ).fetchall()
                work_rows = connection.execute(
                    "SELECT * FROM works ORDER BY work_id"
                ).fetchall()
            finally:
                connection.close()

        self.assertEqual(columns, expected_columns)
        self.assertEqual(rows, work_rows)

    def test_phase1_public_views_are_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='view'")}
            self.assertTrue(
                {
                    "v_entity_work_history",
                    "v_continuity_works",
                    "v_work_connection_reasons",
                    "v_work_connections_all",
                    "v_flowchart_nodes",
                    "v_flowchart_edge_candidates",
                }
                <= names
            )
            connection.close()

    def test_frank_castle_alias_is_resolved_in_entity_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            rows = connection.execute(
                """
                SELECT DISTINCT canonical_entity_id, work_id
                FROM v_entity_work_history
                WHERE raw_entity_id='entity-x-797ce92fcd'
                ORDER BY work_id
                """
            ).fetchall()
            self.assertTrue(rows)
            self.assertTrue(all(row[0] == "entity-x-cacda9afb6" for row in rows))
            connection.close()

    def test_work_connection_rollup_does_not_requery_reason_view_per_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "marvel.sqlite"
            compile_database(ROOT, db_path)
            connection = open_query_connection(db_path)
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='view' AND name='v_work_connections_all'"
            ).fetchone()
            connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            view_sql = str(row[0] or "").upper()
            self.assertEqual(
                view_sql.count("V_WORK_CONNECTION_REASONS"),
                1,
                "v_work_connections_all must consume the reason view once rather than re-querying it per work pair",
            )
            self.assertNotIn("R2.SOURCE_WORK_ID = R.SOURCE_WORK_ID", view_sql)
            self.assertNotIn("R2.TARGET_WORK_ID = R.TARGET_WORK_ID", view_sql)


if __name__ == "__main__":
    unittest.main()
