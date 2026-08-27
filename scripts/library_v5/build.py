from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .audit import write_audit_outputs
from .derive_compat import write_compatibility_outputs
from .derive_edges import write_derived_edges
from .extract_legacy import write_legacy_seeds
from .migrate_entities import write_entity_seed_tables
from .migrate_works_relations import write_work_relation_tables
from .review_migration import write_review_outputs


GENERATED_PATHS = [
    "data/derived",
    "data/migration",
    "views/flowchart",
]
GENERATED_LIBRARY_FILES = [
    "works.csv",
    "entities.csv",
    "entity_relations.csv",
    "appearances.csv",
    "people.csv",
    "portrayals.csv",
    "continuities.csv",
    "work_continuities.csv",
    "chronology_assertions.csv",
    "work_relations.csv",
    "sources.csv",
    "evidence.csv",
    "manifest.json",
]


def clean_generated(repo_root: Path) -> None:
    for rel in GENERATED_PATHS:
        path = repo_root / rel
        if path.exists():
            shutil.rmtree(path)
    library = repo_root / "data" / "library"
    library.mkdir(parents=True, exist_ok=True)
    for name in GENERATED_LIBRARY_FILES:
        path = library / name
        if path.exists():
            path.unlink()


def build(repo_root: Path, *, clean: bool = True) -> dict[str, object]:
    repo_root = repo_root.resolve()
    if clean:
        clean_generated(repo_root)

    result: dict[str, object] = {}
    result["legacy_extract"] = write_legacy_seeds(repo_root)
    result["entities"] = write_entity_seed_tables(repo_root)
    result["works_relations"] = write_work_relation_tables(repo_root)
    result["derived_edges"] = write_derived_edges(repo_root, mode="combined_all_pairs")
    result["compatibility"] = write_compatibility_outputs(repo_root)
    result["migration_review"] = write_review_outputs(repo_root)
    audit = write_audit_outputs(repo_root)
    result["audit_ok"] = audit["ok"]
    result["audit_issue_count"] = len(audit["issues"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and audit Marvel Library v5 migration outputs.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()
    result = build(args.repo_root, clean=not args.no_clean)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["audit_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
