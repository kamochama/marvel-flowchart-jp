from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

from .ids import slug_id


_GROUP_OVERRIDES = {
    "シュリ／エムバク／ネイモア": ["シュリ", "エムバク", "ネイモア"],
}
_PAREN_ACTOR = re.compile(r"^(.*?)（([A-Za-z][^（）]*?)）$")
_UNKNOWN_ROLE = re.compile(r"^([A-Za-z][A-Za-z .'-]+)（役名.*）$")
_RETURN_ACTOR = re.compile(r"^(.+?) / .+? return confirmed$", re.IGNORECASE)
_CAST_ACTOR = re.compile(r"^([A-Z][A-Za-z .'-]+) cast confirmed$", re.IGNORECASE)


class EntityMigrationError(ValueError):
    pass


def _source_by_url(source_rows: Iterable[dict[str, str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in source_rows:
        url = (row.get("url") or "").strip()
        source_id = (row.get("source_id") or "").strip()
        if url and source_id and url not in result:
            result[url] = source_id
    return result


def _add_unique(rows: list[dict[str, str]], seen: set[tuple[str, ...]], key: tuple[str, ...], row: dict[str, str]) -> None:
    if key not in seen:
        seen.add(key)
        rows.append(row)


def _entity_row(name: str) -> dict[str, str]:
    return {
        "entity_id": slug_id("entity", name),
        "name_ja": name,
        "name_en": "",
        "entity_type": "character",
        "notes": "Migrated as legacy seed; identity/variant reconciliation remains separately auditable.",
    }


def _appearance_row(work_id: str, entity_id: str, note: str) -> dict[str, str]:
    return {
        "appearance_id": slug_id("appearance", work_id, entity_id),
        "work_id": work_id,
        "entity_id": entity_id,
        "appearance_kind": "unknown",
        "certainty": "unknown",
        "verification_status": "legacy_seed",
        "notes": note,
    }


def _person_row(name: str) -> dict[str, str]:
    return {
        "person_id": slug_id("person", name),
        "name": name,
        "notes": "Migrated from legacy return/cast seed.",
    }


def _portrayal_row(work_id: str, person_id: str, entity_id: str, kind: str) -> dict[str, str]:
    return {
        "portrayal_id": slug_id("portrayal", work_id, person_id, entity_id or "unknown-role"),
        "work_id": work_id,
        "person_id": person_id,
        "entity_id": entity_id,
        "portrayal_kind": kind,
        "certainty": "unknown",
        "verification_status": "legacy_seed",
        "notes": "Migrated from legacy entity_returns; role/identity must follow source evidence, not actor reuse.",
    }


def _evidence_row(fact_table: str, fact_id: str, source_id: str, note: str) -> dict[str, str]:
    return {
        "evidence_id": slug_id("evidence", fact_table, fact_id, source_id),
        "fact_table": fact_table,
        "fact_id": fact_id,
        "source_id": source_id,
        "evidence_role": "legacy_seed",
        "quoted_or_paraphrased_note": note,
        "verified_at": "",
    }


def _split_return_entity(label: str) -> tuple[list[str], str | None, bool]:
    """Return (entity names, performer name, unknown_role)."""
    label = label.strip()
    if label in _GROUP_OVERRIDES:
        return list(_GROUP_OVERRIDES[label]), None, False
    unknown = _UNKNOWN_ROLE.match(label)
    if unknown:
        return [], unknown.group(1).strip(), True
    actor = _PAREN_ACTOR.match(label)
    if actor:
        return [actor.group(1).strip()], actor.group(2).strip(), False
    return [label], None, False


def _performer_from_evidence(evidence: str) -> str | None:
    for pattern in (_RETURN_ACTOR, _CAST_ACTOR):
        match = pattern.match(evidence.strip())
        if match:
            return match.group(1).strip()
    return None


def normalize_entity_seeds(
    char_links: list[dict[str, str]],
    entity_returns: list[dict[str, str]],
    source_rows: Iterable[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    sources = _source_by_url(source_rows)
    entities: list[dict[str, str]] = []
    appearances: list[dict[str, str]] = []
    people: list[dict[str, str]] = []
    portrayals: list[dict[str, str]] = []
    entity_relations: list[dict[str, str]] = []
    evidence_rows: list[dict[str, str]] = []
    dispositions: list[dict[str, str]] = []

    seen_entities: set[tuple[str, ...]] = set()
    seen_appearances: set[tuple[str, ...]] = set()
    seen_people: set[tuple[str, ...]] = set()
    seen_portrayals: set[tuple[str, ...]] = set()
    seen_evidence: set[tuple[str, ...]] = set()

    for index, row in enumerate(char_links, start=1):
        name = row["character"].strip()
        work_id = row["work_id"].strip()
        entity = _entity_row(name)
        _add_unique(entities, seen_entities, (entity["entity_id"],), entity)
        appearance = _appearance_row(work_id, entity["entity_id"], "Migrated from index.html CHAR_LINKS; not independent evidence.")
        _add_unique(appearances, seen_appearances, (work_id, entity["entity_id"]), appearance)
        dispositions.append({
            "legacy_row_id": f"charlink-{index:06d}",
            "legacy_kind": "CHAR_LINKS",
            "disposition": "migrated_appearance_seed",
            "fact_ids": appearance["appearance_id"],
            "notes": "Exact legacy character/work pair preserved as unverified appearance seed.",
        })

    for index, row in enumerate(entity_returns, start=1):
        work_id = row["target_work_id"].strip()
        names, performer, unknown_role = _split_return_entity(row["entity"])
        performer = performer or _performer_from_evidence(row.get("evidence", ""))
        source_url = row.get("source_url", "").strip()
        source_id = sources.get(source_url, "")
        if source_url and not source_id:
            raise EntityMigrationError(f"entity return source URL is not registered: {source_url}")

        fact_ids: list[str] = []
        entity_ids: list[str] = []
        for name in names:
            entity = _entity_row(name)
            entity_id = entity["entity_id"]
            entity_ids.append(entity_id)
            _add_unique(entities, seen_entities, (entity_id,), entity)
            appearance = _appearance_row(work_id, entity_id, "Migrated from entity_returns; source-backed proxy retained as seed.")
            _add_unique(appearances, seen_appearances, (work_id, entity_id), appearance)
            fact_ids.append(appearance["appearance_id"])
            if source_id:
                ev = _evidence_row("appearances.csv", appearance["appearance_id"], source_id, row.get("evidence", ""))
                _add_unique(evidence_rows, seen_evidence, (ev["evidence_id"],), ev)

        if performer:
            person = _person_row(performer)
            _add_unique(people, seen_people, (person["person_id"],), person)
            targets = [""] if unknown_role or not entity_ids else entity_ids
            for entity_id in targets:
                portrayal = _portrayal_row(
                    work_id,
                    person["person_id"],
                    entity_id,
                    "unknown_role" if not entity_id else "same_character",
                )
                _add_unique(
                    portrayals,
                    seen_portrayals,
                    (work_id, person["person_id"], entity_id, portrayal["portrayal_kind"]),
                    portrayal,
                )
                fact_ids.append(portrayal["portrayal_id"])
                if source_id:
                    ev = _evidence_row("portrayals.csv", portrayal["portrayal_id"], source_id, row.get("evidence", ""))
                    _add_unique(evidence_rows, seen_evidence, (ev["evidence_id"],), ev)

        dispositions.append({
            "legacy_row_id": f"entity-return-{index:06d}",
            "legacy_kind": "entity_returns.csv",
            "disposition": "decomposed_entity_return_seed",
            "fact_ids": "|".join(dict.fromkeys(fact_ids)),
            "notes": "Representative-prior-work is not retained as canonical identity; target appearance/cast evidence is preserved.",
        })

    return {
        "entities": entities,
        "appearances": appearances,
        "people": people,
        "portrayals": portrayals,
        "entity_relations": entity_relations,
        "evidence": evidence_rows,
        "dispositions": dispositions,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_entity_seed_tables(repo_root: Path) -> dict[str, int]:
    migration = repo_root / "data" / "migration"
    library = repo_root / "data" / "library"
    result = normalize_entity_seeds(
        _read_csv(migration / "legacy_char_links.csv"),
        _read_csv(migration / "legacy_entity_returns.csv"),
        _read_csv(repo_root / "data" / "sources.csv"),
    )
    fields = {
        "entities": ["entity_id", "name_ja", "name_en", "entity_type", "notes"],
        "appearances": ["appearance_id", "work_id", "entity_id", "appearance_kind", "certainty", "verification_status", "notes"],
        "people": ["person_id", "name", "notes"],
        "portrayals": ["portrayal_id", "work_id", "person_id", "entity_id", "portrayal_kind", "certainty", "verification_status", "notes"],
        "entity_relations": ["entity_relation_id", "source_entity_id", "relation_kind", "target_entity_id", "certainty", "verification_status", "notes"],
        "evidence": ["evidence_id", "fact_table", "fact_id", "source_id", "evidence_role", "quoted_or_paraphrased_note", "verified_at"],
        "dispositions": ["legacy_row_id", "legacy_kind", "disposition", "fact_ids", "notes"],
    }
    for name in ("entities", "appearances", "people", "portrayals", "entity_relations", "evidence"):
        _write_csv(library / f"{name}.csv", result[name], fields[name])
    _write_csv(migration / "entity_seed_dispositions.csv", result["dispositions"], fields["dispositions"])
    return {name: len(rows) for name, rows in result.items()}
