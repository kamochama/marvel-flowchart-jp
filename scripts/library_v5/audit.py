from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


FACT_ID_COLUMNS = {
    "releases.csv": "release_id",
    "production_status_assertions.csv": "production_status_assertion_id",
    "appearances.csv": "appearance_id",
    "portrayals.csv": "portrayal_id",
    "work_relations.csv": "work_relation_id",
    "entity_relations.csv": "entity_relation_id",
    "chronology_assertions.csv": "chronology_assertion_id",
    "work_continuities.csv": "work_continuity_id",
    "continuities.csv": "continuity_id",
    "events.csv": "event_id",
    "event_occurrences.csv": "event_occurrence_id",
    "event_participants.csv": "event_participant_id",
    "event_relations.csv": "event_relation_id",
    "multiverse_transitions.csv": "transition_id",
    "transition_participants.csv": "transition_participant_id",
}
QUALIFYING_EVIDENCE_ROLES = {"primary", "supporting"}
RAW_SQLITE_PATH = "data/derived/db/marvel.sqlite"
_DIRECTIONAL_TRANSITION_KINDS = {"physical_crossing", "summoning", "spell_displacement", "tva_transfer"}


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


def check_foreign_keys(tables: dict[str, list[dict[str, str]]], schemas: dict[str, dict[str, object]]) -> list[dict[str, str]]:
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
        if (row.get("evidence_role") or "").strip() in QUALIFYING_EVIDENCE_ROLES
    }
    issues: list[dict[str, str]] = []
    for table_name, id_column in FACT_ID_COLUMNS.items():
        for row in tables.get(table_name, []):
            if (row.get("verification_status") or "").strip() != "source_verified":
                continue
            fact_id = (row.get(id_column) or "").strip()
            if (table_name, fact_id) not in evidence_pairs:
                issues.append(_issue("source_verified_without_evidence", f"source_verified {table_name} fact lacks qualifying primary/supporting evidence", table=table_name, fact_id=fact_id))
    return issues


