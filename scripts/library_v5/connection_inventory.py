"""Normalize the independent connectivity audit into a complete inventory.

The inventory is deliberately read-only.  It consumes the independent
``connectivity_audit`` report and adds explicit coverage checks for every
canonical work, derived edge pair, and derived reason ID.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .connectivity_audit import audit_repository


ALLOWED_DISPOSITIONS = {"retain", "needs-source", "explicit-conflict", "defer"}


def _read_ids(path: Path, field: str) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            (row.get(field) or "").strip()
            for row in csv.DictReader(handle)
            if (row.get(field) or "").strip()
        ]


def _read_pairs(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        pairs = []
        for row in csv.DictReader(handle):
            source = (row.get("source_work_id") or "").strip()
            target = (row.get("target_work_id") or "").strip()
            if source and target:
                pairs.append((source, target))
        return pairs


def _split_ids(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return sorted({str(item).strip() for item in value if str(item).strip()})
    return sorted({part.strip() for part in str(value or "").split("|") if part.strip()})


def _read_provenance(
    *, value_field: str, path: Path
) -> dict[tuple[str, str], list[str]]:
    """Read evidence/review links keyed by the canonical fact identity.

    A fact is identified by ``(fact_table, fact_id)``.  Keying only by the ID
    would allow an event and a transition with the same textual ID to borrow
    one another's evidence.
    """

    result: dict[tuple[str, str], list[str]] = {}
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            fact_table = (row.get("fact_table") or "").strip()
            fact_id = (row.get("fact_id") or "").strip()
            value = (row.get(value_field) or "").strip()
            if fact_table and fact_id and value:
                result.setdefault((fact_table, fact_id), []).append(value)
    return {key: sorted(set(values)) for key, values in result.items()}


def _read_fact_index(root: Path) -> dict[str, list[dict[str, str]]]:
    """Index canonical facts by ID while retaining their source table.

    The index intentionally excludes evidence/sources: those are provenance
    registries, not support facts.  Multiple rows/tables may share an ID, so
    the value is a list rather than a single record.
    """

    result: dict[str, list[dict[str, str]]] = {}
    library = root / "data" / "library"
    if not library.exists():
        return result
    for path in sorted(library.glob("*.csv")):
        if path.name in {"evidence.csv", "sources.csv"}:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            id_fields = [field for field in fieldnames if field.endswith("_id")]
            if not id_fields:
                continue
            id_field = id_fields[0]
            for row in reader:
                fact_id = (row.get(id_field) or "").strip()
                if not fact_id:
                    continue
                result.setdefault(fact_id, []).append(
                    {
                        "fact_table": path.name,
                        "fact_id": fact_id,
                        "verification_status": (row.get("verification_status") or "").strip(),
                        "certainty": (row.get("certainty") or row.get("direction_certainty") or "").strip(),
                    }
                )
    return result


def _source_facts(
    fact_ids: list[str],
    *,
    fact_index: Mapping[str, list[dict[str, str]]],
    evidence_by_fact: Mapping[tuple[str, str], list[str]],
    reviews_by_fact: Mapping[tuple[str, str], list[str]],
) -> list[dict[str, Any]]:
    """Resolve each support fact and attach only its exact provenance."""

    resolved: list[dict[str, Any]] = []
    for fact_id in fact_ids:
        matches = fact_index.get(fact_id, [])
        if not matches:
            resolved.append(
                {
                    "fact_table": "",
                    "fact_id": fact_id,
                    "verification_status": "",
                    "certainty": "",
                    "evidence_ids": [],
                    "review_ids": [],
                }
            )
            continue
        for match in matches:
            key = (match["fact_table"], fact_id)
            resolved.append(
                {
                    **match,
                    "evidence_ids": list(evidence_by_fact.get(key, [])),
                    "review_ids": list(reviews_by_fact.get(key, [])),
                }
            )
    return resolved


def _reason_disposition(reason: Mapping[str, Any]) -> str:
    statuses = set(_split_ids(reason.get("verification_statuses")))
    if "conflicted" in statuses:
        return "explicit-conflict"
    if not statuses or "legacy_seed" in statuses:
        return "needs-source"
    if statuses <= {"source_verified"}:
        return "retain"
    return "defer"


def _validate_disposition(value: str, *, scope: str, identifier: str) -> None:
    if value not in ALLOWED_DISPOSITIONS:
        raise ValueError(
            f"unknown disposition for {scope} {identifier}: {value}"
        )


def build_inventory(report: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the independent connectivity audit into a complete inventory."""

    edge_rows = [dict(row) for row in report.get("edge_inventory", [])]
    work_rows = [dict(row) for row in report.get("work_inventory", [])]
    expected_work_ids = {
        str(value) for value in report.get("_expected_work_ids", []) if str(value)
    }
    expected_reason_ids = {
        str(value) for value in report.get("_expected_reason_ids", []) if str(value)
    }
    expected_edge_pairs = [
        tuple(pair)
        for pair in report.get("_expected_edge_pairs", [])
        if len(pair) == 2 and pair[0] and pair[1]
    ]

    edge_pairs = [
        (str(row.get("source_work_id") or ""), str(row.get("target_work_id") or ""))
        for row in edge_rows
    ]
    duplicate_edge_pairs = sorted(
        f"{source}->{target}"
        for (source, target), count in Counter(edge_pairs).items()
        if count > 1
    )
    actual_edge_pairs = {pair for pair in edge_pairs if all(pair)}

    reasons: list[dict[str, Any]] = []
    normalized_edges: list[dict[str, Any]] = []
    reason_ids_seen: list[str] = []
    fact_index = report.get("_fact_index") or {}
    evidence_by_fact = report.get("_evidence_by_fact") or {}
    reviews_by_fact = report.get("_reviews_by_fact") or {}
    for edge in edge_rows:
        source = str(edge.get("source_work_id") or "")
        target = str(edge.get("target_work_id") or "")
        edge_disposition = str(edge.get("disposition") or "defer")
        _validate_disposition(
            edge_disposition,
            scope="edge",
            identifier=f"{source}->{target}",
        )
        normalized_edge = dict(edge)
        normalized_edge["reasons"] = []
        for reason in edge.get("reasons") or []:
            normalized = dict(reason)
            reason_id = str(normalized.get("reason_id") or "")
            if reason_id:
                reason_ids_seen.append(reason_id)
            normalized["source_work_id"] = source
            normalized["target_work_id"] = target
            normalized["source_fact_ids"] = _split_ids(
                normalized.get("support_fact_ids")
            )
            normalized["source_facts"] = _source_facts(
                normalized["source_fact_ids"],
                fact_index=fact_index,
                evidence_by_fact=evidence_by_fact,
                reviews_by_fact=reviews_by_fact,
            )
            normalized["source_fact_table"] = sorted(
                {
                    str(fact.get("fact_table") or "")
                    for fact in normalized["source_facts"]
                    if fact.get("fact_table")
                }
            )
            normalized["evidence_ids"] = sorted(
                {
                    evidence_id
                    for fact in normalized["source_facts"]
                    for evidence_id in fact.get("evidence_ids", [])
                }
            )
            normalized["review_ids"] = sorted(
                {
                    review_id
                    for fact in normalized["source_facts"]
                    for review_id in fact.get("review_ids", [])
                }
            )
            normalized["disposition"] = _reason_disposition(normalized)
            _validate_disposition(
                normalized["disposition"],
                scope="reason",
                identifier=reason_id or f"{source}->{target}",
            )
            reasons.append(normalized)
            normalized_edge["reasons"].append(normalized)
        normalized_edges.append(normalized_edge)

    work_ids_seen = [str(row.get("work_id") or "") for row in work_rows]
    for row in work_rows:
        work_id = str(row.get("work_id") or "")
        _validate_disposition(
            str(row.get("disposition") or "defer"),
            scope="work",
            identifier=work_id,
        )

    reason_counter = Counter(reason_ids_seen)
    work_counter = Counter(work_ids_seen)
    expected_edge_counter = Counter(expected_edge_pairs)
    actual_edge_counter = Counter(actual_edge_pairs)

    missing_reason_ids = sorted(expected_reason_ids - set(reason_ids_seen))
    duplicate_reason_ids = sorted(
        reason_id for reason_id, count in reason_counter.items() if count > 1
    )
    missing_work_ids = sorted(expected_work_ids - set(work_ids_seen))
    duplicate_work_ids = sorted(
        work_id for work_id, count in work_counter.items() if count > 1
    )
    missing_edge_pairs = sorted(
        f"{source}->{target}"
        for (source, target), count in expected_edge_counter.items()
        if count > actual_edge_counter[(source, target)]
    )

    verified_reason_missing_evidence_ids = sorted(
        reason_id
        for reason_id, reason in ((row.get("reason_id"), row) for row in reasons)
        if "source_verified" in _split_ids(reason.get("verification_statuses"))
        and not reason.get("evidence_ids")
    )
    verified_reason_missing_review_ids = sorted(
        reason_id
        for reason_id, reason in ((row.get("reason_id"), row) for row in reasons)
        if "source_verified" in _split_ids(reason.get("verification_statuses"))
        and not reason.get("review_ids")
    )
    unresolved_source_fact_ids = sorted(
        {
            str(fact.get("fact_id") or "")
            for reason in reasons
            for fact in reason.get("source_facts", [])
            if fact.get("fact_id") and not fact.get("fact_table")
        }
    )
    verified_support_fact_missing_evidence = sorted(
        f"{fact.get('fact_table')}:{fact.get('fact_id')}"
        for reason in reasons
        for fact in reason.get("source_facts", [])
        if fact.get("verification_status") == "source_verified"
        and not fact.get("evidence_ids")
    )
    verified_support_fact_missing_review = sorted(
        f"{fact.get('fact_table')}:{fact.get('fact_id')}"
        for reason in reasons
        for fact in reason.get("source_facts", [])
        if fact.get("verification_status") == "source_verified"
        and not fact.get("review_ids")
    )

    summary = report.get("summary") or {}
    projection = summary.get("projection") or {}
    transition = summary.get("transition") or {}
    coverage = {
        "missing_work_ids": missing_work_ids,
        "duplicate_work_ids": duplicate_work_ids,
        "missing_edge_pairs": missing_edge_pairs,
        "duplicate_edge_pairs": duplicate_edge_pairs,
        "source_duplicate_edge_pairs": sorted(
            f"{source}->{target}"
            for (source, target), count in expected_edge_counter.items()
            if count > 1
        ),
        "missing_reason_ids": missing_reason_ids,
        "duplicate_reason_ids": duplicate_reason_ids,
        "structural_failures": int((summary.get("verdicts") or {}).get("fail", 0)),
        "projection_mismatches": int(projection.get("edge_pair_mismatches", 0)),
        "reason_orphans": int(projection.get("reason_orphans", 0)),
        "unsupported_transition_edges": int(
            transition.get("unsupported_pair_edges", 0)
        ),
        "verified_reason_missing_evidence_ids": verified_reason_missing_evidence_ids,
        "verified_reason_missing_review_ids": verified_reason_missing_review_ids,
        "unresolved_source_fact_ids": unresolved_source_fact_ids,
        "verified_support_fact_missing_evidence": verified_support_fact_missing_evidence,
        "verified_support_fact_missing_review": verified_support_fact_missing_review,
    }
    disposition_counts = {
        scope: dict(
            sorted(
                Counter(str(row.get("disposition") or "defer") for row in rows).items()
            )
        )
        for scope, rows in {
            "edges": edge_rows,
            "works": work_rows,
            "reasons": reasons,
        }.items()
    }
    zero_degree_works = sorted(
        str(row.get("work_id") or "")
        for row in work_rows
        if int(row.get("degree") or 0) == 0
    )
    return {
        "baseline_sha": str(report.get("baseline_sha") or ""),
        "canonical_sha256": str(report.get("canonical_sha256") or ""),
        "counts": dict(report.get("counts") or {}),
        "coverage": coverage,
        "dispositions": disposition_counts,
        "zero_degree_works": zero_degree_works,
        "works": sorted(work_rows, key=lambda row: str(row.get("work_id") or "")),
        "edges": sorted(
            normalized_edges,
            key=lambda row: (
                str(row.get("source_work_id") or ""),
                str(row.get("target_work_id") or ""),
            ),
        ),
        "reasons": sorted(reasons, key=lambda row: str(row.get("reason_id") or "")),
    }


