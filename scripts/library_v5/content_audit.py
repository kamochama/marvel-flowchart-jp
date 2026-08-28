from __future__ import annotations

import csv
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

HIGH_IMPACT_WORK_ID_FRAGMENTS = (
    "avengers-doomsday",
    "spider-man-brand-new-day",
    "fantastic-four-first-steps",
    "visionquest",
    "wonder-man",
    "secret-wars",
    "thunderbolts-new-avengers",
)

ALLOWED_STATUSES = {"legacy_seed", "source_verified", "conflicted", "superseded"}
ALLOWED_TRANSITIONS = {
    "legacy_seed": {"legacy_seed", "source_verified", "conflicted", "superseded"},
    "source_verified": {"source_verified", "conflicted", "superseded"},
    "conflicted": {"conflicted", "source_verified", "superseded"},
    "superseded": {"superseded"},
}
SAME_STATUS_REVIEW_ACTIONS = {
    "retained_seed",
    "verified_rechecked",
    "conflict_rechecked",
    "superseded_rechecked",
}


def _issue(code: str, message: str, **extra: str) -> dict[str, str]:
    return {"severity": "error", "code": code, "message": message, **extra}


def _fact_index(tables: dict[str, list[dict[str, str]]]) -> dict[tuple[str, str], dict[str, str]]:
    result: dict[tuple[str, str], dict[str, str]] = {}
    for table_name, id_column in FACT_ID_COLUMNS.items():
        for row in tables.get(table_name, []):
            fact_id = (row.get(id_column) or "").strip()
            if fact_id:
                result[(table_name, fact_id)] = row
    return result


def _split_ids(value: str) -> list[str]:
    return [part.strip() for part in value.replace(",", "|").split("|") if part.strip()]


