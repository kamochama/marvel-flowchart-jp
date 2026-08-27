from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .db_schema import TABLE_SPECS, TableSpec, create_schema
from .db_views import install_internal_helpers, install_public_views


@dataclass(frozen=True)
class CompileResult:
    db_path: Path
    table_counts: dict[str, int]


def _read_csv_rows(path: Path, spec: TableSpec) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = tuple(reader.fieldnames or ())
        if actual != spec.columns:
            raise ValueError(f"db_input_header_mismatch:{spec.name}: expected={spec.columns!r} actual={actual!r}")
        return list(reader)


def _row_values(spec: TableSpec, row: dict[str, str]) -> tuple[object, ...]:
    values: list[object] = []
    for column in spec.columns:
        value: object = row.get(column, "")
        if spec.name == "portrayals" and column == "entity_id" and value == "":
            value = None
        values.append(value)
    return tuple(values)


def _insert_rows(connection: sqlite3.Connection, spec: TableSpec, rows: list[dict[str, str]]) -> None:
    columns = ",".join(spec.columns)
    placeholders = ",".join("?" for _ in spec.columns)
    statement = f"INSERT INTO {spec.name} ({columns}) VALUES ({placeholders})"
    connection.executemany(statement, (_row_values(spec, row) for row in rows))


def _run_integrity_checks(connection: sqlite3.Connection) -> None:
    foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_issues:
        raise sqlite3.IntegrityError(f"foreign_key_check_failed:{foreign_key_issues!r}")
    integrity = connection.execute("PRAGMA integrity_check").fetchall()
    if integrity != [("ok",)]:
        raise sqlite3.DatabaseError(f"integrity_check_failed:{integrity!r}")


def open_query_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def compile_database(repo_root: Path, output_path: Path | None = None) -> CompileResult:
    repo_root = repo_root.resolve()
    output_path = (output_path or (repo_root / "data" / "derived" / "db" / "marvel.sqlite")).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temp_path.unlink(missing_ok=True)

    connection: sqlite3.Connection | None = None
    table_counts: dict[str, int] = {}
    try:
        connection = sqlite3.connect(temp_path)
        create_schema(connection)
        with connection:
            for spec in TABLE_SPECS:
                rows = _read_csv_rows(repo_root / spec.source_path, spec)
                _insert_rows(connection, spec, rows)
                table_counts[spec.name] = len(rows)
            install_internal_helpers(connection)
            install_public_views(connection)
            _run_integrity_checks(connection)
        connection.close()
        connection = None
        output_path.unlink(missing_ok=True)
        temp_path.replace(output_path)
    except Exception:
        if connection is not None:
            connection.close()
        temp_path.unlink(missing_ok=True)
        raise

    return CompileResult(output_path, table_counts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile frozen Marvel Library canonical facts into SQLite.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = compile_database(args.repo_root, args.output)
    print(json.dumps({"db_path": str(result.db_path), "table_counts": result.table_counts}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
