"""Independent connectivity audit for canonical facts and derived exports.

This module deliberately does not import the production edge derivation or
selection implementation.  It checks the five separate connectivity domains:
work relations (R), appearances/entities (A), events/transitions (E),
chronology assertions (C), and export/view projection (P).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping


ACTIVE = "superseded"
CSV_TABLES = (
    "works.csv",
    "work_relations.csv",
    "appearances.csv",
    "entity_relations.csv",
    "entities.csv",
    "events.csv",
    "event_occurrences.csv",
    "event_participants.csv",
    "multiverse_transitions.csv",
    "transition_participants.csv",
    "chronology_assertions.csv",
    "work_continuities.csv",
    "evidence.csv",
    "reviews.csv",
)


def _active(rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in rows if (row.get("verification_status") or "").strip() != ACTIVE]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_repository_tables(root: Path) -> dict[str, list[dict[str, str]]]:
    library = root / "data" / "library"
    tables = {name: _read_csv(library / name) for name in CSV_TABLES if name != "reviews.csv"}
    tables["reviews.csv"] = _read_csv(root / "data" / "content_audit" / "reviews.csv")
    return tables


def _load_repository_derived(root: Path) -> tuple[dict[str, list[dict[str, str]]], dict[str, Any], str]:
    derived_root = root / "data" / "derived"
    derived = {
        "work_edges_all.csv": _read_csv(derived_root / "work_edges_all.csv"),
        "work_pair_reasons.csv": _read_csv(derived_root / "work_pair_reasons.csv"),
    }
    flowchart_path = derived_root / "flowchart.json"
    flowchart: dict[str, Any] = {}
    if flowchart_path.exists():
        flowchart = json.loads(flowchart_path.read_text(encoding="utf-8"))
    html = (root / "index.html").read_text(encoding="utf-8") if (root / "index.html").exists() else ""
    return derived, flowchart, html


def _key(row: Mapping[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def _split_ids(value: str | None) -> list[str]:
    return sorted({part.strip() for part in (value or "").split("|") if part.strip()})


def _sort_key(work_id: str, works: Mapping[str, Mapping[str, str]]) -> tuple[str, str]:
    row = works.get(work_id, {})
    date = _key(row, "release_sort_date") or "9999-99-99"
    return date, work_id


def _edge_key(source: str, target: str) -> str:
    return f"{source}->{target}"


def _record(
    records: list[dict[str, Any]],
    *,
    domain: str,
    case_id: str,
    source: str = "",
    target: str = "",
    expected: str = "",
    actual: str = "",
    coverage: str = "complete",
    verdict: str = "pass",
    support_fact_ids: Iterable[str] = (),
    evidence_ids: Iterable[str] = (),
    review_ids: Iterable[str] = (),
    disposition: str = "keep",
) -> None:
    records.append(
        {
            "domain": domain,
            "case_id": case_id,
            "source_work_id": source,
            "target_work_id": target,
            "expected": expected,
            "actual": actual,
            "coverage": coverage,
            "verdict": verdict,
            "support_fact_ids": sorted(set(support_fact_ids)),
            "evidence_ids": sorted(set(evidence_ids)),
            "review_ids": sorted(set(review_ids)),
            "disposition": disposition,
        }
    )


def _audit_provenance(
    row: Mapping[str, str],
    *,
    fact_table: str,
    fact_id: str,
    evidence_by_fact: Mapping[tuple[str, str], list[str]],
    reviews_by_fact: Mapping[tuple[str, str], list[str]],
) -> tuple[str, str, list[str], list[str], list[str], str]:
    status = _key(row, "verification_status")
    evidence_ids = evidence_by_fact.get((fact_table, fact_id), [])
    review_ids = reviews_by_fact.get((fact_table, fact_id), [])
    if status == "source_verified":
        if not evidence_ids or not review_ids:
            return "partial", "fail", [], evidence_ids, review_ids, "canonical-fix"
        return "complete", "pass", [], evidence_ids, review_ids, "keep"
    if status == "conflicted":
        return "partial", "conflict", [], evidence_ids, review_ids, "conflict"
    if status == "legacy_seed":
        return "partial", "deferred", [], evidence_ids, review_ids, "needs-source"
    return "partial", "deferred", [], evidence_ids, review_ids, "defer"


def _resolve_identity(entity_relations: Iterable[Mapping[str, str]]) -> tuple[dict[str, str], list[str]]:
    direct: dict[str, str] = {}
    issues: list[str] = []
    for row in entity_relations:
        if _key(row, "verification_status") == ACTIVE or _key(row, "relation_kind") != "identity_of":
            continue
        source, target = _key(row, "source_entity_id"), _key(row, "target_entity_id")
        if not source or not target or source == target:
            continue
        if source in direct and direct[source] != target:
            issues.append(f"identity-conflict:{source}")
        else:
            direct[source] = target

    def resolve(entity_id: str) -> str:
        seen: set[str] = set()
        current = entity_id
        while current in direct:
            if current in seen:
                issues.append(f"identity-cycle:{current}")
                return entity_id
            seen.add(current)
            current = direct[current]
        return current

    ids = set(direct) | set(direct.values())
    return {entity_id: resolve(entity_id) for entity_id in ids}, sorted(set(issues))


def _summary(records: list[dict[str, Any]], *, projection: dict[str, int], transition: dict[str, int]) -> dict[str, Any]:
    return {
        "verdicts": dict(sorted(Counter(row["verdict"] for row in records).items())),
        "coverage": dict(sorted(Counter(row["coverage"] for row in records).items())),
        "dispositions": dict(sorted(Counter(row["disposition"] for row in records).items())),
        "domains": dict(sorted(Counter(row["domain"] for row in records).items())),
        "projection": projection,
        "transition": transition,
    }


def audit_inputs(
    tables: Mapping[str, Iterable[Mapping[str, str]]],
    derived: Mapping[str, Iterable[Mapping[str, str]]],
    *,
    html: str = "",
    flowchart: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit already-loaded tables and derived products without production imports."""

    table_data = {name: [dict(row) for row in rows] for name, rows in tables.items()}
    flowchart = dict(flowchart or {})
    works_rows = _active(table_data.get("works.csv", []))
    relation_rows = _active(table_data.get("work_relations.csv", []))
    appearance_rows = _active(table_data.get("appearances.csv", []))
    entity_relation_rows = _active(table_data.get("entity_relations.csv", []))
    event_rows = _active(table_data.get("events.csv", []))
    occurrence_rows = _active(table_data.get("event_occurrences.csv", []))
    event_participant_rows = _active(table_data.get("event_participants.csv", []))
    transition_rows = _active(table_data.get("multiverse_transitions.csv", []))
    transition_participant_rows = _active(table_data.get("transition_participants.csv", []))
    chronology_rows = _active(table_data.get("chronology_assertions.csv", []))
    continuity_rows = _active(table_data.get("work_continuities.csv", []))
    evidence_rows = table_data.get("evidence.csv", [])
    review_rows = table_data.get("reviews.csv", [])
    works = {_key(row, "work_id"): row for row in works_rows if _key(row, "work_id")}
    entities = {_key(row, "entity_id"): row for row in table_data.get("entities.csv", []) if _key(row, "entity_id")}
    events = {_key(row, "event_id"): row for row in event_rows if _key(row, "event_id")}
    transitions = {_key(row, "transition_id"): row for row in transition_rows if _key(row, "transition_id")}
    evidence_by_fact: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in evidence_rows:
        fact = (_key(row, "fact_table"), _key(row, "fact_id"))
        evidence_id = _key(row, "evidence_id")
        if fact[0] and fact[1] and evidence_id:
            evidence_by_fact[fact].append(evidence_id)
    reviews_by_fact: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in review_rows:
        fact = (_key(row, "fact_table"), _key(row, "fact_id"))
        review_id = _key(row, "review_id")
        if fact[0] and fact[1] and review_id:
            reviews_by_fact[fact].append(review_id)

    edge_rows = [dict(row) for row in derived.get("work_edges_all.csv", [])]
    reason_rows = [dict(row) for row in derived.get("work_pair_reasons.csv", [])]
    payload_edges = [dict(row) for row in flowchart.get("edges", []) if isinstance(row, Mapping)]
    payload_reasons = [dict(row) for row in flowchart.get("reasons", []) if isinstance(row, Mapping)]
    actual_pairs = {
        (_key(row, "source_work_id"), _key(row, "target_work_id"))
        for row in edge_rows
        if _key(row, "source_work_id") and _key(row, "target_work_id")
    }
    payload_pairs = {
        (_key(row, "source_work_id"), _key(row, "target_work_id"))
        for row in payload_edges
        if _key(row, "source_work_id") and _key(row, "target_work_id")
    }
    reason_by_relation: dict[str, list[dict[str, str]]] = defaultdict(list)
    shared_reason_by_pair_entity: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    transition_reason_rows: list[dict[str, str]] = []
    base_reason_pairs: set[tuple[str, str]] = set()
    for row in reason_rows:
        kind = _key(row, "reason_kind")
        pair = (_key(row, "source_work_id"), _key(row, "target_work_id"))
        if kind == "explicit_relation" and _key(row, "relation_id"):
            reason_by_relation[_key(row, "relation_id")].append(row)
        elif kind == "shared_entity":
            shared_reason_by_pair_entity[(pair[0], pair[1], _key(row, "entity_id"))].append(row)
        elif kind == "multiverse_transition":
            transition_reason_rows.append(row)
        if kind != "multiverse_transition" and pair[0] and pair[1]:
            base_reason_pairs.add(pair)

    records: list[dict[str, Any]] = []

    # R — explicit work relations: FK/direction/provenance and exact export projection.
    for relation in relation_rows:
        relation_id = _key(relation, "work_relation_id")
        source, target = _key(relation, "source_work_id"), _key(relation, "target_work_id")
        structural = []
        if not relation_id or not source or not target:
            structural.append("missing relation identity or endpoint")
        if source == target and source:
            structural.append("self-loop")
        if source and source not in works:
            structural.append(f"unknown source work: {source}")
        if target and target not in works:
            structural.append(f"unknown target work: {target}")
        projected = reason_by_relation.get(relation_id, [])
        if len(projected) != 1:
            structural.append(f"explicit relation reason count={len(projected)}")
        elif (_key(projected[0], "source_work_id"), _key(projected[0], "target_work_id")) != (source, target):
            structural.append("explicit relation direction mismatch")
        coverage, verdict, _, evidence_ids, review_ids, disposition = _audit_provenance(
            relation,
            fact_table="work_relations.csv",
            fact_id=relation_id,
            evidence_by_fact=evidence_by_fact,
            reviews_by_fact=reviews_by_fact,
        )
        if structural:
            coverage, verdict, disposition = "partial", "fail", "derivation-fix"
        _record(
            records,
            domain="R",
            case_id=relation_id or f"relation:{source}->{target}",
            source=source,
            target=target,
            expected=f"one explicit_relation reason {source}->{target}",
            actual="; ".join(structural) if structural else "one exact explicit_relation reason",
            coverage=coverage,
            verdict=verdict,
            support_fact_ids=[relation_id],
            evidence_ids=evidence_ids,
            review_ids=review_ids,
            disposition=disposition,
        )
    active_relation_ids = { _key(row, "work_relation_id") for row in relation_rows }
    relation_orphans = 0
    for relation_id, projected in reason_by_relation.items():
        if relation_id not in active_relation_ids:
            relation_orphans += 1
            _record(
                records,
                domain="R",
                case_id=f"orphan-explicit-reason:{relation_id}",
                expected="active canonical work relation",
                actual="derived explicit_relation reason without active relation",
                coverage="partial",
                verdict="fail",
                support_fact_ids=[relation_id],
                disposition="derivation-fix",
            )

    # A directed relation cycle is almost always a migration or direction
    # error.  Keep this independent of the viewer's traversal implementation.
    relation_adjacency: dict[str, set[str]] = defaultdict(set)
    for relation in relation_rows:
        source, target = _key(relation, "source_work_id"), _key(relation, "target_work_id")
        if source and target and source != target:
            relation_adjacency[source].add(target)
    cycles: set[tuple[str, ...]] = set()

    def visit_cycle(node: str, path: list[str], active: set[str]) -> None:
        if node in active:
            cycle = path[path.index(node) :]
            if cycle:
                rotations = [tuple(cycle[offset:] + cycle[:offset]) for offset in range(len(cycle))]
                cycles.add(min(rotations))
            return
        active.add(node)
        path.append(node)
        for target in sorted(relation_adjacency.get(node, ())):
            visit_cycle(target, path, active)
        path.pop()
        active.remove(node)

    for source in sorted(relation_adjacency):
        visit_cycle(source, [], set())
    for cycle in sorted(cycles):
        _record(
            records,
            domain="R",
            case_id=f"relation-cycle:{'->'.join(cycle)}",
            source=cycle[0],
            target=cycle[-1],
            expected="acyclic directed work-relation graph",
            actual="directed cycle detected",
            coverage="partial",
            verdict="fail",
            support_fact_ids=(),
            disposition="canonical-fix",
        )

    # A — independent appearance/entity pairs and identity boundaries.
    identity_map, identity_issues = _resolve_identity(entity_relation_rows)
    for issue in identity_issues:
        _record(
            records,
            domain="A",
            case_id=issue,
            expected="acyclic, single-target identity_of map",
            actual=issue,
            coverage="partial",
            verdict="fail",
            disposition="canonical-fix",
        )
    appearances_by_entity: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    appearance_by_id: dict[str, dict[str, str]] = {}
    for appearance in appearance_rows:
        appearance_id = _key(appearance, "appearance_id")
        raw_entity, work_id = _key(appearance, "entity_id"), _key(appearance, "work_id")
        canonical_entity = identity_map.get(raw_entity, raw_entity)
        if appearance_id and canonical_entity and work_id:
            appearances_by_entity[canonical_entity][work_id].append(appearance_id)
            appearance_by_id[appearance_id] = appearance
    expected_shared_pairs: set[tuple[str, str, str]] = set()
    for entity_id, by_work in appearances_by_entity.items():
        ordered = sorted(by_work, key=lambda work_id: _sort_key(work_id, works))
        for source, target in combinations(ordered, 2):
            expected_shared_pairs.add((source, target, entity_id))
            matched = shared_reason_by_pair_entity.get((source, target, entity_id), [])
            support_ids = [appearance_id for work_id in (source, target) for appearance_id in by_work[work_id]]
            provenance = [
                _audit_provenance(
                    appearance_by_id[appearance_id],
                    fact_table="appearances.csv",
                    fact_id=appearance_id,
                    evidence_by_fact=evidence_by_fact,
                    reviews_by_fact=reviews_by_fact,
                )
                for appearance_id in support_ids
            ]
            evidence_ids = sorted({item for result in provenance for item in result[3]})
            review_ids = sorted({item for result in provenance for item in result[4]})
            if any(result[1] == "fail" for result in provenance):
                pair_coverage, pair_verdict, pair_disposition = "partial", "fail", "canonical-fix"
            elif any(result[1] == "conflict" for result in provenance):
                pair_coverage, pair_verdict, pair_disposition = "partial", "conflict", "conflict"
            elif all(result[1] == "pass" for result in provenance):
                pair_coverage, pair_verdict, pair_disposition = "complete", "pass", "keep"
            else:
                pair_coverage, pair_verdict, pair_disposition = "partial", "deferred", "needs-source"
            if not matched:
                _record(
                    records,
                    domain="A",
                    case_id=f"shared-entity:{entity_id}:{source}->{target}",
                    source=source,
                    target=target,
                    expected="shared_entity reason for canonical appearance pair",
                    actual="missing shared_entity reason",
                    coverage="partial",
                    verdict="fail",
                    support_fact_ids=support_ids,
                    evidence_ids=evidence_ids,
                    review_ids=review_ids,
                    disposition="derivation-fix",
                )
            else:
                _record(
                    records,
                    domain="A",
                    case_id=f"shared-entity:{entity_id}:{source}->{target}",
                    source=source,
                    target=target,
                    expected="shared_entity reason for canonical appearance pair",
                    actual=f"exact shared_entity reason present; appearance provenance={pair_verdict}",
                    coverage=pair_coverage,
                    verdict=pair_verdict,
                    support_fact_ids=support_ids,
                    evidence_ids=evidence_ids,
                    review_ids=review_ids,
                    disposition=pair_disposition,
                )
    shared_reason_orphans = 0
    for (source, target, entity_id), projected in shared_reason_by_pair_entity.items():
        support_ids = sorted({fact_id for row in projected for fact_id in _split_ids(_key(row, "support_fact_ids"))})
        endpoints = {
            _key(appearance_by_id[fact_id], "work_id")
            for fact_id in support_ids
            if fact_id in appearance_by_id
        }
        if (source, target, entity_id) not in expected_shared_pairs or not {source, target} <= endpoints:
            shared_reason_orphans += 1
            _record(
                records,
                domain="A",
                case_id=f"orphan-shared-reason:{source}->{target}:{entity_id}",
                source=source,
                target=target,
                expected="supporting appearances at both endpoints",
                actual="shared_entity reason has no exact canonical appearance pair",
                coverage="partial",
                verdict="fail",
                support_fact_ids=support_ids,
                disposition="derivation-fix",
            )
    for relation in entity_relation_rows:
        if _key(relation, "relation_kind") == "variant_of":
            _record(
                records,
                domain="A",
                case_id=f"variant-boundary:{_key(relation, 'entity_relation_id')}",
                expected="variant identities remain distinct unless identity_of is audited",
                actual="variant_of relation retained as a non-identity boundary",
                coverage="partial",
                verdict="deferred",
                support_fact_ids=[_key(relation, "entity_relation_id")],
                disposition="defer",
            )

    # E — transition lineage, participants, and conservative pair derivation.
    event_by_id = events
    occurrence_by_event: dict[str, list[dict[str, str]]] = defaultdict(list)
    for occurrence in occurrence_rows:
        occurrence_by_event[_key(occurrence, "event_id")].append(occurrence)
    participant_by_transition: dict[str, list[dict[str, str]]] = defaultdict(list)
    for participant in transition_participant_rows:
        participant_by_transition[_key(participant, "transition_id")].append(participant)
    transition_by_id = transitions
    unsupported_pair_edges = 0
    transition_reason_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for reason in transition_reason_rows:
        transition_reason_by_id[_key(reason, "transition_id")].append(reason)
        pair = (_key(reason, "source_work_id"), _key(reason, "target_work_id"))
        if pair not in base_reason_pairs:
            unsupported_pair_edges += 1
            _record(
                records,
                domain="E",
                case_id=f"transition-unsupported-pair:{_key(reason, 'reason_id')}",
                source=pair[0],
                target=pair[1],
                expected="transition enriches an independently supported work pair",
                actual="transition reason has no base pair support",
                coverage="partial",
                verdict="fail",
                support_fact_ids=_split_ids(_key(reason, "support_fact_ids")),
                disposition="derivation-fix",
            )
    for transition_id, transition in transition_by_id.items():
        event = event_by_id.get(transition_id)
        structural = []
        if event is None:
            structural.append("transition_id does not resolve to an event")
        elif _key(event, "event_kind") != "multiverse_transition":
            structural.append("event kind is not multiverse_transition")
        if not occurrence_by_event.get(transition_id):
            structural.append("no active event occurrence")
        for participant in participant_by_transition.get(transition_id, []):
            if _key(participant, "entity_id") not in entities:
                structural.append(f"unknown participant entity: {_key(participant, 'entity_id')}")
        projected = transition_reason_by_id.get(transition_id, [])
        if structural:
            _record(
                records,
                domain="E",
                case_id=transition_id,
                expected="valid event→occurrence→transition lineage",
                actual="; ".join(structural),
                coverage="partial",
                verdict="fail",
                support_fact_ids=[transition_id],
                disposition="canonical-fix",
            )
        elif projected:
            _record(
                records,
                domain="E",
                case_id=transition_id,
                expected="transition lineage and conservative pair enrichment",
                actual=f"{len(projected)} transition reason(s) with base support",
                coverage="complete",
                verdict="pass",
                support_fact_ids=[transition_id],
                disposition="keep",
            )
        else:
            _record(
                records,
                domain="E",
                case_id=transition_id,
                expected="transition remains queryable without invented work pair",
                actual="no independently supported pair was materialized",
                coverage="not_materialized",
                verdict="deferred",
                support_fact_ids=[transition_id],
                disposition="defer",
            )

    # C — chronology is a separate semantic/display layer.
    if not chronology_rows:
        _record(
            records,
            domain="C",
            case_id="chronology:not-materialized",
            expected="chronology assertions are independently registered before display",
            actual="chronology_assertions.csv is empty",
            coverage="not_materialized",
            verdict="deferred",
            disposition="defer",
        )
    else:
        continuity_ids = {_key(row, "continuity_id") for row in continuity_rows}
        for chronology in chronology_rows:
            chronology_id = _key(chronology, "chronology_assertion_id")
            source, target = _key(chronology, "earlier_work_id"), _key(chronology, "later_work_id")
            structural = []
            if source == target and source:
                structural.append("self-loop")
            if source not in works or target not in works:
                structural.append("unknown chronology endpoint")
            if _key(chronology, "continuity_id") and _key(chronology, "continuity_id") not in continuity_ids:
                structural.append("unknown continuity")
            coverage, verdict, _, evidence_ids, review_ids, disposition = _audit_provenance(
                chronology,
                fact_table="chronology_assertions.csv",
                fact_id=chronology_id,
                evidence_by_fact=evidence_by_fact,
                reviews_by_fact=reviews_by_fact,
            )
            if structural:
                coverage, verdict, disposition = "partial", "fail", "canonical-fix"
            _record(
                records,
                domain="C",
                case_id=chronology_id,
                source=source,
                target=target,
                expected="independent earlier→later chronology assertion",
                actual="; ".join(structural) if structural else "chronology assertion remains separate from graph edges",
                coverage=coverage,
                verdict=verdict,
                support_fact_ids=[chronology_id],
                evidence_ids=evidence_ids,
                review_ids=review_ids,
                disposition=disposition,
            )

    # P — exported pair/reason identity and static viewer boundaries.
    pair_mismatches = len(actual_pairs ^ payload_pairs) if edge_rows and payload_edges else 0
    reason_orphans = relation_orphans + shared_reason_orphans
    payload_node_ids = {
        _key(row, "work_id")
        for row in flowchart.get("nodes", [])
        if isinstance(row, Mapping) and _key(row, "work_id")
    }
    if flowchart.get("nodes"):
        if payload_node_ids != set(works):
            _record(
                records,
                domain="P",
                case_id="export:nodes",
                expected=f"one exported node per canonical work ({len(works)})",
                actual=f"exported={len(payload_node_ids)}, canonical={len(works)}",
                coverage="partial",
                verdict="fail",
                disposition="derivation-fix",
            )
    payload_reason_ids = {
        _key(row, "reason_id")
        for row in payload_reasons
        if _key(row, "reason_id")
    }
    for edge in payload_edges:
        edge_id = _key(edge, "edge_id")
        reason_ids = edge.get("reason_ids", [])
        if isinstance(reason_ids, str):
            reason_ids = _split_ids(reason_ids)
        source, target = _key(edge, "source_work_id"), _key(edge, "target_work_id")
        edge_reason_rows = [row for row in reason_rows if (_key(row, "source_work_id"), _key(row, "target_work_id")) == (source, target)]
        if not reason_ids or not edge_reason_rows:
            reason_orphans += 1
            _record(
                records,
                domain="P",
                case_id=f"export:edge-support:{edge_id}",
                source=source,
                target=target,
                expected="every exported edge has at least one same-pair reason",
                actual="edge has no reason IDs or no same-pair reason rows",
                coverage="partial",
                verdict="fail",
                disposition="derivation-fix",
            )
        missing = sorted(set(str(value) for value in reason_ids) - payload_reason_ids)
        if missing:
            reason_orphans += 1
            _record(
                records,
                domain="P",
                case_id=f"export:edge-reasons:{edge_id}",
                expected="every exported edge reason ID resolves to flowchart reasons",
                actual=f"missing reason IDs: {','.join(missing)}",
                coverage="partial",
                verdict="fail",
                disposition="derivation-fix",
            )
        reason_ids_by_pair = {
            _key(row, "reason_id")
            for row in edge_reason_rows
            if _key(row, "reason_id")
        }
        unknown_pair_reasons = sorted(set(str(value) for value in reason_ids) - reason_ids_by_pair)
        if unknown_pair_reasons:
            reason_orphans += 1
            _record(
                records,
                domain="P",
                case_id=f"export:edge-pair-reasons:{edge_id}",
                source=source,
                target=target,
                expected="exported edge reason IDs belong to its endpoint pair",
                actual=f"wrong-pair reason IDs: {','.join(unknown_pair_reasons)}",
                coverage="partial",
                verdict="fail",
                disposition="derivation-fix",
            )
    forbidden_reason_kinds = {"release", "production_status", "chronology", "prewatch"}
    forbidden = [
        _key(row, "reason_kind")
        for row in reason_rows + payload_reasons
        if _key(row, "reason_kind") in forbidden_reason_kinds
    ]
    if forbidden:
        _record(
            records,
            domain="P",
            case_id="export:forbidden-reason-kind",
            expected="release/status/chronology/prewatch rows remain outside semantic graph",
            actual=f"forbidden kinds: {','.join(sorted(set(forbidden)))}",
            coverage="partial",
            verdict="fail",
            disposition="derivation-fix",
        )
    if html:
        match = re.search(r'<select[^>]+id="chartConnectionTier"[^>]*>(.*?)</select>', html, flags=re.DOTALL)
        values = re.findall(r'<option\s+value="([^"]+)"', match.group(1)) if match else []
        if values != ["site-proposal", "complete"]:
            _record(
                records,
                domain="P",
                case_id="viewer:public-tiers",
                expected="public chart tiers are site-proposal and complete",
                actual=str(values),
                coverage="partial",
                verdict="fail",
                disposition="presentation-only",
            )
        if 'data-relationship-edges="off"' not in html or "data-release-work-id" not in html:
            _record(
                records,
                domain="P",
                case_id="viewer:publication-order-boundary",
                expected="publication order is card/date-axis view without relationship edges",
                actual="release edge guard or card marker missing",
                coverage="partial",
                verdict="fail",
                disposition="presentation-only",
            )

    degree = Counter()
    for source, target in actual_pairs:
        degree[source] += 1
        degree[target] += 1
    for work_id in sorted(set(works) - set(degree)):
        _record(
            records,
            domain="P",
            case_id=f"work-degree-0:{work_id}",
            source=work_id,
            expected="absence of a graph edge is explicitly classified, not guessed away",
            actual="zero incoming/outgoing derived edges",
            coverage="not_materialized",
            verdict="deferred",
            disposition="defer",
        )

    # Machine-readable inventories make the "all works/all pairs" boundary
    # auditable without treating the viewer output as semantic truth.
    reasons_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for reason in reason_rows:
        pair = (_key(reason, "source_work_id"), _key(reason, "target_work_id"))
        if pair[0] and pair[1]:
            reasons_by_pair[pair].append(reason)
    edge_inventory: list[dict[str, Any]] = []
    pair_dispositions: dict[tuple[str, str], str] = {}
    for source, target in sorted(actual_pairs):
        matching_edges = [
            row
            for row in edge_rows
            if (_key(row, "source_work_id"), _key(row, "target_work_id")) == (source, target)
        ]
        matching_reasons = sorted(
            reasons_by_pair.get((source, target), []),
            key=lambda row: _key(row, "reason_id"),
        )
        statuses = {
            status
            for reason in matching_reasons
            for status in _split_ids(_key(reason, "verification_statuses"))
        }
        if "conflicted" in statuses:
            disposition = "explicit-conflict"
        elif "legacy_seed" in statuses or not statuses:
            disposition = "needs-source"
        elif statuses <= {"source_verified"}:
            disposition = "retain"
        else:
            disposition = "defer"
        pair_dispositions[(source, target)] = disposition
        edge_inventory.append(
            {
                "source_work_id": source,
                "target_work_id": target,
                "edge_ids": sorted({_key(row, "edge_id") for row in matching_edges if _key(row, "edge_id")}),
                "reason_ids": [_key(row, "reason_id") for row in matching_reasons],
                "reasons": [
                    {
                        "reason_id": _key(reason, "reason_id"),
                        "reason_kind": _key(reason, "reason_kind"),
                        "support_fact_ids": _split_ids(_key(reason, "support_fact_ids")),
                        "participant_fact_ids": _split_ids(_key(reason, "participant_fact_ids")),
                        "verification_statuses": _split_ids(_key(reason, "verification_statuses")),
                        "certainty_values": _split_ids(_key(reason, "certainty_values")),
                    }
                    for reason in matching_reasons
                ],
                "disposition": disposition,
            }
        )
    work_inventory: list[dict[str, Any]] = []
    for work_id in sorted(works):
        incoming = sorted(source for source, target in actual_pairs if target == work_id)
        outgoing = sorted(target for source, target in actual_pairs if source == work_id)
        incident_pairs = [
            pair for pair in actual_pairs if work_id in pair
        ]
        reason_kinds = sorted(
            {
                reason["reason_kind"]
                for pair in incident_pairs
                for reason in reasons_by_pair.get(pair, [])
                if reason.get("reason_kind")
            }
        )
        dispositions = [pair_dispositions[pair] for pair in incident_pairs]
        if not dispositions:
            disposition = "defer"
        elif "explicit-conflict" in dispositions:
            disposition = "explicit-conflict"
        elif "needs-source" in dispositions:
            disposition = "needs-source"
        elif all(item == "retain" for item in dispositions):
            disposition = "retain"
        else:
            disposition = "defer"
        work_inventory.append(
            {
                "work_id": work_id,
                "incoming_work_ids": incoming,
                "outgoing_work_ids": outgoing,
                "degree": len(set(incoming) | set(outgoing)),
                "reason_kinds": reason_kinds,
                "disposition": disposition,
            }
        )

    return {
        "counts": {
            "works": len(works),
            "edges": len(actual_pairs),
            "reasons": len(reason_rows),
            "relations": len(relation_rows),
            "appearances": len(appearance_rows),
            "transitions": len(transition_rows),
            "chronology_assertions": len(chronology_rows),
            "continuity_memberships": len(continuity_rows),
        },
        "records": records,
        "edge_inventory": edge_inventory,
        "work_inventory": work_inventory,
        "summary": _summary(
            records,
            projection={"edge_pair_mismatches": pair_mismatches, "reason_orphans": reason_orphans},
            transition={"unsupported_pair_edges": unsupported_pair_edges},
        ),
    }


def audit_repository(root: Path) -> dict[str, Any]:
    """Run the independent audit against a repository checkout."""
    root = Path(root)
    tables = _load_repository_tables(root)
    derived, flowchart, html = _load_repository_derived(root)
    report = audit_inputs(tables, derived, html=html, flowchart=flowchart)
    try:
        import subprocess

        report["baseline_sha"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        report["baseline_sha"] = ""
    canonical_bytes = []
    for path in sorted((root / "data" / "library").glob("*.csv")):
        canonical_bytes.append(path.read_bytes())
    report["canonical_sha256"] = hashlib.sha256(b"\0".join(canonical_bytes)).hexdigest()
    return report


def _markdown(report: Mapping[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Marvel connectivity audit",
        "",
        f"Baseline: `{report.get('baseline_sha', '')}`",
        "",
        f"Counts: `{json.dumps(report['counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        f"Verdicts: `{json.dumps(summary['verdicts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "| domain | case | verdict | coverage | disposition |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["records"]:
        lines.append(
            f"| {row['domain']} | `{row['case_id']}` | {row['verdict']} | {row['coverage']} | {row['disposition']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    report = audit_repository(args.root)
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if report["summary"]["verdicts"].get("fail", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
