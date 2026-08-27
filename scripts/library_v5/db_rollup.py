from __future__ import annotations

import sqlite3


def install_work_connection_rollup(connection: sqlite3.Connection) -> None:
    """Install the deterministic one-pass work-connection rollup.

    The reason view is intentionally consumed once.  The previous rollup used
    a correlated scalar subquery for ``reason_keys`` and therefore re-ran the
    full reason view for every work pair.  Phase 2 makes that reason view more
    expressive, so the repeated evaluation becomes prohibitively expensive.
    """

    connection.execute("DROP VIEW IF EXISTS v_flowchart_edge_candidates")
    connection.execute("DROP VIEW IF EXISTS v_work_connections_all")

    connection.execute(
        """
        CREATE VIEW v_work_connections_all AS
        SELECT
            source_work_id,
            target_work_id,
            COUNT(*) AS reason_count,
            group_concat(reason_key, '|') AS reason_keys
        FROM (
            SELECT
                source_work_id,
                target_work_id,
                reason_kind || ':' || reason_discriminator AS reason_key
            FROM v_work_connection_reasons
            ORDER BY
                source_work_id,
                target_work_id,
                reason_kind,
                reason_discriminator
        ) AS ordered_reasons
        GROUP BY source_work_id, target_work_id
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
