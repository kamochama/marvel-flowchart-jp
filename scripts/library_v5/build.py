from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .audit import write_audit_outputs
from .canonical_guard import assert_canonical_unchanged, canonical_hashes
from .derive_compat import write_compatibility_outputs
from .derive_edges import write_derived_edges


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
    before = canonical_hashes(repo_root)
    if clean:
        clean_generated(repo_root)

    result: dict[str, object] = {}
    result["derived_edges"] = write_derived_edges(repo_root, mode="combined_all_pairs")
    result["compatibility"] = write_compatibility_outputs(repo_root)
    audit = write_audit_outputs(repo_root)

    after = canonical_hashes(repo_root)
    assert_canonical_unchanged(before, after)
    result["canonical_files"] = len(after)
    result["audit_ok"] = audit["ok"]
    result["audit_issue_count"] = len(audit["issues"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and audit downstream products from frozen Marvel Library v5 canonical facts.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()
    result = build(args.repo_root, clean=not args.no_clean)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["audit_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
