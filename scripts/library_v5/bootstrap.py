from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from .canonical_guard import assert_canonical_unchanged, canonical_hashes
from .derive_compat import derive_story_path_compat
from .derive_edges import write_derived_edges
from .extract_legacy import write_legacy_seeds
from .migrate_entities import write_entity_seed_tables
from .migrate_works_relations import write_work_relation_tables
from .review_migration import write_review_outputs


BOOTSTRAP_INPUTS = [
    "index.html",
    "data/entity_returns.csv",
    "data/sources.csv",
    "data/works.csv",
    "data/connections.csv",
    "data/chronology.csv",
    "data/story_paths.csv",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _copy_bootstrap_inputs(repo_root: Path, temp_root: Path) -> None:
    for rel in BOOTSTRAP_INPUTS:
        source = repo_root / rel
        target = temp_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    schema_source = repo_root / "data" / "library" / "schema.json"
    schema_target = temp_root / "data" / "library" / "schema.json"
    schema_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(schema_source, schema_target)


def _write_story_dispositions(temp_root: Path) -> None:
    story_rows = _read_csv(temp_root / "data" / "story_paths.csv")
    edge_rows = _read_csv(temp_root / "data" / "derived" / "work_edges_all.csv")
    compat = derive_story_path_compat(story_rows, edge_rows)
    _write_csv(
        temp_root / "data" / "migration" / "story_path_dispositions.csv",
        compat["dispositions"],
        ["legacy_row_id", "path_id", "edge_order", "source_id", "target_id", "legacy_edge_id", "disposition", "migration_note"],
    )


def _reconstruct_to(repo_root: Path, stage_root: Path) -> dict[str, object]:
    """Reconstruct the initial canonical seed in an isolated temp tree, then stage it."""
    if stage_root.exists():
        shutil.rmtree(stage_root)
    stage_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="marvel-library-v5-bootstrap-") as tmp:
        temp_root = Path(tmp)
        _copy_bootstrap_inputs(repo_root, temp_root)
        legacy = write_legacy_seeds(temp_root)
        entities = write_entity_seed_tables(temp_root)
        works_relations = write_work_relation_tables(temp_root)
        derived = write_derived_edges(temp_root, mode="combined_all_pairs")
        _write_story_dispositions(temp_root)
        review = write_review_outputs(temp_root)

        shutil.copytree(temp_root / "data" / "library", stage_root / "library")
        shutil.copytree(temp_root / "data" / "migration", stage_root / "migration")

    return {
        "legacy_extract": legacy,
        "entities": entities,
        "works_relations": works_relations,
        "derived_observation": derived,
        "migration_review": review,
    }


def candidate_manifest(repo_root: Path) -> dict[str, str]:
    library = repo_root / "data" / "migration" / "bootstrap" / "library"
    if not library.exists():
        return {}
    return {
        f"data/library/{path.relative_to(library).as_posix()}": _sha256(path)
        for path in sorted(p for p in library.rglob("*") if p.is_file())
    }


def assert_install_safe(
    baseline_hashes: dict[str, str],
    current_hashes: dict[str, str],
    *,
    force_destructive: bool,
) -> None:
    if baseline_hashes == current_hashes or force_destructive:
        return
    changed = sorted(
        key for key in set(baseline_hashes) | set(current_hashes)
        if baseline_hashes.get(key) != current_hashes.get(key)
    )
    raise RuntimeError("bootstrap_install_refused: canonical differs from frozen bootstrap baseline: " + ", ".join(changed))


def _install_candidate(repo_root: Path, stage_root: Path) -> list[str]:
    candidate = stage_root / "library"
    library = repo_root / "data" / "library"
    replacements = [f"data/library/{p.relative_to(candidate).as_posix()}" for p in sorted(x for x in candidate.rglob("*") if x.is_file())]
    if library.exists():
        shutil.rmtree(library)
    shutil.copytree(candidate, library)
    return replacements


def bootstrap(
    repo_root: Path,
    *,
    install_canonical: bool = False,
    force_destructive: bool = False,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    before = canonical_hashes(repo_root)
    stage_root = repo_root / "data" / "migration" / "bootstrap"
    reconstruction = _reconstruct_to(repo_root, stage_root)
    staged_hashes = candidate_manifest(repo_root)
    (stage_root / "candidate_manifest.json").write_text(
        json.dumps({"hash_algorithm": "sha256", "canonical_candidate": staged_hashes}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    installed = False
    replaced: list[str] = []
    if install_canonical:
        assert_install_safe(staged_hashes, before, force_destructive=force_destructive)
        replaced = _install_candidate(repo_root, stage_root)
        installed = True
    else:
        assert_canonical_unchanged(before, canonical_hashes(repo_root))

    return {
        "installed_canonical": installed,
        "replacement_files": replaced,
        "candidate_file_count": len(staged_hashes),
        "reconstruction": reconstruction,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct the initial Marvel Library v5 canonical seed in staging.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--install-canonical", action="store_true")
    parser.add_argument("--force-destructive", action="store_true")
    args = parser.parse_args()
    result = bootstrap(
        args.repo_root,
        install_canonical=args.install_canonical,
        force_destructive=args.force_destructive,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
