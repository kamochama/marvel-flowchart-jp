from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.library_v5.db_compile import compile_database, open_query_connection
from scripts.library_v5.db_views import PUBLIC_VIEW_NAMES
from tests.library_v5.test_db_compile import HEADERS, _write_csv, make_minimal_repo


_FIXTURE_TEMP_DIRS: list[tempfile.TemporaryDirectory] = []


def _compile_fixture_with_release_status_rows() -> sqlite3.Connection:
    temporary_directory = tempfile.TemporaryDirectory()
    _FIXTURE_TEMP_DIRS.append(temporary_directory)
    root = make_minimal_repo(Path(temporary_directory.name))
    library = root / "data" / "library"
    _write_csv(library / "releases.csv", HEADERS["releases.csv"], [{
        "release_id": "release-work-a-fixture",
        "work_id": "work-a",
        "territory": "JP",
        "release_kind": "theatrical",
        "release_date": "2020-01-02",
        "release_precision": "day",
        "status": "released",
        "certainty": "confirmed",
        "verification_status": "source_verified",
        "notes": "release fixture",
    }])
    _write_csv(library / "production_status_assertions.csv", HEADERS["production_status_assertions.csv"], [{
        "production_status_assertion_id": "production-status-work-a-fixture",
        "work_id": "work-a",
        "status": "released",
        "asserted_at": "2026-08-29",
        "certainty": "confirmed",
        "verification_status": "source_verified",
        "notes": "status fixture",
    }])
    result = compile_database(root)
    return open_query_connection(result.db_path)


class DbV1ReleasesStatusViewTests(unittest.TestCase):
    def test_release_and_status_views_are_public_and_do_not_create_work_pairs(self):
        connection = _compile_fixture_with_release_status_rows()
        try:
            self.assertIn("v_work_releases", PUBLIC_VIEW_NAMES)
            self.assertIn("v_work_production_status", PUBLIC_VIEW_NAMES)
            self.assertEqual(connection.execute("SELECT count(*) FROM v_work_releases").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM v_work_production_status").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM v_work_connection_reasons").fetchone()[0], 0)
        finally:
            connection.close()

    def test_release_and_status_views_expose_work_metadata_in_explicit_order(self):
        connection = _compile_fixture_with_release_status_rows()
        try:
            release = connection.execute(
                """
                SELECT release_id,work_id,work_title_ja,work_title_en,
                       territory,release_kind,release_date,release_precision,
                       status,certainty,verification_status,notes
                FROM v_work_releases
                ORDER BY release_id
                """
            ).fetchall()
            production_status = connection.execute(
                """
                SELECT production_status_assertion_id,work_id,work_title_ja,work_title_en,
                       status,asserted_at,certainty,verification_status,notes
                FROM v_work_production_status
                ORDER BY production_status_assertion_id
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(release, [(
            "release-work-a-fixture", "work-a", "作品A", "Work A", "JP",
            "theatrical", "2020-01-02", "day", "released", "confirmed",
            "source_verified", "release fixture",
        )])
        self.assertEqual(production_status, [(
            "production-status-work-a-fixture", "work-a", "作品A", "Work A",
            "released", "2026-08-29", "confirmed", "source_verified", "status fixture",
        )])

    def test_release_and_status_views_hide_superseded_rows(self):
        connection = _compile_fixture_with_release_status_rows()
        try:
            connection.execute(
                """
                INSERT INTO releases(
                    release_id,work_id,territory,release_kind,release_date,
                    release_precision,status,certainty,verification_status,notes
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "release-work-a-superseded", "work-a", "US", "theatrical",
                    "2020-01-01", "day", "released", "confirmed", "superseded", "old",
                ),
            )
            connection.execute(
                """
                INSERT INTO production_status_assertions(
                    production_status_assertion_id,work_id,status,asserted_at,
                    certainty,verification_status,notes
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    "production-status-work-a-superseded", "work-a", "announced",
                    "2019-01-01", "confirmed", "superseded", "old",
                ),
            )
            connection.commit()
            release_ids = [
                row[0]
                for row in connection.execute(
                    "SELECT release_id FROM v_work_releases ORDER BY release_id"
                )
            ]
            status_ids = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT production_status_assertion_id
                    FROM v_work_production_status
                    ORDER BY production_status_assertion_id
                    """
                )
            ]
        finally:
            connection.close()

        self.assertEqual(release_ids, ["release-work-a-fixture"])
        self.assertEqual(status_ids, ["production-status-work-a-fixture"])

    def test_release_and_status_views_only_join_works(self):
        connection = _compile_fixture_with_release_status_rows()
        try:
            sql_by_view = {
                view_name: connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (view_name,)
                ).fetchone()[0]
                for view_name in ("v_work_releases", "v_work_production_status")
            }
        finally:
            connection.close()

        for view_name, sql in sql_by_view.items():
            self.assertIn("JOIN WORKS", sql.upper(), view_name)
            self.assertNotIn("JOIN RELEASES", sql.upper(), view_name)
            self.assertNotIn("JOIN PRODUCTION_STATUS_ASSERTIONS", sql.upper(), view_name)


if __name__ == "__main__":
    unittest.main()
