from __future__ import annotations

import hashlib
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hashes(repo_root: Path) -> dict[str, str]:
    """Return deterministic SHA-256 hashes for every canonical library file."""
    repo_root = repo_root.resolve()
    library = repo_root / "data" / "library"
    if not library.exists():
        return {}
    return {
        path.relative_to(repo_root).as_posix(): _sha256(path)
        for path in sorted(p for p in library.rglob("*") if p.is_file())
    }


def protected_input_hashes(repo_root: Path) -> dict[str, str]:
    """Hash authoritative library files plus persistent human review history."""
    repo_root = repo_root.resolve()
    result = canonical_hashes(repo_root)
    reviews = repo_root / "data" / "content_audit" / "reviews.csv"
    if reviews.exists():
        result[reviews.relative_to(repo_root).as_posix()] = _sha256(reviews)
    return dict(sorted(result.items()))


def _assert_hashes_unchanged(before: dict[str, str], after: dict[str, str], *, error_code: str) -> None:
    if before == after:
        return
    keys = sorted(set(before) | set(after))
    changed = [key for key in keys if before.get(key) != after.get(key)]
    detail = ", ".join(changed) if changed else "unknown"
    raise RuntimeError(f"{error_code}: {detail}")


def assert_canonical_unchanged(before: dict[str, str], after: dict[str, str]) -> None:
    _assert_hashes_unchanged(before, after, error_code="canonical_input_mutated")


def assert_protected_inputs_unchanged(before: dict[str, str], after: dict[str, str]) -> None:
    _assert_hashes_unchanged(before, after, error_code="protected_input_mutated")
