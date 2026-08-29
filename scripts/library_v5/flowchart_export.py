from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .db_compile import open_query_connection
from .db_export import reason_rows
from .derive_compat import default_flowchart_policy
from .ids import slug_id


NODE_FIELDS = (
    "work_id",
    "title_ja",
    "title_en",
    "title_official",
    "release",
    "release_raw",
    "format",
    "status",
    "classification",
    "ja_status",
    "japan_date",
    "japan_type",
    "source_url",
    "source_note",
    "notes",
    "release_sort_date",
    "release_display_date",
    "release_kind",
    "release_certainty",
    "release_precision",
    "release_source_note",
    "aliases_ja",
    "title_audit_status",
    "title_audit_source_url",
    "title_last_verified",
    "title_management_note",
    "stable_id_note",
)

EDGE_PRESENTATION_FIELDS = (
    "type",
    "type_en",
    "strength",
    "render_class",
    "importance",
    "importance_ja",
    "importance_note",
)

_KIND_PRIORITY = {
    "multiverse_transition": 3,
    "explicit_relation": 2,
    "shared_entity": 1,
}
_STRENGTH_ORDER = ("very strong", "strong", "moderate", "weak")
_IMPORTANCE_ORDER = ("core", "recommended", "reference", "optional")


def _text(value: object) -> str:
    return str(value or "")


def _split_values(value: str) -> set[str]:
    return {part.strip() for part in value.split("|") if part.strip()}


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_view_policy(repo_root: Path) -> dict[str, Any]:
    """Load checked-in policy while retaining newly required safe defaults."""
    policy_path = repo_root / "views" / "flowchart" / "policy.json"
    if not policy_path.exists():
        return default_flowchart_policy()
    try:
        loaded = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"flowchart_policy_invalid:{policy_path}") from exc
    if not isinstance(loaded, dict):
        raise ValueError("flowchart_policy_must_be_object")
    return _merge_dicts(default_flowchart_policy(), loaded)


def _query_dicts(db_path: Path, query: str) -> list[dict[str, object]]:
    connection = open_query_connection(db_path)
    try:
        cursor = connection.execute(query)
        columns = [description[0] for description in cursor.description or ()]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _node_rows(db_path: Path) -> list[dict[str, str]]:
    rows = _query_dicts(
        db_path,
        "SELECT * FROM v_flowchart_nodes ORDER BY work_id",
    )
    result: list[dict[str, str]] = []
    for row in rows:
        if tuple(row) != NODE_FIELDS:
            raise ValueError(
                "flowchart_node_contract_mismatch: "
                f"expected={NODE_FIELDS!r} actual={tuple(row)!r}"
            )
        result.append({field: _text(row[field]) for field in NODE_FIELDS})
    return result


def _candidate_rows(db_path: Path) -> list[dict[str, object]]:
    return _query_dicts(
        db_path,
        """
        SELECT source_work_id,target_work_id,reason_count,reason_keys
        FROM v_flowchart_edge_candidates
        ORDER BY source_work_id,target_work_id
        """,
    )


def _threshold_matches(
    threshold: object,
    *,
    statuses: set[str],
    certainties: set[str],
    notes: str,
    strength: str | None = None,
) -> bool:
    if not isinstance(threshold, dict):
        return False
    required_statuses = {str(value) for value in threshold.get("verification_statuses", [])}
    required_certainties = {str(value) for value in threshold.get("certainty_values", [])}
    notes_any = [str(value).casefold() for value in threshold.get("notes_any", [])]
    if required_statuses and not statuses.issubset(required_statuses):
        return False
    if required_certainties and not certainties.issubset(required_certainties):
        return False
    if notes_any and not any(marker in notes.casefold() for marker in notes_any):
        return False
    strengths = {str(value) for value in threshold.get("strengths", [])}
    return not strengths or (strength is not None and strength in strengths)


def _reason_kind_presentation(
    kind: str,
    rows: list[dict[str, str]],
    policy: dict[str, Any],
) -> dict[str, str]:
    rules = policy.get("reason_kind_rules", {})
    rule = rules.get(kind) if isinstance(rules, dict) else None
    if not isinstance(rule, dict):
        kind = "fallback"
        rule = rules.get(kind, {}) if isinstance(rules, dict) else {}
    statuses = set().union(*(_split_values(row["verification_statuses"]) for row in rows)) if rows else set()
    certainties = set().union(*(_split_values(row["certainty_values"]) for row in rows)) if rows else set()
    notes = " ".join(row["notes"] for row in rows)
    # Missing metadata is treated as the least certain value. This prevents a
    # partially populated row from receiving a stronger visual treatment.
    statuses = statuses or {"legacy_seed"}
    certainties = certainties or {"unknown"}
    strength_thresholds = rule.get("strength_thresholds", {})
    strength = "weak"
    if isinstance(strength_thresholds, dict):
        for candidate in _STRENGTH_ORDER:
            if _threshold_matches(
                strength_thresholds.get(candidate),
                statuses=statuses,
                certainties=certainties,
                notes=notes,
            ):
                strength = candidate
                break

    importance = "reference"
    importance_thresholds = rule.get("importance_thresholds", {})
    if isinstance(importance_thresholds, dict):
        for candidate in _IMPORTANCE_ORDER:
            if _threshold_matches(
                importance_thresholds.get(candidate),
                statuses=statuses,
                certainties=certainties,
                notes=notes,
                strength=strength,
            ):
                importance = candidate
                break

    importance_ja = rule.get("importance_ja", {})
    importance_notes = rule.get("importance_notes_ja", {})
    return {
        "type": _text(rule.get("label_ja")),
        "type_en": _text(rule.get("label_en")),
        "strength": strength,
        "render_class": _text(rule.get("render_class")) or "dotted",
        "importance": importance,
        "importance_ja": (
            _text(importance_ja.get(importance))
            if isinstance(importance_ja, dict)
            else "参照"
        ),
        "importance_note": (
            _text(importance_notes.get(importance))
            if isinstance(importance_notes, dict)
            else "保守的な参照用の接続。"
        ),
    }


