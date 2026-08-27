from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .ids import slug_id


_WORK_DROP_FIELDS = {
    "priority",
    "branch_ja",
    "branch_en",
    "chronology_lane",
    "chronology_order",
    "chronology_track",
    "chronology_certainty",
    "chronology_note",
}


def migrate_works(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    migrated: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        work_id = (row.get("work_id") or "").strip()
        if not work_id:
            raise ValueError("legacy work row lacks work_id")
        if work_id in seen:
            raise ValueError(f"duplicate work_id in legacy input: {work_id}")
        seen.add(work_id)
        migrated.append({key: value for key, value in row.items() if key not in _WORK_DROP_FIELDS})
    return migrated


def _certainty_from_legacy(row: dict[str, str]) -> str:
    confidence = (row.get("audit_confidence") or "").strip().lower()
    return {"high": "confirmed", "medium": "strong", "low": "uncertain"}.get(confidence, "unknown")


def _is_cancelled_wonder_man_edge(row: dict[str, str]) -> bool:
    source = (row.get("source_id") or "").strip()
    target = (row.get("target_id") or "").strip()
    return source.startswith("wonder-man-s1") and target.startswith("wonder-man-s2")


def _relation_row(row: dict[str, str]) -> dict[str, str]:
    source = row["source_id"].strip()
    target = row["target_id"].strip()
    kind = (row.get("relation_kind") or "story_link").strip() or "story_link"
    notes = " | ".join(
        part.strip()
        for part in (row.get("reason", ""), row.get("proxy_note", ""), row.get("management_notes", ""))
        if part and part.strip()
    )
    return {
        "work_relation_id": slug_id("work-relation", source, target, kind),
        "source_work_id": source,
        "target_work_id": target,
        "relation_kind": kind,
        "relation_scope": (row.get("relation_scope") or "story").strip() or "story",
        "directness": (row.get("directness") or "indirect").strip() or "indirect",
        "continuity_scope": (row.get("continuity_scope") or "same_or_intended").strip() or "same_or_intended",
        "certainty": _certainty_from_legacy(row),
        "notes": notes or "Migrated from legacy connections.csv pending v5 fact audit.",
    }


def migrate_connections(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    relations: list[dict[str, str]] = []
    dispositions: list[dict[str, str]] = []
    seen_relation_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        edge_id = (row.get("edge_id") or "").strip() or f"legacy-connection-{index:06d}"
        source = (row.get("source_id") or "").strip()
        target = (row.get("target_id") or "").strip()
        scope = (row.get("relation_scope") or "").strip()
        kind = (row.get("relation_kind") or "").strip()

        if not source or not target or source == target:
            disposition = "rejected_invalid"
            relation_id = ""
            note = "Missing endpoint or self-loop; preserved only in migration ledger."
        elif _is_cancelled_wonder_man_edge(row):
            disposition = "rejected_superseded"
            relation_id = ""
            note = "Cancelled/superseded Wonder Man Season 2 plan is not a current canonical work relation."
        elif scope == "character" or kind == "character_continuity":
            disposition = "appearance_derived_pending_audit"
            relation_id = ""
            note = "Character-only legacy edge moves to appearances/portrayals; original edge metadata remains in this ledger."
        else:
            relation = _relation_row(row)
            relation_id = relation["work_relation_id"]
            if relation_id not in seen_relation_ids:
                relations.append(relation)
                seen_relation_ids.add(relation_id)
            if scope == "promotion" or kind == "promotion":
                disposition = "migrated_promotion_fact"
                note = "Official promotional association retained as a promotion fact; prewatch tier is view/policy data."
            else:
                disposition = "migrated_explicit_relation"
                note = "Legacy relation retained as explicit v5 relation seed pending content audit."

        dispositions.append({
            "legacy_row_id": f"connection-{index:06d}",
            "legacy_edge_id": edge_id,
            "source_id": source,
            "target_id": target,
            "legacy_relation_scope": scope,
            "legacy_relation_kind": kind,
            "disposition": disposition,
            "work_relation_id": relation_id,
            "migration_note": note,
            "legacy_reason": (row.get("reason") or "").strip(),
        })

    return {"work_relations": relations, "dispositions": dispositions}


def migrate_chronology(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    continuities: list[dict[str, str]] = []
    work_continuities: list[dict[str, str]] = []
    dispositions: list[dict[str, str]] = []
    continuity_ids: dict[str, str] = {}

    for index, row in enumerate(rows, start=1):
        work_id = (row.get("work_id") or "").strip()
        world_group = (row.get("world_group") or "").strip()
        if not work_id:
            raise ValueError(f"chronology row {index} lacks work_id")
        if world_group:
            continuity_id = continuity_ids.get(world_group)
            if continuity_id is None:
                continuity_id = slug_id("continuity", world_group)
                continuity_ids[world_group] = continuity_id
                continuities.append({
                    "continuity_id": continuity_id,
                    "label_ja": world_group,
                    "label_en": "",
                    "continuity_kind": "legacy_world_group",
                    "certainty": "unknown",
                    "notes": "Migrated from legacy chronology world_group as a seed; independent continuity audit required.",
                })
            work_continuities.append({
                "work_continuity_id": slug_id("work-continuity", work_id, continuity_id),
                "work_id": work_id,
                "continuity_id": continuity_id,
                "relation_to_continuity": "legacy_group_membership",
                "certainty": "unknown",
                "notes": (row.get("note") or "").strip(),
            })
        dispositions.append({
            "legacy_row_id": f"chronology-{index:06d}",
            "work_id": work_id,
            "world_group": world_group,
            "lane": (row.get("lane") or "").strip(),
            "track": (row.get("track") or "").strip(),
            "legacy_order": (row.get("order") or "").strip(),
            "disposition": "legacy_display_placement_seed",
            "migration_note": "lane/order/track are not promoted to source-backed chronology assertions without evidence audit.",
        })

    return {
        "continuities": continuities,
        "work_continuities": work_continuities,
        "chronology_assertions": [],
        "dispositions": dispositions,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_work_relation_tables(repo_root: Path) -> dict[str, int]:
    library = repo_root / "data" / "library"
    migration = repo_root / "data" / "migration"

    legacy_works = _read_csv(repo_root / "data" / "works.csv")
    legacy_connections = _read_csv(repo_root / "data" / "connections.csv")
    legacy_chronology = _read_csv(repo_root / "data" / "chronology.csv")

    works = migrate_works(legacy_works)
    conn = migrate_connections(legacy_connections)
    chrono = migrate_chronology(legacy_chronology)

    work_fields = list(works[0].keys()) if works else ["work_id"]
    _write_csv(library / "works.csv", works, work_fields)
    _write_csv(library / "work_relations.csv", conn["work_relations"], ["work_relation_id", "source_work_id", "target_work_id", "relation_kind", "relation_scope", "directness", "continuity_scope", "certainty", "notes"])
    _write_csv(library / "continuities.csv", chrono["continuities"], ["continuity_id", "label_ja", "label_en", "continuity_kind", "certainty", "notes"])
    _write_csv(library / "work_continuities.csv", chrono["work_continuities"], ["work_continuity_id", "work_id", "continuity_id", "relation_to_continuity", "certainty", "notes"])
    _write_csv(library / "chronology_assertions.csv", chrono["chronology_assertions"], ["chronology_assertion_id", "continuity_id", "earlier_work_id", "later_work_id", "certainty", "notes"])
    _write_csv(migration / "connection_dispositions.csv", conn["dispositions"], ["legacy_row_id", "legacy_edge_id", "source_id", "target_id", "legacy_relation_scope", "legacy_relation_kind", "disposition", "work_relation_id", "migration_note", "legacy_reason"])
    _write_csv(migration / "chronology_dispositions.csv", chrono["dispositions"], ["legacy_row_id", "work_id", "world_group", "lane", "track", "legacy_order", "disposition", "migration_note"])

    # Canonical source registry starts as a byte-semantic copy of the legacy registry;
    # later evidence normalization may evolve its columns without losing source IDs.
    sources = _read_csv(repo_root / "data" / "sources.csv")
    source_fields = list(sources[0].keys()) if sources else ["source_id"]
    _write_csv(library / "sources.csv", sources, source_fields)

    return {
        "works": len(works),
        "work_relations": len(conn["work_relations"]),
        "connection_dispositions": len(conn["dispositions"]),
        "continuities": len(chrono["continuities"]),
        "work_continuities": len(chrono["work_continuities"]),
        "chronology_dispositions": len(chrono["dispositions"]),
        "sources": len(sources),
    }
