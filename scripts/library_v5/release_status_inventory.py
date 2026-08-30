"""Build a deterministic inventory for normalized release/status facts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


FIELDS = (
    "fact_id",
    "fact_table",
    "work_id",
    "verification_status",
    "source_candidates",
    "evidence_count",
    "review_count",
    "disposition",
    "disposition_reason",
    "next_action",
)

CONFLICT_FACT_IDS = {
    "release-your-friendly-neighborhood-spider-man-s2-2026-primary",
    "production-status-wonder-man-s2-tba-snapshot-2026-08-28",
}


def _assert_safe_output(output: Path) -> None:
    """Refuse paths that could overwrite canonical inputs or the review ledger."""

    parts = [part.lower() for part in output.resolve().parts]
    for index in range(len(parts) - 1):
        if parts[index : index + 2] == ["data", "library"]:
            raise ValueError(f"inventory output cannot be under data/library: {output}")
    if len(parts) >= 3 and parts[-3:] == ["data", "content_audit", "reviews.csv"]:
        raise ValueError(f"inventory output cannot overwrite reviews.csv: {output}")


def _read_rows(root: Path, relative: str) -> list[dict[str, str]]:
    with (root / relative).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _evidence_index(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        index.setdefault((row["fact_table"], row["fact_id"]), []).append(row)
    return index


def _review_index(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        index.setdefault((row["fact_table"], row["fact_id"]), []).append(row)
    return index


def build_inventory(root: Path) -> list[dict[str, str]]:
    """Return one deterministic inventory row for every normalized fact."""

    evidence = _evidence_index(_read_rows(root, "data/library/evidence.csv"))
    reviews = _review_index(_read_rows(root, "data/content_audit/reviews.csv"))
    sources = _read_rows(root, "data/library/sources.csv")
    source_ids_by_url: dict[str, list[str]] = {}
    for source in sources:
        source_ids_by_url.setdefault(source.get("url", "").strip(), []).append(source["source_id"])
    works = {row["work_id"]: row for row in _read_rows(root, "data/library/works.csv")}
    facts: list[dict[str, str]] = []
    table_specs = (
        ("releases.csv", "release_id"),
        ("production_status_assertions.csv", "production_status_assertion_id"),
    )
    for table_name, id_column in table_specs:
        for source_row in _read_rows(root, f"data/library/{table_name}"):
            fact_id = source_row[id_column]
            fact_evidence = evidence.get((table_name, fact_id), [])
            fact_reviews = reviews.get((table_name, fact_id), [])
            source_ids = {
                row["source_id"] for row in fact_evidence if row.get("source_id")
            }
            work = works.get(source_row["work_id"], {})
            for url_field in ("source_url", "title_audit_source_url"):
                url = work.get(url_field, "").strip()
                source_ids.update(source_ids_by_url.get(url, []))
            verified = source_row["verification_status"] == "source_verified"
            if verified:
                disposition = "promote"
                disposition_reason = "direct source-backed fact with qualifying evidence and review"
                next_action = "retain source_verified; recheck when the source changes"
            elif fact_id in CONFLICT_FACT_IDS:
                disposition = "conflict"
                disposition_reason = "registered source conflicts with the migrated fact; no silent rewrite"
                next_action = "resolve conflicting primary sources before any promotion"
            elif source_ids:
                disposition = "defer"
                disposition_reason = "source registration/listing is not fact-level qualifying evidence"
                next_action = "add work-specific primary evidence and a review transition"
            else:
                disposition = "defer"
                disposition_reason = "no qualifying source or fact-level evidence is registered"
                next_action = "register a work-specific primary source, then add evidence and review"
            facts.append(
                {
                    "fact_id": fact_id,
                    "fact_table": table_name,
                    "work_id": source_row["work_id"],
                    "verification_status": source_row["verification_status"],
                    "source_candidates": ";".join(sorted(source_ids)),
                    "evidence_count": str(len(fact_evidence)),
                    "review_count": str(len(fact_reviews)),
                    "disposition": disposition,
                    "disposition_reason": disposition_reason,
                    "next_action": next_action,
                }
            )
    return sorted(facts, key=lambda row: (row["fact_table"], row["fact_id"]))


def write_inventory(rows: Iterable[dict[str, str]], output: Path) -> None:
    """Write inventory rows as a stable UTF-8 CSV."""

    _assert_safe_output(output)
    materialized = sorted(
        rows, key=lambda row: (row.get("fact_table", ""), row.get("fact_id", ""))
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, "") for field in FIELDS} for row in materialized
        )


def write_markdown_report(rows: Iterable[dict[str, str]], output: Path) -> None:
    """Write a compact human-auditable Markdown report for the inventory."""

    materialized = sorted(
        rows, key=lambda row: (row.get("fact_table", ""), row.get("fact_id", ""))
    )
    release_count = sum(row["fact_table"] == "releases.csv" for row in materialized)
    status_count = sum(
        row["fact_table"] == "production_status_assertions.csv" for row in materialized
    )
    verified_count = sum(row["disposition"] == "promote" for row in materialized)
    conflict_count = sum(row["disposition"] == "conflict" for row in materialized)
    _assert_safe_output(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# 全作品 release/status fact inventory\n\n")
        handle.write(
            f"- release facts: {release_count}\n"
            f"- production-status facts: {status_count}\n"
            f"- promote dispositions: {verified_count}\n"
            f"- deferred dispositions: {len(materialized) - verified_count - conflict_count}\n"
            f"- conflict dispositions: {conflict_count}\n\n"
        )
        handle.write(
            "| fact_id | fact_table | work_id | verification_status | "
            "source_candidates | evidence_count | review_count | disposition | "
            "disposition_reason | next_action |\n"
        )
        handle.write("|---|---|---|---|---|---:|---:|---|---|---|\n")
        for row in materialized:
            values = [row.get(field, "").replace("|", "\\|") for field in FIELDS]
            handle.write("| " + " | ".join(values) + " |\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/content_audit/release_status_inventory.csv"),
    )
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    rows = build_inventory(args.repo_root)
    write_inventory(rows, args.output)
    if args.markdown_output is not None:
        write_markdown_report(rows, args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