def check_transition_semantics(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    events = {
        (row.get("event_id") or "").strip(): row
        for row in tables.get("events.csv", [])
        if (row.get("event_id") or "").strip()
    }
    issues: list[dict[str, str]] = []
    for index, row in enumerate(tables.get("multiverse_transitions.csv", []), start=2):
        transition_id = (row.get("transition_id") or "").strip()
        event = events.get(transition_id)
        if event is not None and (event.get("event_kind") or "").strip() != "multiverse_transition":
            issues.append(_issue(
                "transition_event_kind_mismatch",
                f"multiverse transition {transition_id} must reference an events.csv row with event_kind=multiverse_transition",
                table="multiverse_transitions.csv",
                row=str(index),
                transition_id=transition_id,
            ))
        source = (row.get("source_continuity_id") or "").strip()
        destination = (row.get("destination_continuity_id") or "").strip()
        transition_kind = (row.get("transition_kind") or "").strip()
        if source and destination and source == destination and transition_kind in _DIRECTIONAL_TRANSITION_KINDS:
            issues.append(_issue(
                "transition_same_continuity",
                f"{transition_kind} transition {transition_id} cannot use the same known source and destination continuity",
                table="multiverse_transitions.csv",
                row=str(index),
                transition_id=transition_id,
                continuity_id=source,
            ))
    return issues


def check_migration_coverage(legacy_counts: dict[str, int], disposition_counts: dict[str, int]) -> list[dict[str, str]]:
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
        return next(csv.reader(handle), [])


def check_csv_shape(path: Path, table_name: str) -> list[dict[str, str]]:
    """Reject rows whose field count would be silently hidden by DictReader."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            return []
        expected_columns = len(header)
        issues: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            actual_columns = len(row)
            if actual_columns == expected_columns:
                continue
            issues.append(_issue(
                "malformed_csv_row",
                f"{table_name} row {row_number} has {actual_columns} columns; expected {expected_columns}",
                table=table_name,
                row=str(row_number),
                expected_columns=str(expected_columns),
                actual_columns=str(actual_columns),
            ))
        return issues


def manifest_output_path(repo_root: Path) -> Path:
    return repo_root / "data" / "derived" / "library_manifest.json"


def _hash_tree(repo_root: Path, root_name: str, excluded: set[str]) -> dict[str, str]:
    root = repo_root / root_name
    if not root.exists():
        return {}
    result: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(repo_root).as_posix()
        if rel in excluded or rel.startswith("data/migration/bootstrap/"):
            continue
        result[rel] = sha256_file(path)
    return result


def build_manifest(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    excluded = {
        "data/library/manifest.json",
        "data/derived/library_manifest.json",
        "data/derived/audit.json",
        "data/derived/LIBRARY_AUDIT.md",
        RAW_SQLITE_PATH,
    }
    canonical_inputs = _hash_tree(repo_root, "data/library", excluded)
    persistent_inputs = _hash_tree(repo_root, "data/migration", excluded)
    reviews = repo_root / "data" / "content_audit" / "reviews.csv"
    if reviews.exists():
        persistent_inputs[reviews.relative_to(repo_root).as_posix()] = sha256_file(reviews)
    generated_outputs: dict[str, str] = {}
    for root_name in ("data/derived", "views/flowchart"):
        generated_outputs.update(_hash_tree(repo_root, root_name, excluded))
    for name in ("queue.csv", "CONTENT_AUDIT.md"):
        path = repo_root / "data" / "content_audit" / name
        if path.exists():
            generated_outputs[path.relative_to(repo_root).as_posix()] = sha256_file(path)
    files = {**canonical_inputs, **persistent_inputs, **generated_outputs}
    return {
        "schema_version": "5.1",
        "hash_algorithm": "sha256",
        "canonical_inputs": canonical_inputs,
        "persistent_inputs": persistent_inputs,
        "generated_outputs": generated_outputs,
        "files": dict(sorted(files.items())),
    }


def _verification_status_counts(tables: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for table_name, rows in sorted(tables.items()):
        if not rows or "verification_status" not in rows[0]:
            continue
        counts = Counter((row.get("verification_status") or "").strip() or "<blank>" for row in rows)
        result[table_name] = dict(sorted(counts.items()))
    return result


def audit_repository(repo_root: Path) -> dict[str, object]:
    from .content_audit import review_issues_from_repo

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
        issues.extend(check_csv_shape(path, table_name))
        rows = _read_csv(path)
        tables[table_name] = rows
        primary_key = table_schema.get("primary_key")
        if primary_key:
            issues.extend(check_primary_keys(table_name, rows, str(primary_key)))

    issues.extend(check_foreign_keys(tables, table_schemas))
    issues.extend(check_transition_semantics(tables))
    issues.extend(check_evidence_coverage(tables))

    reviews_path = repo_root / "data" / "content_audit" / "reviews.csv"
    issues.extend(check_csv_shape(reviews_path, "data/content_audit/reviews.csv"))

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

    issues.extend(review_issues_from_repo(repo_root))

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

    derived_checks = [
        ("data/derived/work_pair_reasons.csv", "reason_id"),
        ("data/derived/work_edges_all.csv", "edge_id"),
        ("data/derived/prewatch_edges.csv", "prewatch_edge_id"),
    ]
    for rel, pk in derived_checks:
        issues.extend(check_primary_keys(rel, _read_csv(repo_root / rel), pk))

    return {
        "schema_version": "5.1",
        "ok": not any(issue.get("severity") == "error" for issue in issues),
        "issues": sorted(issues, key=lambda i: (i.get("code", ""), i.get("table", ""), i.get("row", ""), i.get("message", ""))),
        "observed_counts": {
            "canonical_tables": {name: len(rows) for name, rows in sorted(tables.items())},
            "verification_statuses": _verification_status_counts(tables),
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
    derived = repo_root / "data" / "derived"
    derived.mkdir(parents=True, exist_ok=True)

    audit = audit_repository(repo_root)
    (derived / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    counts = audit["observed_counts"]
    issue_lines = [f"- [{i['code']}] {i['message']}" for i in audit["issues"]] or ["- none"]
    verification_lines: list[str] = []
    for table_name, statuses in counts["verification_statuses"].items():
        status_text = ", ".join(f"{status}={count}" for status, count in statuses.items())
        verification_lines.append(f"- {table_name}: {status_text}")
    if not verification_lines:
        verification_lines = ["- none"]

    md = "\n".join([
        "# Marvel Library v5 Audit",
        "",
        f"Status: {'PASS' if audit['ok'] else 'FAIL'}",
        "",
        "## Principle",
        "",
        "Canonical facts are read-only build inputs. Counts below are observations, not correctness targets.",
        "",
        "## Frozen migration coverage",
        "",
        *(f"- {k}: {v}" for k, v in counts["legacy_inputs"].items()),
        "",
        "## Verification backlog",
        "",
        *verification_lines,
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
    (derived / "LIBRARY_AUDIT.md").write_text(md, encoding="utf-8")

    manifest = build_manifest(repo_root)
    manifest_output_path(repo_root).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit
