from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .audit import write_audit_outputs
from .canonical_guard import (
    assert_protected_inputs_unchanged,
    canonical_hashes,
    protected_input_hashes,
)
from .content_audit import write_content_audit_outputs
from .db_compile import compile_database
from .db_export import export_work_graph
from .db_fingerprint import write_db_manifest
from .derive_compat import write_compatibility_outputs


GENERATED_PATHS = [
    "data/derived",
    "views/flowchart",
]
GENERATED_CONTENT_AUDIT_FILES = [
    "queue.csv",
    "CONTENT_AUDIT.md",
]


def clean_generated(repo_root: Path) -> None:
    """Delete only downstream products. Canonical and persistent review inputs survive."""
    repo_root = repo_root.resolve()
    for rel in GENERATED_PATHS:
        path = repo_root / rel
        if path.exists():
            shutil.rmtree(path)
    content_audit = repo_root / "data" / "content_audit"
    for name in GENERATED_CONTENT_AUDIT_FILES:
        path = content_audit / name
        if path.exists():
            path.unlink()


def build(repo_root: Path, *, clean: bool = True) -> dict[str, object]:
    repo_root = repo_root.resolve()
    protected_before = protected_input_hashes(repo_root)
    if clean:
        clean_generated(repo_root)

    result: dict[str, object] = {}
    db_result = compile_database(repo_root)
    db_manifest = write_db_manifest(repo_root, db_result.db_path)
    result["database"] = {
        "path": db_result.db_path.relative_to(repo_root).as_posix(),
        "manifest_path": db_manifest.relative_to(repo_root).as_posix(),
        "table_counts": db_result.table_counts,
    }
    result["derived_edges"] = export_work_graph(db_result.db_path, repo_root / "data" / "derived")
    result["compatibility"] = write_compatibility_outputs(repo_root)
    content_audit = write_content_audit_outputs(repo_root)
    result["content_audit"] = {
        "queue_count": content_audit["queue_count"],
        "review_count": content_audit["review_count"],
        "issue_count": len(content_audit["issues"]),
        "status_counts": content_audit["status_counts"],
    }
    audit = write_audit_outputs(repo_root)

    protected_after = protected_input_hashes(repo_root)
    assert_protected_inputs_unchanged(protected_before, protected_after)
    result["canonical_files"] = len(canonical_hashes(repo_root))
    result["audit_ok"] = audit["ok"] and not content_audit["issues"]
    result["audit_issue_count"] = len(audit["issues"]) + len(content_audit["issues"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and audit downstream products from frozen Marvel Library v5 canonical facts through SQLite.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()
    result = build(args.repo_root, clean=not args.no_clean)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["audit_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
