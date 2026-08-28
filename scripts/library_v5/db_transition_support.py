from __future__ import annotations

import sqlite3


def install_transition_work_reasons(connection: sqlite3.Connection) -> None:
    """Install transition-derived work reasons with participant-appearance support.

    The base work pair must already exist. A transition may then enrich that pair
    either through the original continuity-based rule or when a verified traveler
    is independently verified to appear in the opposite endpoint work.
    """

    # v_work_connections_all depends on v_work_connection_reasons. The optimized
    # rollup is reinstalled by db_rollup immediately after this helper.
    connection.execute("DROP VIEW IF EXISTS v_work_connections_all")
    connection.execute("DROP VIEW IF EXISTS v_work_connection_reasons")
    connection.execute(
        """
        CREATE VIEW v_work_connection_reasons AS
        SELECT * FROM _v_base_work_connection_reasons

        UNION ALL

        SELECT
            b.source_work_id,
            b.target_work_id,
            'multiverse_transition' AS reason_kind,
            '' AS canonical_entity_id,
            '' AS relation_id,
            mt.transition_id,
            mt.transition_id AS event_id,
            eo.event_occurrence_id,
            COALESCE(mt.source_continuity_id, '') AS source_continuity_id,
            COALESCE(mt.destination_continuity_id, '') AS destination_continuity_id,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT tp2.transition_participant_id AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = mt.transition_id
                      AND tp2.verification_status <> 'superseded'
                    ORDER BY value
                )
            ), '') AS participant_fact_ids,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT mt.transition_id AS value
                    UNION
                    SELECT eo.event_occurrence_id AS value
                    UNION
                    SELECT wc2.work_continuity_id AS value
                    FROM work_continuities AS wc2
                    WHERE wc2.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                      AND wc2.verification_status <> 'superseded'
                      AND wc2.continuity_id IN (mt.source_continuity_id, mt.destination_continuity_id)
                    UNION
                    SELECT tp2.transition_participant_id AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = mt.transition_id
                      AND tp2.verification_status <> 'superseded'
                    UNION
                    SELECT rav.appearance_id AS value
                    FROM transition_participants AS tpv
                    JOIN _entity_identity_map AS imv
                      ON imv.raw_entity_id = tpv.entity_id
                    JOIN _v_resolved_appearances AS rav
                      ON rav.canonical_entity_id = imv.canonical_entity_id
                    WHERE tpv.transition_id = mt.transition_id
                      AND tpv.verification_status <> 'superseded'
                      AND rav.verification_status = 'source_verified'
                      AND rav.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                    ORDER BY value
                )
            ), '') AS support_fact_ids,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT DISTINCT rav.appearance_kind AS value
                    FROM transition_participants AS tpv
                    JOIN _entity_identity_map AS imv
                      ON imv.raw_entity_id = tpv.entity_id
                    JOIN _v_resolved_appearances AS rav
                      ON rav.canonical_entity_id = imv.canonical_entity_id
                    WHERE tpv.transition_id = mt.transition_id
                      AND tpv.verification_status <> 'superseded'
                      AND rav.verification_status = 'source_verified'
                      AND rav.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                      AND TRIM(rav.appearance_kind) <> ''
                    ORDER BY value
                )
            ), '') AS appearance_kinds,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT e.verification_status AS value
                    UNION
                    SELECT mt.verification_status AS value
                    UNION
                    SELECT eo.verification_status AS value
                    UNION
                    SELECT wc2.verification_status AS value
                    FROM work_continuities AS wc2
                    WHERE wc2.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                      AND wc2.verification_status <> 'superseded'
                      AND wc2.continuity_id IN (mt.source_continuity_id, mt.destination_continuity_id)
                    UNION
                    SELECT tp2.verification_status AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = mt.transition_id
                      AND tp2.verification_status <> 'superseded'
                    UNION
                    SELECT rav.verification_status AS value
                    FROM transition_participants AS tpv
                    JOIN _entity_identity_map AS imv
                      ON imv.raw_entity_id = tpv.entity_id
                    JOIN _v_resolved_appearances AS rav
                      ON rav.canonical_entity_id = imv.canonical_entity_id
                    WHERE tpv.transition_id = mt.transition_id
                      AND tpv.verification_status <> 'superseded'
                      AND rav.verification_status = 'source_verified'
                      AND rav.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                    ORDER BY value
                )
            ), '') AS verification_statuses,
            COALESCE((
                SELECT group_concat(value, '|')
                FROM (
                    SELECT e.certainty AS value
                    UNION
                    SELECT mt.direction_certainty AS value
                    UNION
                    SELECT eo.certainty AS value
                    UNION
                    SELECT wc2.certainty AS value
                    FROM work_continuities AS wc2
                    WHERE wc2.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                      AND wc2.verification_status <> 'superseded'
                      AND wc2.continuity_id IN (mt.source_continuity_id, mt.destination_continuity_id)
                    UNION
                    SELECT tp2.identity_certainty AS value
                    FROM transition_participants AS tp2
                    WHERE tp2.transition_id = mt.transition_id
                      AND tp2.verification_status <> 'superseded'
                    UNION
                    SELECT rav.certainty AS value
                    FROM transition_participants AS tpv
                    JOIN _entity_identity_map AS imv
                      ON imv.raw_entity_id = tpv.entity_id
                    JOIN _v_resolved_appearances AS rav
                      ON rav.canonical_entity_id = imv.canonical_entity_id
                    WHERE tpv.transition_id = mt.transition_id
                      AND tpv.verification_status <> 'superseded'
                      AND rav.verification_status = 'source_verified'
                      AND rav.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                      AND TRIM(rav.certainty) <> ''
                    ORDER BY value
                )
            ), '') AS certainty_values,
            mt.transition_kind
              || '; source=' || COALESCE(mt.source_continuity_id, 'unknown')
              || '; destination=' || COALESCE(mt.destination_continuity_id, 'unknown')
              || '; occurrence=' || eo.event_occurrence_id AS notes,
            mt.transition_id || ':' || eo.event_occurrence_id AS reason_discriminator
        FROM _v_supported_work_pairs AS b
        JOIN event_occurrences AS eo
          ON eo.work_id IN (b.source_work_id, b.target_work_id)
         AND eo.verification_status <> 'superseded'
        JOIN multiverse_transitions AS mt
          ON mt.transition_id = eo.event_id
         AND mt.verification_status <> 'superseded'
        JOIN events AS e
          ON e.event_id = mt.transition_id
         AND e.verification_status <> 'superseded'
        WHERE (
            (
                EXISTS (
                    SELECT 1
                    FROM work_continuities AS wc
                    WHERE wc.work_id = CASE
                              WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                              ELSE b.source_work_id
                          END
                      AND wc.verification_status <> 'superseded'
                      AND wc.continuity_id IN (mt.source_continuity_id, mt.destination_continuity_id)
                )
                AND (
                    NOT EXISTS (
                        SELECT 1
                        FROM transition_participants AS tp0
                        JOIN _entity_identity_map AS im0
                          ON im0.raw_entity_id = tp0.entity_id
                        JOIN _v_resolved_appearances AS ra0
                          ON ra0.canonical_entity_id = im0.canonical_entity_id
                        JOIN work_continuities AS wc0
                          ON wc0.work_id = ra0.work_id
                        JOIN _v_supported_work_pairs AS sb0
                          ON (sb0.source_work_id = ra0.work_id AND sb0.target_work_id = eo.work_id)
                          OR (sb0.target_work_id = ra0.work_id AND sb0.source_work_id = eo.work_id)
                        WHERE tp0.transition_id = mt.transition_id
                          AND tp0.verification_status <> 'superseded'
                          AND wc0.verification_status <> 'superseded'
                          AND wc0.continuity_id = mt.source_continuity_id
                          AND ra0.work_id <> eo.work_id
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM transition_participants AS tp
                        JOIN _entity_identity_map AS im
                          ON im.raw_entity_id = tp.entity_id
                        JOIN _v_resolved_appearances AS ra
                          ON ra.canonical_entity_id = im.canonical_entity_id
                        JOIN work_continuities AS pwc
                          ON pwc.work_id = ra.work_id
                        JOIN works AS pw
                          ON pw.work_id = ra.work_id
                        WHERE tp.transition_id = mt.transition_id
                          AND tp.verification_status <> 'superseded'
                          AND pwc.verification_status <> 'superseded'
                          AND pwc.continuity_id = mt.source_continuity_id
                          AND ra.work_id = CASE
                                  WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                                  ELSE b.source_work_id
                              END
                          AND NOT EXISTS (
                              SELECT 1
                              FROM _v_resolved_appearances AS ra2
                              JOIN work_continuities AS pwc2
                                ON pwc2.work_id = ra2.work_id
                              JOIN works AS pw2
                                ON pw2.work_id = ra2.work_id
                              JOIN _v_supported_work_pairs AS sb2
                                ON (sb2.source_work_id = ra2.work_id AND sb2.target_work_id = eo.work_id)
                                OR (sb2.target_work_id = ra2.work_id AND sb2.source_work_id = eo.work_id)
                              WHERE ra2.canonical_entity_id = im.canonical_entity_id
                                AND pwc2.verification_status <> 'superseded'
                                AND pwc2.continuity_id = mt.source_continuity_id
                                AND ra2.work_id <> eo.work_id
                                AND (
                                    COALESCE(NULLIF(TRIM(pw2.release_sort_date), ''), '9999-99-99')
                                        > COALESCE(NULLIF(TRIM(pw.release_sort_date), ''), '9999-99-99')
                                    OR (
                                        COALESCE(NULLIF(TRIM(pw2.release_sort_date), ''), '9999-99-99')
                                            = COALESCE(NULLIF(TRIM(pw.release_sort_date), ''), '9999-99-99')
                                        AND ra2.work_id > ra.work_id
                                    )
                                )
                          )
                    )
                )
            )
            OR EXISTS (
                SELECT 1
                FROM transition_participants AS tpv
                JOIN _entity_identity_map AS imv
                  ON imv.raw_entity_id = tpv.entity_id
                JOIN _v_resolved_appearances AS rav
                  ON rav.canonical_entity_id = imv.canonical_entity_id
                WHERE tpv.transition_id = mt.transition_id
                  AND tpv.verification_status <> 'superseded'
                  AND rav.verification_status = 'source_verified'
                  AND rav.work_id = CASE
                          WHEN eo.work_id = b.source_work_id THEN b.target_work_id
                          ELSE b.source_work_id
                      END
            )
        )
        """
    )
