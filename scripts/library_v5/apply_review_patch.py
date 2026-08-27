from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ALLOWED_PATHS = {
    "works.csv": Path("data/library/works.csv"),
    "entities.csv": Path("data/library/entities.csv"),
    "entity_relations.csv": Path("data/library/entity_relations.csv"),
    "appearances.csv": Path("data/library/appearances.csv"),
    "people.csv": Path("data/library/people.csv"),
    "portrayals.csv": Path("data/library/portrayals.csv"),
    "continuities.csv": Path("data/library/continuities.csv"),
    "work_continuities.csv": Path("data/library/work_continuities.csv"),
    "chronology_assertions.csv": Path("data/library/chronology_assertions.csv"),
    "work_relations.csv": Path("data/library/work_relations.csv"),
    "events.csv": Path("data/library/events.csv"),
    "event_occurrences.csv": Path("data/library/event_occurrences.csv"),
    "event_participants.csv": Path("data/library/event_participants.csv"),
    "event_relations.csv": Path("data/library/event_relations.csv"),
    "multiverse_transitions.csv": Path("data/library/multiverse_transitions.csv"),
    "transition_participants.csv": Path("data/library/transition_participants.csv"),
    "sources.csv": Path("data/library/sources.csv"),
    "evidence.csv": Path("data/library/evidence.csv"),
    "reviews.csv": Path("data/content_audit/reviews.csv"),
}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def apply_patch(repo_root: Path, patch_path: Path, *, archive: bool = False) -> list[Path]:
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    patch_id = (patch.get("patch_id") or "").strip()
    if not patch_id:
        raise ValueError("patch_id is required")
    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("operations must be a non-empty list")

    grouped: dict[str, list[dict[str, object]]] = {}
    for op in operations:
        if not isinstance(op, dict):
            raise ValueError("each operation must be an object")
        table = str(op.get("table") or "")
        if table not in ALLOWED_PATHS:
            raise ValueError(f"table is not patchable: {table}")
        grouped.setdefault(table, []).append(op)

    changed: list[Path] = []
    for table, table_ops in grouped.items():
        path = repo_root / ALLOWED_PATHS[table]
        fieldnames, rows = _read_csv(path)
        for op in table_ops:
            action = str(op.get("action") or "")
            key_column = str(op.get("key_column") or "")
            key = str(op.get("key") or "")
            if not key_column or key_column not in fieldnames or not key:
                raise ValueError(f"invalid key for {table}: {key_column}={key!r}")
            matches = [index for index, row in enumerate(rows) if row.get(key_column) == key]

            if action == "update":
                if len(matches) != 1:
                    raise ValueError(f"update expected exactly one row in {table}: {key_column}={key!r}")
                changes = op.get("set")
                if not isinstance(changes, dict) or not changes:
                    raise ValueError("update requires non-empty set object")
                unknown = set(changes) - set(fieldnames)
                if unknown:
                    raise ValueError(f"unknown columns for {table}: {sorted(unknown)}")
                rows[matches[0]].update({str(k): str(v) for k, v in changes.items()})
            elif action == "insert":
                if matches:
                    raise ValueError(f"insert would duplicate row in {table}: {key_column}={key!r}")
                values = op.get("values")
                if not isinstance(values, dict):
                    raise ValueError("insert requires values object")
                unknown = set(values) - set(fieldnames)
                if unknown:
                    raise ValueError(f"unknown columns for {table}: {sorted(unknown)}")
                row = {field: str(values.get(field, "")) for field in fieldnames}
                if row.get(key_column) != key:
                    raise ValueError("insert key must match values")
                rows.append(row)
            else:
                raise ValueError(f"unsupported action: {action}")
        _write_csv(path, fieldnames, rows)
        changed.append(path)

    if archive:
        applied_dir = repo_root / "data/content_audit/applied"
        applied_dir.mkdir(parents=True, exist_ok=True)
        destination = applied_dir / patch_path.name
        if destination.exists():
            raise ValueError(f"archive already exists: {destination}")
        patch_path.replace(destination)
        changed.extend([patch_path, destination])
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--patch")
    parser.add_argument("--all-pending", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()

    if args.all_pending:
        pending = sorted((root / "data/content_audit/pending").glob("*.json"))
        for patch_path in pending:
            apply_patch(root, patch_path, archive=True)
        print(json.dumps({"applied": [path.name for path in pending]}, sort_keys=True))
        return
    if not args.patch:
        parser.error("--patch or --all-pending is required")
    apply_patch(root, Path(args.patch).resolve(), archive=False)


if __name__ == "__main__":
    main()