def audit_inventory(root: Path, *, baseline_sha: str | None = None) -> dict[str, Any]:
    """Run the independent audit and add canonical/export ID expectations."""

    root = Path(root)
    report = dict(audit_repository(root))
    if baseline_sha:
        report["baseline_sha"] = baseline_sha
    required_inputs = [
        root / "data" / "library" / "works.csv",
        root / "data" / "derived" / "work_edges_all.csv",
        root / "data" / "derived" / "work_pair_reasons.csv",
        root / "data" / "derived" / "flowchart.json",
    ]
    report["_missing_inputs"] = [str(path) for path in required_inputs if not path.exists()]
    report["_expected_work_ids"] = _read_ids(root / "data" / "library" / "works.csv", "work_id")
    report["_expected_reason_ids"] = _read_ids(
        root / "data" / "derived" / "work_pair_reasons.csv", "reason_id"
    )
    report["_expected_edge_pairs"] = _read_pairs(
        root / "data" / "derived" / "work_edges_all.csv"
    )
    report["_evidence_by_fact"] = _read_provenance(
        value_field="evidence_id",
        path=root / "data" / "library" / "evidence.csv",
    )
    report["_reviews_by_fact"] = _read_provenance(
        value_field="review_id",
        path=root / "data" / "content_audit" / "reviews.csv",
    )
    report["_fact_index"] = _read_fact_index(root)
    inventory = build_inventory(report)
    inventory["coverage"]["missing_inputs"] = report["_missing_inputs"]
    flowchart_path = root / "data" / "derived" / "flowchart.json"
    if flowchart_path.exists():
        flowchart = json.loads(flowchart_path.read_text(encoding="utf-8"))
        expected_reason_ids = set(report["_expected_reason_ids"])
        payload_reason_ids = {
            str(row.get("reason_id"))
            for row in flowchart.get("reasons", [])
            if row.get("reason_id")
        }
        expected_edge_pairs = set(report["_expected_edge_pairs"])
        payload_edge_pairs = {
            (str(row.get("source_work_id")), str(row.get("target_work_id")))
            for row in flowchart.get("edges", [])
            if row.get("source_work_id") and row.get("target_work_id")
        }
        expected_work_ids = set(report["_expected_work_ids"])
        payload_work_ids = {
            str(row.get("work_id"))
            for row in flowchart.get("nodes", [])
            if row.get("work_id")
        }
        inventory["coverage"].update(
            {
                "payload_missing_work_ids": sorted(expected_work_ids - payload_work_ids),
                "payload_extra_work_ids": sorted(payload_work_ids - expected_work_ids),
                "payload_missing_edge_pairs": sorted(
                    f"{source}->{target}"
                    for source, target in expected_edge_pairs - payload_edge_pairs
                ),
                "payload_extra_edge_pairs": sorted(
                    f"{source}->{target}"
                    for source, target in payload_edge_pairs - expected_edge_pairs
                ),
                "payload_missing_reason_ids": sorted(expected_reason_ids - payload_reason_ids),
                "payload_extra_reason_ids": sorted(payload_reason_ids - expected_reason_ids),
            }
        )
    else:
        inventory["coverage"].update(
            {
                "payload_missing_work_ids": [],
                "payload_extra_work_ids": [],
                "payload_missing_edge_pairs": [],
                "payload_extra_edge_pairs": [],
                "payload_missing_reason_ids": [],
                "payload_extra_reason_ids": [],
            }
        )
    return inventory


