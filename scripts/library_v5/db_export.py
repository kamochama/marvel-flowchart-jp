from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .db_compile import open_query_connection
from .ids import slug_id


REASON_FIELDS = [
    "reason_id",
    "source_work_id",
    "target_work_id",
    "reason_kind",
    "entity_id",
    "relation_id",
    "transition_id",
    "event_id",
    "event_occurrence_id",
    "source_continuity_id",
    "destination_continuity_id",
    "participant_fact_ids",
    "support_fact_ids",
    "appearance_kinds",
    "verification_statuses",
    "certainty_values",
    "notes",
]
EDGE_FIELDS = ["edge_id", "source_work_id", "target_work_id", "reason_ids", "reason_count"]


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _reason_rows(db_path: Path) -> list[dict[str, str]]:
    connection = open_query_connection(db_path)
    try:
        cursor = connection.execute(
            """
            SELECT source_work_id,target_work_id,reason_kind,
                   canonical_entity_id,relation_id,
                   transition_id,event_id,event_occurrence_id,
                   source_continuity_id,destination_continuity_id,participant_fact_ids,
                   support_fact_ids,appearance_kinds,verification_statuses,certainty_values,
                   notes,reason_discriminator
            FROM v_work_connection_reasons
            ORDER BY source_work_id,target_work_id,reason_kind,
                     canonical_entity_id,relation_id,transition_id,event_occurrence_id,reason_discriminator
            """
        )
        rows: list[dict[str, str]] = []
        for (
            source_work_id,
            target_work_id,
            reason_kind,
            canonical_entity_id,
            relation_id,
            transition_id,
            event_id,
            event_occurrence_id,
            source_continuity_id,
            destination_continuity_id,
            participant_fact_ids,
            support_fact_ids,
            appearance_kinds,
            verification_statuses,
            certainty_values,
            notes,
            reason_discriminator,
        ) in cursor:
            source = str(source_work_id or "")
            target = str(target_work_id or "")
            kind = str(reason_kind or "")
            discriminator = str(reason_discriminator or "") or kind
            rows.append(
                {
                    "reason_id": slug_id("reason", source, target, kind, discriminator),
                    "source_work_id": source,
                    "target_work_id": target,
                    "reason_kind": kind,
                    "entity_id": str(canonical_entity_id or ""),
                    "relation_id": str(relation_id or ""),
                    "transition_id": str(transition_id or ""),
                    "event_id": str(event_id or ""),
                    "event_occurrence_id": str(event_occurrence_id or ""),
                    "source_continuity_id": str(source_continuity_id or ""),
                    "destination_continuity_id": str(destination_continuity_id or ""),
                    "participant_fact_ids": str(participant_fact_ids or ""),
                    "support_fact_ids": str(support_fact_ids or ""),
                    "appearance_kinds": str(appearance_kinds or ""),
                    "verification_statuses": str(verification_statuses or ""),
                    "certainty_values": str(certainty_values or ""),
                    "notes": str(notes or ""),
                }
            )
        return sorted(
            rows,
            key=lambda row: (
                row["source_work_id"],
                row["target_work_id"],
                row["reason_kind"],
                row["entity_id"],
                row["relation_id"],
                row["transition_id"],
                row["event_occurrence_id"],
                row["reason_id"],
            ),
        )
    finally:
        connection.close()


def _edge_rows(reasons: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in reasons:
        grouped[(row["source_work_id"], row["target_work_id"])].append(row)

    edges: list[dict[str, str]] = []
    for (source, target), rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: row["reason_id"])
        edges.append(
            {
                "edge_id": slug_id("edge", source, target),
                "source_work_id": source,
                "target_work_id": target,
                "reason_ids": "|".join(row["reason_id"] for row in ordered),
                "reason_count": str(len(ordered)),
            }
        )
    return edges


def export_work_graph(db_path: Path, output_dir: Path) -> dict[str, int]:
    reasons = _reason_rows(db_path)
    edges = _edge_rows(reasons)
    _write_csv(output_dir / "work_pair_reasons.csv", reasons, REASON_FIELDS)
    _write_csv(output_dir / "work_edges_all.csv", edges, EDGE_FIELDS)
    return {"work_pair_reasons": len(reasons), "work_edges_all": len(edges)}
