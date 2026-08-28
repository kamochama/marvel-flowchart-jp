from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


_REVIEW_DATASETS = {
    "connections": "connection_dispositions.csv",
    "entity_seeds": "entity_seed_dispositions.csv",
    "story_paths": "story_path_dispositions.csv",
    "chronology": "chronology_dispositions.csv",
}

# These legacy dispositions either represent facts that still require independent
# source verification, source-derived reconstruction that has not yet happened,
# or an explicit watch item whose current exclusion must remain visible.
_BACKLOG_DISPOSITIONS = {
    "migrated_explicit_relation",
    "migrated_promotion_fact",
    "appearance_derived_pending_audit",
    "rejected_superseded",
    "migrated_appearance_seed",
    "decomposed_entity_return_seed",
    "legacy_display_placement_seed",
}


def summarize_dispositions(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter((row.get("disposition") or "").strip() or "<blank>" for row in rows)
    return dict(sorted(counts.items()))


def summarize_review_rows(
    *,
    connection_rows: list[dict[str, str]],
    entity_rows: list[dict[str, str]],
    story_rows: list[dict[str, str]],
    chronology_rows: list[dict[str, str]],
) -> dict[str, dict[str, int]]:
    result = {
        "connections": summarize_dispositions(connection_rows),
        "entity_seeds": summarize_dispositions(entity_rows),
        "story_paths": summarize_dispositions(story_rows),
        "chronology": summarize_dispositions(chronology_rows),
    }
    backlog = Counter()
    for dataset in (connection_rows, entity_rows, chronology_rows, story_rows):
        for row in dataset:
            disposition = (row.get("disposition") or "").strip()
            if disposition in _BACKLOG_DISPOSITIONS:
                backlog[disposition] += 1
    result["content_audit_backlog"] = dict(sorted(backlog.items()))
    return result


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def review_repository(repo_root: Path) -> dict[str, object]:
    migration = repo_root / "data" / "migration"
    datasets = {
        name: _read_csv(migration / filename)
        for name, filename in _REVIEW_DATASETS.items()
    }
    summaries = summarize_review_rows(
        connection_rows=datasets["connections"],
        entity_rows=datasets["entity_seeds"],
        story_rows=datasets["story_paths"],
        chronology_rows=datasets["chronology"],
    )
    return {
        "schema_version": "5.0",
        "principle": "Disposition counts are review observations, not correctness targets.",
        "row_counts": {name: len(rows) for name, rows in datasets.items()},
        "dispositions": {
            name: summaries[name]
            for name in ("connections", "entity_seeds", "story_paths", "chronology")
        },
        "content_audit_backlog": summaries["content_audit_backlog"],
    }


def write_review_outputs(repo_root: Path) -> dict[str, object]:
    migration = repo_root / "data" / "migration"
    migration.mkdir(parents=True, exist_ok=True)
    review = review_repository(repo_root)

    (migration / "migration_review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Marvel Library v5 Migration Review",
        "",
        "This review inventories migration dispositions. Counts are observations, not correctness targets.",
        "",
        "## Dataset coverage",
        "",
    ]
    for dataset, count in review["row_counts"].items():
        lines.append(f"- {dataset}: {count}")

    for dataset, counts in review["dispositions"].items():
        lines.extend(["", f"## {dataset} dispositions", ""])
        if counts:
            for disposition, count in counts.items():
                lines.append(f"- {disposition}: {count}")
        else:
            lines.append("- none")

    lines.extend(["", "## Content-audit backlog", ""])
    backlog = review["content_audit_backlog"]
    if backlog:
        for disposition, count in backlog.items():
            lines.append(f"- {disposition}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `migrated_*` and `*_seed` rows are preserved legacy knowledge and still require independent source review before promotion to `source_verified`.",
        "- `appearance_derived_pending_audit` rows must be explained by canonical appearances/portrayals/entity relations rather than copied back as work-to-work facts.",
        "- `legacy_display_placement_seed` rows are display history only and must not become chronology facts without evidence.",
        "- `rejected_superseded` remains visible as a watch item so a later official status change cannot be silently missed.",
        "- reproduced story-path rows are compatibility observations, not canonical source facts.",
        "",
    ])
    (migration / "MIGRATION_REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
    return review


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    review = write_review_outputs(args.repo_root.resolve())
    print(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