def render_markdown(inventory: Mapping[str, Any]) -> str:
    """Render a complete human-readable inventory without semantic edits."""

    lines = [
        "# Marvel connection/reason inventory",
        "",
        "## Boundary",
        "",
        "This is a read-only inventory of the current derived graph. It does not promote, delete, or rewrite canonical facts.",
        "",
        f"- Baseline: `{inventory.get('baseline_sha', '')}`",
        f"- Canonical input hash: `{inventory.get('canonical_sha256', '')}`",
        f"- Counts: `{json.dumps(inventory.get('counts', {}), ensure_ascii=False, sort_keys=True)}`",
        "- `needs-source`, `explicit-conflict`, and `defer` are audit dispositions, not mutation requests.",
        "",
        "## Coverage",
        "",
        f"```json\n{json.dumps(inventory.get('coverage', {}), ensure_ascii=False, indent=2, sort_keys=True)}\n```",
        "",
        "## Disposition counts",
        "",
        f"```json\n{json.dumps(inventory.get('dispositions', {}), ensure_ascii=False, indent=2, sort_keys=True)}\n```",
        "",
        "## Zero-degree works",
        "",
        *[f"- `{work_id}`" for work_id in inventory.get("zero_degree_works", [])],
        "",
        "## All works",
        "",
        "| work_id | degree | incoming | outgoing | reason kinds | disposition |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for work in inventory.get("works", []):
        lines.append(
            "| `{work_id}` | {degree} | `{incoming}` | `{outgoing}` | `{kinds}` | {disposition} |".format(
                work_id=work.get("work_id", ""),
                degree=work.get("degree", 0),
                incoming=", ".join(work.get("incoming_work_ids", [])),
                outgoing=", ".join(work.get("outgoing_work_ids", [])),
                kinds=", ".join(work.get("reason_kinds", [])),
                disposition=work.get("disposition", ""),
            )
        )
    lines.extend(
        [
            "",
            "## All derived edge pairs and reasons",
            "",
            "| source | target | edge IDs | reason IDs | reason kinds | fact tables | fact IDs | evidence | reviews | statuses | disposition |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for edge in inventory.get("edges", []):
        reasons = edge.get("reasons", [])
        lines.append(
            "| `{source}` | `{target}` | `{edges}` | `{reasons}` | `{kinds}` | `{tables}` | `{facts}` | `{evidence}` | `{reviews}` | `{statuses}` | {disposition} |".format(
                source=edge.get("source_work_id", ""),
                target=edge.get("target_work_id", ""),
                edges=", ".join(edge.get("edge_ids", [])),
                reasons=", ".join(edge.get("reason_ids", [])),
                kinds=", ".join(sorted({str(row.get('reason_kind') or '') for row in reasons})),
                tables=", ".join(
                    sorted(
                        {
                            table
                            for row in reasons
                            for table in row.get("source_fact_table", [])
                        }
                    )
                ),
                facts=", ".join(
                    sorted(
                        {
                            fact_id
                            for row in reasons
                            for fact_id in _split_ids(row.get("support_fact_ids"))
                        }
                    )
                ),
                evidence=", ".join(
                    sorted(
                        {
                            evidence_id
                            for row in reasons
                            for evidence_id in row.get("evidence_ids", [])
                        }
                    )
                ),
                reviews=", ".join(
                    sorted(
                        {
                            review_id
                            for row in reasons
                            for review_id in row.get("review_ids", [])
                        }
                    )
                ),
                statuses=", ".join(
                    sorted(
                        {
                            status
                            for row in reasons
                            for status in _split_ids(row.get("verification_statuses"))
                        }
                    )
                ),
                disposition=edge.get("disposition", ""),
            )
        )
    lines.extend(
        [
            "",
            "## All reasons with exact fact provenance",
            "",
            "The edge table above is an aggregate summary. This table is one row per reason; `source_facts` preserves the exact `(fact_table, fact_id) -> evidence/review` mapping.",
            "",
            "| reason_id | source | target | kind | source_facts | statuses | disposition |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for reason in inventory.get("reasons", []):
        source_facts = [
            {
                "fact_table": fact.get("fact_table", ""),
                "fact_id": fact.get("fact_id", ""),
                "verification_status": fact.get("verification_status", ""),
                "certainty": fact.get("certainty", ""),
                "evidence_ids": fact.get("evidence_ids", []),
                "review_ids": fact.get("review_ids", []),
            }
            for fact in reason.get("source_facts", [])
        ]
        lines.append(
            "| `{reason_id}` | `{source}` | `{target}` | `{kind}` | `{facts}` | `{statuses}` | {disposition} |".format(
                reason_id=reason.get("reason_id", ""),
                source=reason.get("source_work_id", ""),
                target=reason.get("target_work_id", ""),
                kind=reason.get("reason_kind", ""),
                facts=json.dumps(source_facts, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                statuses=", ".join(_split_ids(reason.get("verification_statuses"))),
                disposition=reason.get("disposition", ""),
            )
        )
    return "\n".join(lines) + "\n"


def _has_failures(inventory: Mapping[str, Any]) -> bool:
    coverage = inventory.get("coverage") or {}
    return any(
        coverage.get(field)
        for field in (
            "missing_inputs",
            "missing_work_ids",
            "duplicate_work_ids",
            "missing_edge_pairs",
            "duplicate_edge_pairs",
            "source_duplicate_edge_pairs",
            "missing_reason_ids",
            "duplicate_reason_ids",
            "structural_failures",
            "projection_mismatches",
            "reason_orphans",
            "unsupported_transition_edges",
            "verified_reason_missing_evidence_ids",
            "verified_reason_missing_review_ids",
            "payload_missing_work_ids",
            "payload_extra_work_ids",
            "payload_missing_edge_pairs",
            "payload_extra_edge_pairs",
            "payload_missing_reason_ids",
            "payload_extra_reason_ids",
            "unresolved_source_fact_ids",
            "verified_support_fact_missing_evidence",
            "verified_support_fact_missing_review",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--baseline-sha")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    inventory = audit_inventory(args.root, baseline_sha=args.baseline_sha)
    payload = json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.write_text(payload, encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(render_markdown(inventory), encoding="utf-8")
    print(json.dumps({"counts": inventory["counts"], "coverage": inventory["coverage"]}, ensure_ascii=False, sort_keys=True))
    return 1 if _has_failures(inventory) else 0


if __name__ == "__main__":
    raise SystemExit(main())
