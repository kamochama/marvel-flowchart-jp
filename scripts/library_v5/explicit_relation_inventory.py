"""Audit canonical explicit work-to-work relations without mutating inputs.

The audit treats ``(fact_table, fact_id)`` as the provenance identity and
classifies every row in ``work_relations.csv``.  It deliberately does not
promote, rewrite, or regenerate canonical semantic data.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .connectivity_audit import audit_repository


FACT_TABLE = "work_relations.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _split(value: str) -> list[str]:
    return sorted({part.strip() for part in (value or "").split("|") if part.strip()})


def _read_inputs(root: Path) -> tuple[
    list[dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, list[dict[str, str]]],
    dict[str, list[dict[str, str]]],
    list[dict[str, str]],
    list[dict[str, str]],
    set[str],
    dict[str, dict[str, str]],
]:
    library = root / "data" / "library"
    audit = root / "data" / "content_audit"
    relations = _rows(library / FACT_TABLE)
    sources = {row["source_id"]: row for row in _rows(library / "sources.csv") if row.get("source_id")}
    evidence: dict[str, list[dict[str, str]]] = {}
    all_evidence_ids: set[str] = set()
    all_evidence_by_id: dict[str, dict[str, str]] = {}
    for row in _rows(library / "evidence.csv"):
        if row.get("evidence_id"):
            all_evidence_ids.add(row["evidence_id"])
            all_evidence_by_id[row["evidence_id"]] = row
        if row.get("fact_table") == FACT_TABLE and row.get("fact_id"):
            evidence.setdefault(row["fact_id"], []).append(row)
    reviews: dict[str, list[dict[str, str]]] = {}
    for row in _rows(audit / "reviews.csv"):
        if row.get("fact_table") == FACT_TABLE and row.get("fact_id"):
            reviews.setdefault(row["fact_id"], []).append(row)
    reasons = _rows(root / "data" / "derived" / "work_pair_reasons.csv")
    edges = _rows(root / "data" / "derived" / "work_edges_all.csv")
    return relations, sources, evidence, reviews, reasons, edges, all_evidence_ids, all_evidence_by_id


def _disposition(row: dict[str, str], evidence: list[dict[str, str]], reviews: list[dict[str, str]], sources: dict[str, dict[str, str]]) -> tuple[str, list[str]]:
    status = (row.get("verification_status") or "").strip()
    notes = (row.get("notes") or "").lower()
    if status == "superseded":
        return "superseded", []
    if status == "conflicted" or "explicit-conflict" in notes or "conflicted" in notes:
        return "explicit-conflict", []
    source_ids = sorted({(item.get("source_id") or "").strip() for item in evidence if item.get("source_id")})
    missing_source = [source_id for source_id in source_ids if source_id not in sources]
    if status == "source_verified" and evidence and reviews and not missing_source:
        return "retain", source_ids
    if status == "legacy_seed":
        return "needs-source", source_ids
    return "defer", source_ids


def build_inventory(root: Path) -> dict[str, Any]:
    """Build a deterministic, read-only explicit relation inventory."""

    root = Path(root)
    relations, sources, evidence_by_id, reviews_by_id, reasons, edges, all_evidence_ids, all_evidence_by_id = _read_inputs(root)
    relation_ids = [row.get("work_relation_id", "").strip() for row in relations]
    counts = Counter((row.get("verification_status") or "").strip() for row in relations)
    inventory: list[dict[str, Any]] = []
    missing_evidence: list[str] = []
    missing_review: list[str] = []
    missing_source: list[str] = []
    reason_by_relation: dict[str, list[dict[str, str]]] = {}
    for reason in reasons:
        if reason.get("reason_kind") == "explicit_relation" and reason.get("relation_id"):
            reason_by_relation.setdefault(reason["relation_id"], []).append(reason)
    edge_by_pair = {
        (row.get("source_work_id", ""), row.get("target_work_id", "")): row
        for row in edges
    }
    reason_failures = {
        "missing": [],
        "duplicate": [],
        "direction": [],
        "support": [],
        "status": [],
        "certainty": [],
        "edge": [],
        "edge_duplicate": [],
        "notes": [],
        "reason_id": [],
        "orphan": [],
        "extra": [],
        "qualifying_evidence": [],
    }
    relation_id_set = set(relation_ids)
    active_relation_id_set = {
        row.get("work_relation_id", "")
        for row in relations
        if row.get("verification_status") != "superseded"
    }
    all_explicit_reason_ids = {
        reason.get("relation_id", "")
        for reason in reasons
        if reason.get("reason_kind") == "explicit_relation"
    }
    reason_failures["extra"].extend(
        sorted(
            relation_id
            for relation_id in all_explicit_reason_ids
            if relation_id not in active_relation_id_set
        )
    )
    for row in sorted(relations, key=lambda item: item.get("work_relation_id", "")):
        relation_id = (row.get("work_relation_id") or "").strip()
        evidence = sorted(evidence_by_id.get(relation_id, []), key=lambda item: item.get("evidence_id", ""))
        reviews = sorted(reviews_by_id.get(relation_id, []), key=lambda item: item.get("review_id", ""))
        qualifying_evidence = [
            item for item in evidence if item.get("evidence_role") in {"primary", "supporting"}
        ]
        disposition, source_ids = _disposition(row, qualifying_evidence, reviews, sources)
        relation_reasons = reason_by_relation.get(relation_id, [])
        reason_ids = sorted({item.get("reason_id", "") for item in relation_reasons if item.get("reason_id")})
        edge = edge_by_pair.get((row.get("source_work_id", ""), row.get("target_work_id", "")))
        if row.get("verification_status") != "superseded":
            if not relation_reasons:
                reason_failures["missing"].append(relation_id)
            elif len(relation_reasons) != 1:
                reason_failures["duplicate"].append(relation_id)
            else:
                reason = relation_reasons[0]
                if (reason.get("source_work_id"), reason.get("target_work_id")) != (row.get("source_work_id"), row.get("target_work_id")):
                    reason_failures["direction"].append(relation_id)
                if _split(reason.get("support_fact_ids", "")) != [relation_id]:
                    reason_failures["support"].append(relation_id)
                if _split(reason.get("verification_statuses", "")) != [row.get("verification_status", "")]:
                    reason_failures["status"].append(relation_id)
                if _split(reason.get("certainty_values", "")) != [row.get("certainty", "")]:
                    reason_failures["certainty"].append(relation_id)
                expected_notes = "; ".join(
                    [row.get("relation_kind", ""), row.get("relation_scope", ""), row.get("directness", "")]
                )
                if reason.get("notes", "") != expected_notes:
                    reason_failures["notes"].append(relation_id)
                expected_reason_id = (
                    f"reason-{row.get('source_work_id', '')}-{row.get('target_work_id', '')}"
                    f"-explicit-relation-{relation_id}"
                )
                if reason.get("reason_id") != expected_reason_id:
                    reason_failures["reason_id"].append(relation_id)
                edge_reason_ids = _split(edge.get("reason_ids", "")) if edge else []
                if not edge or reason.get("reason_id") not in edge_reason_ids:
                    reason_failures["edge"].append(relation_id)
                if edge and edge_reason_ids.count(reason.get("reason_id", "")) != 1:
                    reason_failures["edge_duplicate"].append(relation_id)
        elif relation_reasons:
            reason_failures["orphan"].append(relation_id)
        review_evidence_ids = sorted({item for review in reviews for item in _split(review.get("evidence_ids", ""))})
        exact_evidence_ids = sorted({item.get("evidence_id", "") for item in evidence if item.get("evidence_id")})
        if set(review_evidence_ids) - all_evidence_ids:
            reason_failures.setdefault("review_missing_evidence", []).append(relation_id)
        if row.get("verification_status") == "source_verified" and not qualifying_evidence:
            reason_failures["qualifying_evidence"].append(relation_id)
        if row.get("verification_status") == "source_verified":
            if not evidence:
                missing_evidence.append(relation_id)
            if not reviews:
                missing_review.append(relation_id)
            if any(source_id not in sources for source_id in source_ids):
                missing_source.append(relation_id)
        inventory.append(
            {
                **row,
                "work_relation_id": relation_id,
                "evidence_ids": sorted({item.get("evidence_id", "") for item in evidence if item.get("evidence_id")}),
                "qualifying_evidence_ids": sorted({item.get("evidence_id", "") for item in qualifying_evidence if item.get("evidence_id")}),
                "review_ids": sorted({item.get("review_id", "") for item in reviews if item.get("review_id")}),
                "source_ids": source_ids,
                "reason_ids": reason_ids,
                "edge_ids": [edge["edge_id"]] if edge and edge.get("edge_id") else [],
                "review_external_evidence_ids": sorted(set(review_evidence_ids) - set(exact_evidence_ids)),
                "external_evidence_details": [
                    {
                        "evidence_id": evidence_id,
                        "fact_table": all_evidence_by_id[evidence_id].get("fact_table", ""),
                        "fact_id": all_evidence_by_id[evidence_id].get("fact_id", ""),
                        "source_id": all_evidence_by_id[evidence_id].get("source_id", ""),
                        "evidence_role": all_evidence_by_id[evidence_id].get("evidence_role", ""),
                    }
                    for evidence_id in sorted(set(review_evidence_ids) - set(exact_evidence_ids))
                    if evidence_id in all_evidence_by_id
                ],
                "source_details": [
                    {
                        "source_id": item.get("source_id", ""),
                        "url": sources.get(item.get("source_id", ""), {}).get("url", ""),
                        "evidence_id": item.get("evidence_id", ""),
                        "evidence_role": item.get("evidence_role", ""),
                        "fact_table": FACT_TABLE,
                        "fact_id": relation_id,
                    }
                    for item in evidence
                    if item.get("source_id") in sources
                ],
                "source_facts": [
                    {
                        "fact_table": FACT_TABLE,
                        "fact_id": relation_id,
                        "evidence_ids": sorted({item.get("evidence_id", "") for item in evidence if item.get("evidence_id")}),
                        "review_ids": sorted({item.get("review_id", "") for item in reviews if item.get("review_id")}),
                    }
                ] if relation_id else [],
                "disposition": disposition,
            }
        )

    duplicate_ids = sorted({relation_id for relation_id in relation_ids if relation_ids.count(relation_id) > 1})
    graph_report = audit_repository(root)
    graph_counts = graph_report["counts"]
    graph_summary = graph_report["summary"]
    coverage = {
        "missing_relation_ids": sorted({relation_id for relation_id in relation_ids if not relation_id}),
        "duplicate_relation_ids": duplicate_ids,
        "source_verified_missing_evidence": sorted(set(missing_evidence)),
        "source_verified_missing_review": sorted(set(missing_review)),
        "source_verified_missing_source": sorted(set(missing_source)),
        "relation_reason_missing": sorted(set(reason_failures["missing"])),
        "relation_reason_duplicate": sorted(set(reason_failures["duplicate"])),
        "relation_reason_direction": sorted(set(reason_failures["direction"])),
        "relation_reason_support": sorted(set(reason_failures["support"])),
        "relation_reason_status": sorted(set(reason_failures["status"])),
        "relation_reason_certainty": sorted(set(reason_failures["certainty"])),
        "relation_reason_edge": sorted(set(reason_failures["edge"])),
        "relation_reason_edge_duplicate": sorted(set(reason_failures["edge_duplicate"])),
        "relation_reason_notes": sorted(set(reason_failures["notes"])),
        "relation_reason_id": sorted(set(reason_failures["reason_id"])),
        "extra_explicit_relation_reasons": sorted(set(reason_failures["extra"])),
        "superseded_reason_orphans": sorted(set(reason_failures["orphan"])),
        "source_verified_missing_qualifying_evidence": sorted(set(reason_failures["qualifying_evidence"])),
        "review_missing_evidence": sorted(set(reason_failures.get("review_missing_evidence", []))),
        "projection_mismatches": graph_summary.get("projection", {}).get("edge_pair_mismatches", 0),
        "reason_orphans": graph_summary.get("projection", {}).get("reason_orphans", 0),
    }
    return {
        "summary": {
            "total": len(relations),
            "active": sum(1 for row in relations if row.get("verification_status") != "superseded"),
            "source_verified": counts.get("source_verified", 0),
            "legacy_seed": counts.get("legacy_seed", 0),
            "superseded": counts.get("superseded", 0),
        },
        "graph": {
            "works": graph_counts.get("works", 0),
            "edges": graph_counts.get("edges", 0),
            "reasons": graph_counts.get("reasons", 0),
        },
        "coverage": coverage,
        "relations": inventory,
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Marvel explicit relation inventory",
        "",
        f"Summary: `{json.dumps(report['summary'], ensure_ascii=False, sort_keys=True)}`",
        f"Graph: `{json.dumps(report['graph'], ensure_ascii=False, sort_keys=True)}`",
        "",
        f"Coverage: `{json.dumps(report['coverage'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "| relation_id | source | target | kind | status | disposition | same-fact evidence | qualifying evidence | external review evidence | reviews | sources |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["relations"]:
        lines.append(
            f"| {row['work_relation_id']} | {row.get('source_work_id', '')} | "
            f"{row.get('target_work_id', '')} | {row.get('relation_kind', '')} | "
            f"{row.get('verification_status', '')} | {row['disposition']} | "
                f"{', '.join(row['evidence_ids']) or '—'} | "
                f"{', '.join(row['qualifying_evidence_ids']) or '—'} | "
                f"{', '.join(row['review_external_evidence_ids']) or '—'} | "
                f"{', '.join(row['review_ids']) or '—'} | "
            f"{', '.join(row['source_ids']) or '—'} |"
        )
    lines.extend(["", "## Needs-source relations", ""])
    lines.extend(f"- `{row['work_relation_id']}`" for row in report["relations"] if row["disposition"] == "needs-source")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    report = build_inventory(args.root)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    failures = [value for value in report["coverage"].values() if value not in (0, [], {})]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
