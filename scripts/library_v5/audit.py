from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


FACT_ID_COLUMNS = {
    "appearances.csv": "appearance_id",
    "portrayals.csv": "portrayal_id",
    "work_relations.csv": "work_relation_id",
    "entity_relations.csv": "entity_relation_id",
    "chronology_assertions.csv": "chronology_assertion_id",
    "work_continuities.csv": "work_continuity_id",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _issue(code: str, message: str, **extra: str) -> dict[str, str]:
    return {"severity": "error", "code": code, "message": message, **extra}


def check_primary_keys(table_name: str, rows: list[dict[str, str]], primary_key: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        value = (row.get(primary_key) or "").strip()
        if not value:
            issues.append(_issue("missing_primary_key", f"{table_name} row {index} has empty {primary_key}", table=table_name, row=str(index), column=primary_key))
        elif value in seen:
            issues.append(_issue("duplicate_primary_key", f"{table_name} duplicates {primary_key}={value}", table=table_name, row=str(index), column=primary_key, value=value))
        else:
            seen.add(value)
    return issues


def check_foreign_keys(
    tables: dict[str, list[dict[str, str]]],
    schemas: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for table_name, table_schema in schemas.items():
        rows = tables.get(table_name, [])
        nullable = set(table_schema.get("nullable_columns", []))
        foreign_keys = table_schema.get("foreign_keys", {})
        if not isinstance(foreign_keys, dict):
            continue
        for column, target in foreign_keys.items():
            target_base, target_column = str(target).split(".", 1)
            target_table = f"{target_base}.csv"
            target_values = {(row.get(target_column) or "").strip() for row in tables.get(target_table, [])}
            for index, row in enumerate(rows, start=2):
                value = (row.get(column) or "").strip()
                if not value and column in nullable:
                    continue
                if not value or value not in target_values:
                    issues.append(_issue("broken_foreign_key", f"{table_name} row {index} {column}={value!r} does not resolve to {target}", table=table_name, row=str(index), column=column, value=value, target=str(target)))
    return issues


def check_evidence_coverage(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    evidence_pairs = {
        ((row.get("fact_table") or "").strip(), (row.get("fact_id") or "").strip())
        for row in tables.get("evidence.csv", [])
    }
    issues: list[dict[str, str]] = []
    for table_name, id_column in FACT_ID_COLUMNS.items():
        for row in tables.get(table_name, []):
            if (row.get("verification_status") or "").strip() != "verified":
                continue
            fact_id = (row.get(id_column) or "").strip()
            if (table_name, fact_id) not in evidence_pairs:
                issues.append(_issue("verified_without_evidence", f"verified {table_name} fact lacks evidence", table=table_name, fact_id=fact_id))
    return issues


def check_migration_coverage(
    legacy_counts: dict[str, int],
    disposition_counts: dict[str, int],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for dataset in sorted(legacy_counts):
        expected = legacy_counts[dataset]
        actual = disposition_counts.get(dataset, 0)
        if expected != actual:
            issues.append(_issue("migration_coverage_mismatch", f"{dataset}: input rows={expected}, disposition rows={actual}", dataset=dataset, expected=str(expected), actual=str(actual)))
    return issues


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def build_manifest(repo_root: Path) -> dict[str, object]:
    excluded = {
        "data/library/manifest.json",
        "data/migration/audit.json",
        "data/migration/MIGRATION_AUDIT.md",
    }
    files: dict[str, str] = {}
    for root_name in ("data/library", "data/derived", "data/migration", "views/flowchart"):
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(repo_root).as_posix()
            if rel in excluded:
                continue
            files[rel] = sha256_file(path)
    return {"schema_version": "5.0", "hash_algorithm": "sha256", "files": files}


def audit_repository(repo_root: Path) -> dict[str, object]:
    schema_path = repo_root / "data" / "library" / "schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    table_schemas = schema["tables"]
    tables: dict[str, list[dict[str, str]]] = {}
    issues: list[dict[str, str]] = []

    for table_name, table_schema in table_schemas.items():
        path = repo_root / "data" / "library" / table_name
        if not path.exists():
            issues.append(_issue("missing_canonical_table", f"missing canonical table {table_name}", table=table_name))
            tables[table_name] = []
            continue
        header = _csv_header(path)
        required = list(table_schema.get("required_columns", []))
        missing = [column for column in required if column not in header]
        if missing:
            issues.append(_issue("missing_required_columns", f"{table_name} missing columns: {', '.join(missing)}", table=table_name))
        rows = _read_csv(path)
        tables[table_name] = rows
        primary_key = table_schema.get("primary_key")
        if primary_key:
            issues.extend(check_primary_keys(table_name, rows, str(primary_key)))

    issues.extend(check_foreign_keys(tables, table_schemas))
    issues.extend(check_evidence_coverage(tables))

    # Evidence uses a polymorphic fact reference. Validate source FK through the
    # schema above, then verify the referenced fact exists when it targets a
    # canonical table with a known primary key.
    fact_indexes: dict[str, set[str]] = {}
    for table_name, table_schema in table_schemas.items():
        pk = table_schema.get("primary_key")
        if pk:
            fact_indexes[table_name] = {(row.get(str(pk)) or "").strip() for row in tables.get(table_name, [])}
    for index, row in enumerate(tables.get("evidence.csv", []), start=2):
        fact_table = (row.get("fact_table") or "").strip()
        fact_id = (row.get("fact_id") or "").strip()
        if fact_table in fact_indexes and fact_id not in fact_indexes[fact_table]:
            issues.append(_issue("broken_evidence_fact_reference", f"evidence.csv row {index} references missing {fact_table}:{fact_id}", table="evidence.csv", row=str(index), fact_id=fact_id, fact_table=fact_table))

    connection_rows = _read_csv(repo_root / "data" / "connections.csv")
    char_rows = _read_csv(repo_root / "data" / "migration" / "legacy_char_links.csv")
    return_rows = _read_csv(repo_root / "data" / "entity_returns.csv")
    story_rows = _read_csv(repo_root / "data" / "story_paths.csv")
    connection_disp = _read_csv(repo_root / "data" / "migration" / "connection_dispositions.csv")
    entity_disp = _read_csv(repo_root / "data" / "migration" / "entity_seed_dispositions.csv")
    story_disp = _read_csv(repo_root / "data" / "migration" / "story_path_dispositions.csv")

    disposition_counts = Counter((row.get("legacy_kind") or "").strip() for row in entity_disp)
    issues.extend(check_migration_coverage(
        legacy_counts={
            "connections": len(connection_rows),
            "char_links": len(char_rows),
            "entity_returns": len(return_rows),
            "story_paths": len(story_rows),
        },
        disposition_counts={
            "connections": len(connection_disp),
            "char_links": disposition_counts.get("CHAR_LINKS", 0),
            "entity_returns": disposition_counts.get("entity_returns.csv", 0),
            "story_paths": len(story_disp),
        },
    ))

    # Derived reason IDs and logical edge IDs must also be unique.
    derived_checks = [
        ("data/derived/work_pair_reasons.csv", "reason_id"),
        ("data/derived/work_edges_all.csv", "edge_id"),
        ("data/derived/prewatch_edges.csv", "prewatch_edge_id"),
    ]
    for rel, pk in derived_checks:
        rows = _read_csv(repo_root / rel)
        issues.extend(check_primary_keys(rel, rows, pk))

    return {
        "schema_version": "5.0",
        "ok": not any(issue.get("severity") == "error" for issue in issues),
        "issues": sorted(issues, key=lambda i: (i.get("code", ""), i.get("table", ""), i.get("row", ""), i.get("message", ""))),
        "observed_counts": {
            "canonical_tables": {name: len(rows) for name, rows in sorted(tables.items())},
            "legacy_inputs": {
                "connections": len(connection_rows),
                "char_links": len(char_rows),
                "entity_returns": len(return_rows),
                "story_paths": len(story_rows),
            },
            "derived": {
                "work_pair_reasons": len(_read_csv(repo_root / "data" / "derived" / "work_pair_reasons.csv")),
                "work_edges_all": len(_read_csv(repo_root / "data" / "derived" / "work_edges_all.csv")),
                "prewatch_edges": len(_read_csv(repo_root / "data" / "derived" / "prewatch_edges.csv")),
                "story_paths_reproduced": len(_read_csv(repo_root / "data" / "derived" / "story_paths.csv")),
            },
        },
    }


def write_audit_outputs(repo_root: Path) -> dict[str, object]:
    migration = repo_root / "data" / "migration"
    library = repo_root / "data" / "library"
    migration.mkdir(parents=True, exist_ok=True)
    library.mkdir(parents=True, exist_ok=True)

    audit = audit_repository(repo_root)
    (migration / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    counts = audit["observed_counts"]
    issue_lines = [f"- [{i['code']}] {i['message']}" for i in audit["issues"]] or ["- none"]
    md = "\n".join([
        "# Marvel Library v5 Migration Audit",
        "",
        f"Status: {'PASS' if audit['ok'] else 'FAIL'}",
        "",
        "## Principle",
        "",
        "Counts below are observations, not correctness targets. Completeness is measured by migration coverage, referential integrity, evidence state, and deterministic derivation.",
        "",
        "## Legacy input coverage",
        "",
        *(f"- {k}: {v}" for k, v in counts["legacy_inputs"].items()),
        "",
        "## Derived observations",
        "",
        *(f"- {k}: {v}" for k, v in counts["derived"].items()),
        "",
        "## Issues",
        "",
        *issue_lines,
        "",
    ])
    (migration / "MIGRATION_AUDIT.md").write_text(md, encoding="utf-8")

    manifest = build_manifest(repo_root)
    (library / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit
