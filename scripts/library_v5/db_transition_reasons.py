from __future__ import annotations

import sqlite3


_INTERNAL_VIEW_NAMES = (
    "_v_transition_supported_pairs",
    "v_multiverse_transition_reasons",
)


def _other_work_expr(alias: str = "r") -> str:
    return f"CASE WHEN eo.work_id = {alias}.source_work_id THEN {alias}.target_work_id ELSE {alias}.source_work_id END"


def install_transition_reason_views(connection: sqlite3.Connection) -> None:
    """Overlay conservative multiverse-transition reasons onto the Phase 1 graph views.

    A transition never creates a work pair by itself in Phase 2 infrastructure.  It may only
    add metadata to an already-active explicit multiverse pair when the transition occurrence
    is one endpoint and the other endpoint is explained by either a transition participant's
    canonical appearance or the opposite transition continuity.
    """
    for view_name in ("v_flowchart_edge_candidates", "v_work_connections_all", "v_work_connection_reasons", *_INTERNAL_VIEW_NAMES):
        connection.execute(f"DROP VIEW IF EXISTS {view_name}")

    other = _other_work_expr()
    participant_match = f"""
        EXISTS (
            SELECT 1
            FROM transition_participants AS tp
            JOIN _entity_identity_map AS tim
              ON tim.raw_entity_id = tp.entity_id
            JOIN _v_resolved_appearances AS a
              ON a.canonical_entity_id = tim.canonical_entity_id
             AND a.work_id = {other}
            WHERE tp.transition_id = t.transition_id
              AND tp.verification_status <> 'superseded'
        )
    """
    continuity_match = f"""
        (
            t.source_continuity_id IS NOT NULL
            AND t.destination_continuity_id IS NOT NULL
            AND (
                (
                    EXISTS (
                        SELECT 1 FROM v_continuity_works AS cw_containing
                        WHERE cw_containing.work_id = eo.work_id
                          AND cw_containing.continuity_id = t.source_continuity_id
                    )
                    AND EXISTS (
                        SELECT 1 FROM v_continuity_works AS cw_other
                        WHERE cw_other.work_id = {other}
                          AND cw_other.continuity_id = t.destination_continuity_id
                    )
                )
                OR
                (
                    EXISTS (
                        SELECT 1 FROM v_continuity_works AS cw_containing
                        WHERE cw_containing.work_id = eo.work_id
                          AND cw_containing.continuity_id = t.destination_continuity_id
                    )
                    AND EXISTS (
                        SELECT 1 FROM v_continuity_works AS cw_other
                        WHERE cw_other.work_id = {other}
                          AND cw_other.continuity_id = t.source_continuity_id
                    )
                )
            )
        )
    """

    connection.execute(
        f"""
        CREATE VIEW _v_transition_supported_pairs AS
        SELECT DISTINCT
            r.source_work_id,
            r.target_work_id,
            t.transition_id,
            eo.work_id AS containing_work_id,
            {other} AS other_work_id
        FROM work_relations AS r
        JOIN event_occurrences AS eo
          ON eo.work_id IN (r.source_work_id, r.target_work_id)
         AND eo.verification_status <> 'superseded'
        JOIN multiverse_transitions AS t
          ON t.transition_id = eo.event_id
         AND t.verification_status <> 'superseded'
        JOIN events AS e
          ON e.event_id = t.transition_id
         AND e.event_kind = 'multiverse_transition'
         AND e.verification_status <> 'superseded'
        WHERE r.verification_status <> 'superseded'
          AND r.continuity_scope = 'multiverse'
          AND r.source_work_id <> r.target_work_id
          AND ({participant_match} OR {continuity_match})
        """
    )

    connection.execute(
        """
        CREATE VIEW v_multiverse_transition_reasons AS
        SELECT
            p.source_work_id,
            p.target_work_id,
            'multiverse_transition' AS reason_kind,
            '' AS canonical_entity_id,
            '' AS relation_id,
            (
                SELECT group_concat(value, '|')
                FROM (
                    SELECT p.transition_id AS value
                    UNION
                    SELECT eo2.event_occurrence_id AS value
                    FROM event_occurrences AS eo2
                    WHERE eo2.event_id = p.transition_id
                      AND eo2.work_id = p.containing_work_id
                      AND eo2.verification_status <> 'superseded'
                    UNION
                    SELECT tp2.transition_participant_id AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = p.transition_id
                      AND tp2.verification_status <> 'superseded'
                    ORDER BY value
                )
            ) AS support_fact_ids,
            '' AS appearance_kinds,
            (
                SELECT group_concat(value, '|')
                FROM (
                    SELECT e2.verification_status AS value
                    FROM events AS e2 WHERE e2.event_id = p.transition_id
                    UNION
                    SELECT t2.verification_status AS value
                    FROM multiverse_transitions AS t2 WHERE t2.transition_id = p.transition_id
                    UNION
                    SELECT eo2.verification_status AS value
                    FROM event_occurrences AS eo2
                    WHERE eo2.event_id = p.transition_id
                      AND eo2.work_id = p.containing_work_id
                      AND eo2.verification_status <> 'superseded'
                    UNION
                    SELECT tp2.verification_status AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = p.transition_id
                      AND tp2.verification_status <> 'superseded'
                    ORDER BY value
                )
            ) AS verification_statuses,
            (
                SELECT group_concat(value, '|')
                FROM (
                    SELECT e2.certainty AS value
                    FROM events AS e2 WHERE e2.event_id = p.transition_id
                    UNION
                    SELECT t2.direction_certainty AS value
                    FROM multiverse_transitions AS t2 WHERE t2.transition_id = p.transition_id
                    UNION
                    SELECT eo2.certainty AS value
                    FROM event_occurrences AS eo2
                    WHERE eo2.event_id = p.transition_id
                      AND eo2.work_id = p.containing_work_id
                      AND eo2.verification_status <> 'superseded'
                    UNION
                    SELECT tp2.identity_certainty AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = p.transition_id
                      AND tp2.verification_status <> 'superseded'
                    ORDER BY value
                )
            ) AS certainty_values,
            'multiverse_transition; transition=' || p.transition_id ||
            '; kind=' || t.transition_kind ||
            '; source=' || COALESCE(t.source_continuity_id, '?') || '->' || COALESCE(t.destination_continuity_id, '?') ||
            '; containing_work=' || p.containing_work_id ||
            '; participant_facts=' || COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT tp2.transition_participant_id || ':' || tp2.entity_id || ':' || tp2.participant_role AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = p.transition_id
                      AND tp2.verification_status <> 'superseded'
                    ORDER BY value
                )
            ), '') AS notes,
            p.transition_id AS reason_discriminator
        FROM _v_transition_supported_pairs AS p
        JOIN multiverse_transitions AS t ON t.transition_id = p.transition_id
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
                SELECT group_concat(value, '|') FROM (
                    SELECT DISTINCT a2.appearance_kind AS value
                    FROM _v_resolved_appearances AS a2
                    WHERE a2.canonical_entity_id = p.canonical_entity_id
                      AND a2.work_id IN (p.source_work_id, p.target_work_id)
                      AND TRIM(a2.appearance_kind) <> ''
                    ORDER BY value
                )
            ), '') AS appearance_kinds,
            COALESCE((
                SELECT group_concat(value, '|') FROM (
                    SELECT DISTINCT a2.verification_status AS value
                    FROM _v_resolved_appearances AS a2
                    WHERE a2.canonical_entity_id = p.canonical_entity_id
                      AND a2.work_id IN (p.source_work_id, p.target_work_id)
                      AND TRIM(a2.verification_status) <> ''
                    ORDER BY value
                )
            ), '') AS verification_statuses,
            COALESCE((
                SELECT group_concat(value, '|') FROM (
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

        UNION ALL

        SELECT
            source_work_id,target_work_id,reason_kind,canonical_entity_id,relation_id,
            support_fact_ids,appearance_kinds,verification_statuses,certainty_values,notes,reason_discriminator
        FROM v_multiverse_transition_reasons
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
        CREATE VIEW v_flowchart_edge_candidates AS
        SELECT source_work_id,target_work_id,reason_count,reason_keys
        FROM v_work_connections_all
        """
    )
