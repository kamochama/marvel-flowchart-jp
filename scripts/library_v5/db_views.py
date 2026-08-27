from __future__ import annotations

import sqlite3

from .derive_edges import _identity_canonical_map


PUBLIC_VIEW_NAMES = (
    "v_entity_work_history",
    "v_continuity_works",
    "v_work_connection_reasons",
    "v_work_connections_all",
    "v_flowchart_nodes",
    "v_flowchart_edge_candidates",
)


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


def install_public_views(connection: sqlite3.Connection) -> None:
    for view_name in (*PUBLIC_VIEW_NAMES, "_v_entity_work_pairs", "_v_entity_work_presence", "_v_resolved_appearances"):
        connection.execute(f"DROP VIEW IF EXISTS {view_name}")

    connection.execute(
        """
        CREATE VIEW _v_resolved_appearances AS
        SELECT
            a.appearance_id,
            a.work_id,
            a.entity_id AS raw_entity_id,
            m.canonical_entity_id,
            a.appearance_kind,
            a.certainty,
            a.verification_status,
            a.notes
        FROM appearances AS a
        JOIN _entity_identity_map AS m
          ON m.raw_entity_id = a.entity_id
        WHERE a.verification_status <> 'superseded'
        """
    )

    connection.execute(
        """
        CREATE VIEW _v_entity_work_presence AS
        SELECT DISTINCT
            a.canonical_entity_id,
            a.work_id,
            COALESCE(NULLIF(TRIM(w.release_sort_date), ''), '9999-99-99') AS release_sort_date
        FROM _v_resolved_appearances AS a
        JOIN works AS w ON w.work_id = a.work_id
        """
    )

    connection.execute(
        """
        CREATE VIEW _v_entity_work_pairs AS
        SELECT
            a.canonical_entity_id,
            a.work_id AS source_work_id,
            b.work_id AS target_work_id
        FROM _v_entity_work_presence AS a
        JOIN _v_entity_work_presence AS b
          ON b.canonical_entity_id = a.canonical_entity_id
         AND (
              a.release_sort_date < b.release_sort_date
              OR (a.release_sort_date = b.release_sort_date AND a.work_id < b.work_id)
         )
        """
    )

    connection.execute(
        """
        CREATE VIEW v_entity_work_history AS
        SELECT
            a.appearance_id,
            a.work_id,
            a.raw_entity_id,
            a.canonical_entity_id,
            a.appearance_kind,
            a.certainty,
            a.verification_status,
            a.notes,
            w.title_ja,
            w.title_en,
            w.release_sort_date,
            w.release_display_date,
            w.format,
            w.status
        FROM _v_resolved_appearances AS a
        JOIN works AS w ON w.work_id = a.work_id
        """
    )

    connection.execute(
        """
        CREATE VIEW v_continuity_works AS
        SELECT
            wc.work_continuity_id,
            wc.work_id,
            wc.continuity_id,
            wc.relation_to_continuity,
            wc.certainty,
            wc.verification_status,
            wc.notes,
            c.label_ja AS continuity_label_ja,
            c.label_en AS continuity_label_en,
            c.continuity_kind,
            w.title_ja,
            w.title_en,
            w.release_sort_date
        FROM work_continuities AS wc
        JOIN continuities AS c ON c.continuity_id = wc.continuity_id
        JOIN works AS w ON w.work_id = wc.work_id
        WHERE wc.verification_status <> 'superseded'
          AND c.verification_status <> 'superseded'
        """
    )

    connection.execute(
        """
        CREATE VIEW v_work_connection_reasons AS
        SELECT
            p.source_work_id,
            p.target_work_id,
            'shared_entity' AS reason_kind,
            p.canonical_entity_id,
            '' AS relation_id,
            (
                SELECT group_concat(value, '|')
                FROM (
                    SELECT DISTINCT a2.appearance_id AS value
                    FROM _v_resolved_appearances AS a2
                    WHERE a2.canonical_entity_id = p.canonical_entity_id
                      AND a2.work_id IN (p.source_work_id, p.target_work_id)
                    ORDER BY value
                )
            ) AS support_fact_ids,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT DISTINCT a2.appearance_kind AS value
                    FROM _v_resolved_appearances AS a2
                    WHERE a2.canonical_entity_id = p.canonical_entity_id
                      AND a2.work_id IN (p.source_work_id, p.target_work_id)
                      AND TRIM(a2.appearance_kind) <> ''
                    ORDER BY value
                )
            ), '') AS appearance_kinds,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT DISTINCT a2.verification_status AS value
                    FROM _v_resolved_appearances AS a2
                    WHERE a2.canonical_entity_id = p.canonical_entity_id
                      AND a2.work_id IN (p.source_work_id, p.target_work_id)
                      AND TRIM(a2.verification_status) <> ''
                    ORDER BY value
                )
            ), '') AS verification_statuses,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT DISTINCT a2.certainty AS value
                    FROM _v_resolved_appearances AS a2
                    WHERE a2.canonical_entity_id = p.canonical_entity_id
                      AND a2.work_id IN (p.source_work_id, p.target_work_id)
                      AND TRIM(a2.certainty) <> ''
                    ORDER BY value
                )
            ), '') AS certainty_values,
            '' AS notes,
            p.canonical_entity_id AS reason_discriminator
        FROM _v_entity_work_pairs AS p

        UNION ALL

        SELECT
            r.source_work_id,
            r.target_work_id,
            'explicit_relation' AS reason_kind,
            '' AS canonical_entity_id,
            r.work_relation_id AS relation_id,
            r.work_relation_id AS support_fact_ids,
            '' AS appearance_kinds,
            r.verification_status AS verification_statuses,
            r.certainty AS certainty_values,
            r.relation_kind || '; ' || r.relation_scope || '; ' || r.directness AS notes,
            r.work_relation_id AS reason_discriminator
        FROM work_relations AS r
        WHERE r.verification_status <> 'superseded'
          AND TRIM(r.source_work_id) <> ''
          AND TRIM(r.target_work_id) <> ''
          AND r.source_work_id <> r.target_work_id
        """
    )

    connection.execute(
        """
        CREATE VIEW v_work_connections_all AS
        SELECT
            source_work_id,
            target_work_id,
            COUNT(*) AS reason_count,
            (
                SELECT group_concat(reason_key, '|')
                FROM (
                    SELECT r2.reason_kind || ':' || r2.reason_discriminator AS reason_key
                    FROM v_work_connection_reasons AS r2
                    WHERE r2.source_work_id = r.source_work_id
                      AND r2.target_work_id = r.target_work_id
                    ORDER BY r2.reason_kind, r2.reason_discriminator
                )
            ) AS reason_keys
        FROM v_work_connection_reasons AS r
        GROUP BY source_work_id, target_work_id
        """
    )

    connection.execute(
        """
        CREATE VIEW v_flowchart_nodes AS
        SELECT
            work_id,
            title_ja,
            title_en,
            title_official,
            format,
            status,
            classification,
            release_sort_date,
            release_display_date,
            release_kind,
            release_certainty
        FROM works
        """
    )

    connection.execute(
        """
        CREATE VIEW v_flowchart_edge_candidates AS
        SELECT
            source_work_id,
            target_work_id,
            reason_count,
            reason_keys
        FROM v_work_connections_all
        """
    )
