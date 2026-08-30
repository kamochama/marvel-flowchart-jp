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
)


def _read_rows(root: Path, relative: str) -> list[dict[str, str]]:
    with (root / relative).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _evidence_index(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        index.setdefault(row["fact_id"], []).append(row)
    return index


def _review_index(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        index.setdefault(row["fact_id"], []).append(row)
    return index


def build_inventory(root: Path) -> list[dict[str, str]]:
    """Return one deterministic inventory row for every normalized fact."""

    evidence = _evidence_index(_read_rows(root, "data/library/evidence.csv"))
    reviews = _review_index(_read_rows(root, "data/content_audit/reviews.csv"))
    facts: list[dict[str, str]] = []
    table_specs = (
        ("releases.csv", "release_id"),
        ("production_status_assertions.csv", "production_status_assertion_id"),
    )
    for table_name, id_column in table_specs:
        for source_row in _read_rows(root, f"data/library/{table_name}"):
            fact_id = source_row[id_column]
            fact_evidence = evidence.get(fact_id, [])
            fact_reviews = reviews.get(fact_id, [])
            source_ids = sorted(
                {row["source_id"] for row in fact_evidence if row.get("source_id")}
            )
            verified = source_row["verification_status"] == "source_verified"
            facts.append(
                {
                    "fact_id": fact_id,
                    "fact_table": table_name,
                    "work_id": source_row["work_id"],
                    "verification_status": source_row["verification_status"],
                    "source_candidates": ";".join(source_ids),
                    "evidence_count": str(len(fact_evidence)),
                    "review_count": str(len(fact_reviews)),
                    "disposition": "verified" if verified else "defer",
                }
            )
    return sorted(facts, key=lambda row: (row["fact_table"], row["fact_id"]))


def write_inventory(rows: Iterable[dict[str, str]], output: Path) -> None:
    """Write inventory rows as a stable UTF-8 CSV."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_markdown_report(rows: Iterable[dict[str, str]], output: Path) -> None:
    """Write a compact human-auditable Markdown report for the inventory."""

    materialized = list(rows)
    release_count = sum(row["fact_table"] == "releases.csv" for row in materialized)
    status_count = sum(
        row["fact_table"] == "production_status_assertions.csv" for row in materialized
    )
    verified_count = sum(row["disposition"] == "verified" for row in materialized)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# 全作品 release/status fact inventory\n\n")
        handle.write(
            f"- release facts: {release_count}\n"
            f"- production-status facts: {status_count}\n"
            f"- verified dispositions: {verified_count}\n"
            f"- deferred dispositions: {len(materialized) - verified_count}\n\n"
        )
        handle.write(
            "| fact_id | fact_table | work_id | verification_status | "
            "source_candidates | evidence_count | review_count | disposition |\n"
        )
        handle.write("|---|---|---|---|---|---:|---:|---|\n")
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