def validate_reviews(
    tables: dict[str, list[dict[str, str]]],
    evidence_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    facts = _fact_index(tables)
    evidence_ids = {(row.get("evidence_id") or "").strip() for row in evidence_rows}
    issues: list[dict[str, str]] = []
    seen_review_ids: set[str] = set()
    latest_by_fact: dict[tuple[str, str], dict[str, str]] = {}
    last_status_by_fact: dict[tuple[str, str], str] = {}

    for index, review in enumerate(review_rows, start=2):
        review_id = (review.get("review_id") or "").strip()
        table = (review.get("fact_table") or "").strip()
        fact_id = (review.get("fact_id") or "").strip()
        previous = (review.get("previous_verification_status") or "").strip()
        new = (review.get("new_verification_status") or "").strip()
        action = (review.get("review_action") or "").strip()
        review_evidence_ids = _split_ids(review.get("evidence_ids") or "")

        if not review_id or review_id in seen_review_ids:
            issues.append(_issue("duplicate_review_id", f"reviews.csv row {index} has missing or duplicate review_id={review_id!r}", row=str(index), review_id=review_id))
        else:
            seen_review_ids.add(review_id)

        key = (table, fact_id)
        if key not in facts:
            issues.append(_issue("review_missing_fact", f"reviews.csv row {index} references missing fact {table}:{fact_id}", row=str(index), fact_table=table, fact_id=fact_id))
        for evidence_id in review_evidence_ids:
            if evidence_id not in evidence_ids:
                issues.append(_issue("review_missing_evidence", f"reviews.csv row {index} references missing evidence {evidence_id}", row=str(index), evidence_id=evidence_id))

        prior_review_status = last_status_by_fact.get(key)
        if prior_review_status is not None and previous != prior_review_status:
            issues.append(_issue("review_history_discontinuity", f"reviews.csv row {index} previous status {previous!r} does not match prior review status {prior_review_status!r}", row=str(index), review_id=review_id))

        is_creation = action == "created_verified"
        if is_creation:
            allowed = prior_review_status is None and previous == "" and new == "source_verified"
            if not review_evidence_ids:
                issues.append(_issue("created_verified_without_evidence", f"reviews.csv row {index} created_verified requires at least one evidence id", row=str(index), review_id=review_id))
        else:
            allowed = previous in ALLOWED_STATUSES and new in ALLOWED_TRANSITIONS.get(previous, set())
            if previous == new and action not in SAME_STATUS_REVIEW_ACTIONS:
                allowed = False
        if not allowed:
            issues.append(_issue("invalid_review_transition", f"reviews.csv row {index} invalid transition {previous!r}->{new!r} for action {action!r}", row=str(index), review_id=review_id))

        latest_by_fact[key] = review
        last_status_by_fact[key] = new

    for key, review in latest_by_fact.items():
        fact = facts.get(key)
        if fact is None:
            continue
        current = (fact.get("verification_status") or "").strip()
        claimed = (review.get("new_verification_status") or "").strip()
        if current != claimed:
            issues.append(_issue("review_current_status_mismatch", f"latest review for {key[0]}:{key[1]} says {claimed!r} but canonical row is {current!r}", fact_table=key[0], fact_id=key[1]))
    return issues


def _work_ids(row: dict[str, str]) -> list[str]:
    values: list[str] = []
    for key in ("work_id", "source_work_id", "target_work_id", "earlier_work_id", "later_work_id"):
        value = (row.get(key) or "").strip()
        if value and value not in values:
            values.append(value)
    return values


def _is_high_impact(work_id: str) -> bool:
    return any(fragment in work_id for fragment in HIGH_IMPACT_WORK_ID_FRAGMENTS)


def build_review_queue(
    tables: dict[str, list[dict[str, str]]],
    *,
    high_degree_work_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    high_degree_work_ids = high_degree_work_ids or set()
    queue: list[dict[str, str]] = []
    for table_name, id_column in FACT_ID_COLUMNS.items():
        for row in tables.get(table_name, []):
            status = (row.get("verification_status") or "").strip()
            if status not in {"legacy_seed", "conflicted"}:
                continue
            fact_id = (row.get(id_column) or "").strip()
            works = _work_ids(row)
            if any(_is_high_impact(work_id) for work_id in works):
                priority = 10
                reason = "high_impact_current_cluster"
            elif any(work_id in high_degree_work_ids for work_id in works):
                priority = 20
                reason = "high_degree_work"
            elif status == "conflicted":
                priority = 30
                reason = "conflicted_fact"
            elif table_name == "work_relations.csv":
                priority = 40
                reason = "legacy_explicit_relation"
            elif table_name in {"appearances.csv", "portrayals.csv"}:
                priority = 50
                reason = "legacy_entity_fact"
            else:
                priority = 60
                reason = "legacy_continuity_or_identity_fact"
            queue.append({
                "queue_id": f"{table_name}:{fact_id}",
                "priority": str(priority),
                "priority_reason": reason,
                "fact_table": table_name,
                "fact_id": fact_id,
                "work_ids": "|".join(works),
                "verification_status": status,
                "certainty": (row.get("certainty") or "").strip(),
            })
    return sorted(queue, key=lambda row: (int(row["priority"]), row["fact_table"], row["fact_id"]))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _load_tables(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: _read_csv(repo_root / "data" / "library" / name) for name in FACT_ID_COLUMNS}


def review_issues_from_repo(repo_root: Path) -> list[dict[str, str]]:
    reviews_path = repo_root / "data" / "content_audit" / "reviews.csv"
    if not reviews_path.exists():
        return [_issue("missing_content_review_ledger", "persistent data/content_audit/reviews.csv is required input")]
    return validate_reviews(
        _load_tables(repo_root),
        _read_csv(repo_root / "data" / "library" / "evidence.csv"),
        _read_csv(reviews_path),
    )


def _high_degree_work_ids(repo_root: Path) -> set[str]:
    counts: Counter[str] = Counter()
    for row in _read_csv(repo_root / "data" / "derived" / "work_edges_all.csv"):
        for key in ("source_work_id", "target_work_id"):
            work_id = (row.get(key) or "").strip()
            if work_id:
                counts[work_id] += 1
    return {work_id for work_id, degree in counts.items() if degree >= 8}


def write_content_audit_outputs(repo_root: Path) -> dict[str, object]:
    audit_dir = repo_root / "data" / "content_audit"
    reviews_path = audit_dir / "reviews.csv"
    if not reviews_path.exists():
        raise RuntimeError("missing_content_review_ledger: data/content_audit/reviews.csv must be created and reviewed explicitly")

    tables = _load_tables(repo_root)
    evidence_rows = _read_csv(repo_root / "data" / "library" / "evidence.csv")
    review_rows = _read_csv(reviews_path)
    issues = validate_reviews(tables, evidence_rows, review_rows)
    queue = build_review_queue(tables, high_degree_work_ids=_high_degree_work_ids(repo_root))
    queue_fields = ["queue_id", "priority", "priority_reason", "fact_table", "fact_id", "work_ids", "verification_status", "certainty"]
    _write_csv(audit_dir / "queue.csv", queue, queue_fields)

    status_counts: Counter[str] = Counter()
    for rows in tables.values():
        for row in rows:
            status = (row.get("verification_status") or "").strip()
            if status:
                status_counts[status] += 1
    priority_counts = Counter(row["priority_reason"] for row in queue)
    lines = [
        "# Marvel Library v5 Content Audit",
        "",
        f"Review ledger rows: {len(review_rows)}",
        f"Queue rows: {len(queue)}",
        f"Review integrity issues: {len(issues)}",
        "",
        "## Verification statuses",
        "",
        *(f"- {key}: {value}" for key, value in sorted(status_counts.items())),
        "",
        "## Queue priorities",
        "",
        *(f"- {key}: {value}" for key, value in sorted(priority_counts.items())),
        "",
        "## Review integrity issues",
        "",
        *([f"- [{issue['code']}] {issue['message']}" for issue in issues] or ["- none"]),
        "",
    ]
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "CONTENT_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    return {"queue_count": len(queue), "review_count": len(review_rows), "issues": issues, "status_counts": dict(status_counts)}
