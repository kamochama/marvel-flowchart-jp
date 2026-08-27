from __future__ import annotations

import csv
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from .ids import slug_id


VALID_MODES = {"all_pairs", "adjacent_release", "target_centric", "explicit_only", "combined_all_pairs"}


def _work_sort_key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("release_sort_date") or "9999-99-99").strip() or "9999-99-99", row["work_id"].strip())


def _ordered_pair(a: str, b: str, work_order: dict[str, tuple[str, str]]) -> tuple[str, str]:
    if work_order.get(a, ("9999", a)) <= work_order.get(b, ("9999", b)):
        return a, b
    return b, a


def _joined(values: list[str] | set[str]) -> str:
    return "|".join(sorted({value.strip() for value in values if value and value.strip()}))


def _reason_row(
    source: str,
    target: str,
    kind: str,
    *,
    entity_id: str = "",
    relation_id: str = "",
    support_fact_ids: str = "",
    appearance_kinds: str = "",
    verification_statuses: str = "",
    certainty_values: str = "",
    notes: str = "",
) -> dict[str, str]:
    discriminator = entity_id or relation_id or support_fact_ids or notes or kind
    return {
        "reason_id": slug_id("reason", source, target, kind, discriminator),
        "source_work_id": source,
        "target_work_id": target,
        "reason_kind": kind,
        "entity_id": entity_id,
        "relation_id": relation_id,
        "support_fact_ids": support_fact_ids,
        "appearance_kinds": appearance_kinds,
        "verification_statuses": verification_statuses,
        "certainty_values": certainty_values,
        "notes": notes,
    }


def _variant_components(entity_relations: list[dict[str, str]]) -> dict[str, str]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for row in entity_relations:
        if (row.get("verification_status") or "").strip() == "superseded":
            continue
        if (row.get("relation_kind") or "").strip() != "variant_of":
            continue
        a = (row.get("source_entity_id") or "").strip()
        b = (row.get("target_entity_id") or "").strip()
        if a and b:
            union(a, b)
    return {entity: find(entity) for entity in list(parent)}


def _appearance_reason_metadata(rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        "support_fact_ids": _joined([row.get("appearance_id", "") for row in rows]),
        "appearance_kinds": _joined([row.get("appearance_kind", "") for row in rows]),
        "verification_statuses": _joined([row.get("verification_status", "") for row in rows]),
        "certainty_values": _joined([row.get("certainty", "") for row in rows]),
    }