def _edge_presentation(rows: list[dict[str, str]], policy: dict[str, Any]) -> dict[str, str]:
    if not rows:
        return _reason_kind_presentation("fallback", [], policy)
    kind = max(
        (row["reason_kind"] for row in rows),
        key=lambda value: (_KIND_PRIORITY.get(value, 0), value),
    )
    return _reason_kind_presentation(kind, [row for row in rows if row["reason_kind"] == kind], policy)


def _character_rows(db_path: Path) -> list[dict[str, object]]:
    history = _query_dicts(
        db_path,
        """
        SELECT h.canonical_entity_id,h.work_id,e.name_ja,e.name_en
        FROM v_entity_work_history AS h
        JOIN entities AS e ON e.entity_id = h.canonical_entity_id
        WHERE e.entity_type='character'
        ORDER BY h.canonical_entity_id,h.work_id,h.appearance_id
        """,
    )
    grouped: dict[str, dict[str, Any]] = {}
    for row in history:
        entity_id = _text(row["canonical_entity_id"])
        work_id = _text(row["work_id"])
        if not entity_id or not work_id:
            continue
        item = grouped.setdefault(
            entity_id,
            {
                "entity_id": entity_id,
                "name_ja": _text(row["name_ja"]),
                "name_en": _text(row["name_en"]),
                "work_ids": set(),
            },
        )
        item["work_ids"].add(work_id)
    return [
        {
            "entity_id": entity_id,
            "name_ja": item["name_ja"],
            "name_en": item["name_en"],
            "work_ids": sorted(item["work_ids"]),
        }
        for entity_id, item in sorted(grouped.items())
    ]


def _manifest_value(manifest: dict[str, object], key: str) -> str:
    if key == "logical_fingerprint":
        value = manifest.get("logical_fingerprint") or manifest.get("equivalence")
    else:
        value = manifest.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"flowchart_manifest_missing:{key}")
    return value


def export_flowchart(
    repo_root: Path,
    db_path: Path,
    output_path: Path,
    *,
    db_manifest: dict[str, object],
) -> dict[str, int]:
    """Write the deterministic static flowchart artifact from compiled views."""
    repo_root = repo_root.resolve()
    nodes = _node_rows(db_path)
    reasons = sorted(reason_rows(db_path), key=lambda row: row["reason_id"])
    view_policy = _load_view_policy(repo_root)
    reasons_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    reasons_by_id = {row["reason_id"]: row for row in reasons}
    for row in reasons:
        reasons_by_pair[(row["source_work_id"], row["target_work_id"])].append(row)

    candidates = _candidate_rows(db_path)
    edges: list[dict[str, object]] = []
    candidate_pairs = {
        (_text(row["source_work_id"]), _text(row["target_work_id"]))
        for row in candidates
    }
    orphan_pairs = sorted(set(reasons_by_pair) - candidate_pairs)
    if orphan_pairs:
        raise ValueError(f"flowchart_reason_without_candidate:{orphan_pairs!r}")
    for candidate in candidates:
        source = _text(candidate["source_work_id"])
        target = _text(candidate["target_work_id"])
        pair_reasons = sorted(reasons_by_pair[(source, target)], key=lambda row: row["reason_id"])
        reason_ids = [row["reason_id"] for row in pair_reasons]
        candidate_count = int(candidate["reason_count"] or 0)
        if candidate_count != len(reason_ids):
            raise ValueError(
                "flowchart_candidate_reason_count_mismatch:"
                f"{source}:{target}:{candidate_count}!={len(reason_ids)}"
            )
        if any(reason_id not in reasons_by_id for reason_id in reason_ids):
            raise ValueError(f"flowchart_edge_reason_missing:{source}:{target}")
        edge: dict[str, object] = {
            "edge_id": slug_id("edge", source, target),
            "source_work_id": source,
            "target_work_id": target,
            "reason_ids": reason_ids,
            "reason_count": len(reason_ids),
        }
        edge.update(_edge_presentation(pair_reasons, view_policy))
        edges.append(edge)

    payload = {
        "schema_version": "1",
        "generated_from": {
            "db_schema_version": _manifest_value(db_manifest, "db_schema_version"),
            "logical_fingerprint": _manifest_value(db_manifest, "logical_fingerprint"),
        },
        "nodes": nodes,
        "edges": edges,
        "reasons": reasons,
        "characters": _character_rows(db_path),
        "view_policy": view_policy,
    }
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    output_path.write_bytes(serialized.encode("utf-8"))
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "reasons": len(reasons),
        "characters": len(payload["characters"]),
    }
