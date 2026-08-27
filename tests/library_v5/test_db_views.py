from __future__ import annotations

import sqlite3
import unittest

from scripts.library_v5.db_schema import create_schema
from scripts.library_v5.db_views import install_internal_helpers


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


if __name__ == "__main__":
    unittest.main()
