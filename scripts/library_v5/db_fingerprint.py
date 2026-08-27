from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Iterable

from .canonical_guard import canonical_hashes
from .db_schema import DB_SCHEMA_VERSION, TABLE_SPECS
from .db_views import PUBLIC_VIEW_NAMES


_INTERNAL_TABLE_PRIMARY_KEYS = {
    "_entity_identity_map": ("raw_entity_id",),
}

_VIEW_ORDER_KEYS = {
    "v_entity_work_history": ("work_id", "canonical_entity_id", "raw_entity_id", "appearance_id"),
    "v_continuity_works": ("continuity_id", "work_id", "work_continuity_id"),
    "v_work_connection_reasons": ("source_work_id", "target_work_id", "reason_kind", "canonical_entity_id", "relation_id", "reason_discriminator"),
    "v_work_connections_all": ("source_work_id", "target_work_id"),
    "v_flowchart_nodes": ("work_id",),
    "v_flowchart_edge_candidates": ("source_work_id", "target_work_id"),
}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql or "").strip()


def _hash_payload_rows(rows: Iterable[tuple[object, ...]]) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        payload = json.dumps(list(row), ensure_ascii=False, separators=(",", ":"))
        digest.update(payload.encode("utf-8"))
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()


def _table_primary_keys() -> dict[str, tuple[str, ...]]:
    keys = {spec.name: (spec.primary_key,) for spec in TABLE_SPECS}
    keys.update(_INTERNAL_TABLE_PRIMARY_KEYS)
    return keys


def _object_sql(connection: sqlite3.Connection) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {"tables": {}, "views": {}}
    for object_type, name, sql in connection.execute(
        """
        SELECT type,name,COALESCE(sql,'')
        FROM sqlite_master
        WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'
        ORDER BY type,name
        """
    ):
        bucket = "tables" if object_type == "table" else "views"
        normalized = _normalize_sql(sql)
        result[bucket][name] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return result


def _table_fingerprints(connection: sqlite3.Connection) -> dict[str, dict[str, object]]:
    primary_keys = _table_primary_keys()
    table_names = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    result: dict[str, dict[str, object]] = {}
    for table_name in table_names:
        key_columns = primary_keys.get(table_name)
        if not key_columns:
            raise ValueError(f"db_fingerprint_missing_table_key:{table_name}")
        order_by = ",".join(_quote(column) for column in key_columns)
        rows = connection.execute(f"SELECT * FROM {_quote(table_name)} ORDER BY {order_by}")
        count, content_hash = _hash_payload_rows(rows)
        result[table_name] = {
            "row_count": count,
            "content_sha256": content_hash,
            "order_key": list(key_columns),
        }
    return result


def _view_fingerprints(connection: sqlite3.Connection) -> dict[str, dict[str, object]]:
    existing = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    }
    missing = set(PUBLIC_VIEW_NAMES) - existing
    if missing:
        raise ValueError(f"db_fingerprint_missing_public_views:{sorted(missing)!r}")

    result: dict[str, dict[str, object]] = {}
    for view_name in PUBLIC_VIEW_NAMES:
        key_columns = _VIEW_ORDER_KEYS[view_name]
        order_by = ",".join(_quote(column) for column in key_columns)
        rows = connection.execute(f"SELECT * FROM {_quote(view_name)} ORDER BY {order_by}")
        count, content_hash = _hash_payload_rows(rows)
        result[view_name] = {
            "row_count": count,
            "content_sha256": content_hash,
            "order_key": list(key_columns),
        }
    return result


def _canonical_input_hashes(repo_root: Path) -> dict[str, str]:
    inputs = canonical_hashes(repo_root)
    reviews = repo_root / "data" / "content_audit" / "reviews.csv"
    if reviews.exists():
        inputs[reviews.relative_to(repo_root).as_posix()] = _sha256_file(reviews)
    return dict(sorted(inputs.items()))


def logical_fingerprint(db_path: Path, *, repo_root: Path) -> dict[str, object]:
    db_path = db_path.resolve()
    repo_root = repo_root.resolve()
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        schema_objects = _object_sql(connection)
        tables = _table_fingerprints(connection)
        views = _view_fingerprints(connection)
        canonical_inputs = _canonical_input_hashes(repo_root)
        equivalence_payload = {
            "db_schema_version": DB_SCHEMA_VERSION,
            "schema": schema_objects,
            "tables": tables,
            "views": views,
            "canonical_inputs": canonical_inputs,
        }
        encoded = json.dumps(equivalence_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        equivalence = hashlib.sha256(encoded).hexdigest()
        return {
            **equivalence_payload,
            "equivalence": equivalence,
            "diagnostics": {
                "sqlite_version": sqlite3.sqlite_version,
                "database_file": db_path.name,
            },
        }
    finally:
        connection.close()


def write_db_manifest(repo_root: Path, db_path: Path, *, output_path: Path | None = None) -> Path:
    repo_root = repo_root.resolve()
    output_path = (output_path or (repo_root / "data" / "derived" / "db" / "library_db_manifest.json")).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = logical_fingerprint(db_path, repo_root=repo_root)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a logical fingerprint for a compiled Marvel Library SQLite database.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    db_path = (args.db or (repo_root / "data" / "derived" / "db" / "marvel.sqlite")).resolve()
    output = write_db_manifest(repo_root, db_path, output_path=args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