def derive_reasons(
    works: list[dict[str, str]],
    appearances: list[dict[str, str]],
    explicit_relations: list[dict[str, str]],
    entity_relations: list[dict[str, str]],
    mode: str,
    *,
    portrayals: list[dict[str, str]] | None = None,
    include_variants: bool = False,
    target_work_id: str | None = None,
) -> list[dict[str, str]]:
    """Derive work-pair reasons from canonical facts.

    Portrayals are accepted only so callers can pass the whole library bundle;
    performer identity is intentionally not consulted when deriving character
    relationships. Every derived reason keeps the IDs and audit states of its
    supporting canonical facts so view policy can style reasons without
    rewriting or deleting facts.
    """
    del portrayals
    if mode not in VALID_MODES:
        raise ValueError(f"unsupported derivation mode: {mode}")
    if mode == "target_centric" and not target_work_id:
        raise ValueError("target_centric mode requires target_work_id")

    work_order = {row["work_id"].strip(): _work_sort_key(row) for row in works}
    appearances_by_entity: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in appearances:
        entity_id = (row.get("entity_id") or "").strip()
        work_id = (row.get("work_id") or "").strip()
        status = (row.get("verification_status") or "").strip()
        if entity_id and work_id and status != "superseded":
            appearances_by_entity[entity_id][work_id].append(row)

    reasons: list[dict[str, str]] = []

    if mode != "explicit_only":
        for entity_id in sorted(appearances_by_entity):
            by_work = appearances_by_entity[entity_id]
            ordered_works = sorted(by_work, key=lambda w: work_order.get(w, ("9999-99-99", w)))
            if mode == "adjacent_release":
                candidate_pairs = list(zip(ordered_works, ordered_works[1:]))
            elif mode == "target_centric":
                if target_work_id not in ordered_works:
                    candidate_pairs = []
                else:
                    target_key = work_order.get(target_work_id, ("9999-99-99", target_work_id))
                    candidate_pairs = [(w, target_work_id) for w in ordered_works if w != target_work_id and work_order.get(w, ("9999-99-99", w)) <= target_key]
            else:
                candidate_pairs = list(combinations(ordered_works, 2))
            for a, b in candidate_pairs:
                source, target = _ordered_pair(a, b, work_order)
                metadata = _appearance_reason_metadata(by_work[source] + by_work[target])
                reasons.append(_reason_row(source, target, "shared_entity", entity_id=entity_id, **metadata))

        if include_variants:
            components = _variant_components(entity_relations)
            grouped: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
            for entity_id, work_map in appearances_by_entity.items():
                root = components.get(entity_id)
                if root:
                    grouped[root][entity_id].update(work_map)
            for root in sorted(grouped):
                entity_map = grouped[root]
                entity_ids = sorted(entity_map)
                for e1, e2 in combinations(entity_ids, 2):
                    for a in sorted(entity_map[e1]):
                        for b in sorted(entity_map[e2]):
                            if a == b:
                                continue
                            source, target = _ordered_pair(a, b, work_order)
                            if mode == "target_centric" and target != target_work_id:
                                continue
                            rows = appearances_by_entity[e1][a] + appearances_by_entity[e2][b]
                            metadata = _appearance_reason_metadata(rows)
                            reasons.append(_reason_row(source, target, "variant_entity", entity_id=f"{e1}|{e2}", notes="variant_of relation explicitly enabled", **metadata))

    if mode in {"explicit_only", "combined_all_pairs"}:
        for row in explicit_relations:
            if (row.get("verification_status") or "").strip() == "superseded":
                continue
            source = (row.get("source_work_id") or "").strip()
            target = (row.get("target_work_id") or "").strip()
            relation_id = (row.get("work_relation_id") or "").strip()
            if not source or not target or source == target:
                continue
            notes = "; ".join(part for part in [row.get("relation_kind", ""), row.get("relation_scope", ""), row.get("directness", "")] if part)
            reasons.append(_reason_row(
                source,
                target,
                "explicit_relation",
                relation_id=relation_id,
                support_fact_ids=relation_id,
                verification_statuses=(row.get("verification_status") or "").strip(),
                certainty_values=(row.get("certainty") or "").strip(),
                notes=notes,
            ))

    by_id = {row["reason_id"]: row for row in reasons}
    return sorted(by_id.values(), key=lambda r: (r["source_work_id"], r["target_work_id"], r["reason_kind"], r["entity_id"], r["relation_id"], r["reason_id"]))


def collapse_reasons_to_edges(reasons: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in reasons:
        grouped[(row["source_work_id"], row["target_work_id"])].append(row)

    edges: list[dict[str, str]] = []
    for (source, target), rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda r: r["reason_id"])
        edges.append({
            "edge_id": slug_id("edge", source, target),
            "source_work_id": source,
            "target_work_id": target,
            "reason_ids": "|".join(r["reason_id"] for r in ordered),
            "reason_count": str(len(ordered)),
        })
    return edges


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_derived_edges(repo_root: Path, mode: str = "combined_all_pairs") -> dict[str, int]:
    library = repo_root / "data" / "library"
    derived = repo_root / "data" / "derived"
    reasons = derive_reasons(
        _read_csv(library / "works.csv"),
        _read_csv(library / "appearances.csv"),
        _read_csv(library / "work_relations.csv"),
        _read_csv(library / "entity_relations.csv"),
        mode=mode,
        portrayals=_read_csv(library / "portrayals.csv"),
    )
    edges = collapse_reasons_to_edges(reasons)
    _write_csv(
        derived / "work_pair_reasons.csv",
        reasons,
        [
            "reason_id",
            "source_work_id",
            "target_work_id",
            "reason_kind",
            "entity_id",
            "relation_id",
            "support_fact_ids",
            "appearance_kinds",
            "verification_statuses",
            "certainty_values",
            "notes",
        ],
    )
    _write_csv(derived / "work_edges_all.csv", edges, ["edge_id", "source_work_id", "target_work_id", "reason_ids", "reason_count"])
    return {"work_pair_reasons": len(reasons), "work_edges_all": len(edges)}
