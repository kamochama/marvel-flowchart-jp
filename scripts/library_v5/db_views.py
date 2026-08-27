from __future__ import annotations

import sqlite3

from .derive_edges import _identity_canonical_map


def _entity_relation_rows(connection: sqlite3.Connection) -> list[dict[str, str]]:
    cursor = connection.execute(
        "SELECT entity_relation_id,source_entity_id,relation_kind,target_entity_id,certainty,verification_status,notes FROM entity_relations ORDER BY entity_relation_id"
    )
    columns = [description[0] for description in cursor.description or ()]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def install_internal_helpers(connection: sqlite3.Connection) -> None:
    relation_rows = _entity_relation_rows(connection)
    identity_map = _identity_canonical_map(relation_rows)
    entity_ids = [row[0] for row in connection.execute("SELECT entity_id FROM entities ORDER BY entity_id")]

    connection.execute("DROP TABLE IF EXISTS _entity_identity_map")
    connection.execute(
        """
        CREATE TABLE _entity_identity_map (
            raw_entity_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
            canonical_entity_id TEXT NOT NULL REFERENCES entities(entity_id)
        )
        """
    )
    connection.executemany(
        "INSERT INTO _entity_identity_map(raw_entity_id,canonical_entity_id) VALUES(?,?)",
        ((entity_id, identity_map.get(entity_id, entity_id)) for entity_id in entity_ids),
    )
