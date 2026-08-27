from __future__ import annotations

import sqlite3
from dataclasses import dataclass


DB_SCHEMA_VERSION = "1.0-phase1"

VERIFICATION_STATUSES = ("legacy_seed", "source_verified", "conflicted", "superseded")
CERTAINTIES = ("confirmed", "probable", "uncertain", "unknown")
ENTITY_TYPES = ("character", "organization", "artifact", "place", "species", "event", "concept")
ENTITY_RELATION_KINDS = ("variant_of", "identity_of", "successor_identity_of", "member_of")
APPEARANCE_KINDS = ("onscreen", "voice", "post_credit", "archive", "mention", "photo_or_recording", "unknown")
PORTRAYAL_KINDS = ("same_character", "variant", "voice", "archive", "unknown_role")
EVIDENCE_ROLES = ("primary", "supporting", "conflicting", "legacy_seed")
RELATION_SCOPES = ("story", "character", "crossover", "world_lore", "promotion", "variant_meta")
DIRECTNESSES = ("direct", "strong", "indirect", "proxy", "promotional")
CONTINUITY_SCOPES = ("same_or_intended", "multiverse", "variant", "promotional", "uncertain_legacy_tv", "uncertain_return_continuity")
WORK_RELATION_KINDS = ("sequel", "spinoff", "lead_in", "aftermath", "crossover", "world_lore", "promotion", "variant_callback", "story_link")


def _in_check(column: str, values: tuple[str, ...]) -> str:
    quoted = ",".join(f"'{value}'" for value in values)
    return f"CHECK ({column} IN ({quoted}))"


@dataclass(frozen=True)
class TableSpec:
    name: str
    source_path: str
    primary_key: str
    columns: tuple[str, ...]


TABLE_SPECS: tuple[TableSpec, ...] = (
    TableSpec(
        "works",
        "data/library/works.csv",
        "work_id",
        (
            "work_id", "title_ja", "title_en", "title_official", "release", "release_raw",
            "format", "status", "classification", "ja_status", "japan_date", "japan_type",
            "source_url", "source_note", "notes", "release_sort_date", "release_display_date",
            "release_kind", "release_certainty", "release_precision", "release_source_note",
            "aliases_ja", "title_audit_status", "title_audit_source_url", "title_last_verified",
            "title_management_note", "stable_id_note",
        ),
    ),
    TableSpec("entities", "data/library/entities.csv", "entity_id", ("entity_id", "name_ja", "name_en", "entity_type", "notes")),
    TableSpec("entity_relations", "data/library/entity_relations.csv", "entity_relation_id", ("entity_relation_id", "source_entity_id", "relation_kind", "target_entity_id", "certainty", "verification_status", "notes")),
    TableSpec("appearances", "data/library/appearances.csv", "appearance_id", ("appearance_id", "work_id", "entity_id", "appearance_kind", "certainty", "verification_status", "notes")),
    TableSpec("people", "data/library/people.csv", "person_id", ("person_id", "name", "notes")),
    TableSpec("portrayals", "data/library/portrayals.csv", "portrayal_id", ("portrayal_id", "work_id", "person_id", "entity_id", "portrayal_kind", "certainty", "verification_status", "notes")),
    TableSpec("continuities", "data/library/continuities.csv", "continuity_id", ("continuity_id", "label_ja", "label_en", "continuity_kind", "certainty", "verification_status", "notes")),
    TableSpec("work_continuities", "data/library/work_continuities.csv", "work_continuity_id", ("work_continuity_id", "work_id", "continuity_id", "relation_to_continuity", "certainty", "verification_status", "notes")),
    TableSpec("chronology_assertions", "data/library/chronology_assertions.csv", "chronology_assertion_id", ("chronology_assertion_id", "continuity_id", "earlier_work_id", "later_work_id", "certainty", "verification_status", "notes")),
    TableSpec("work_relations", "data/library/work_relations.csv", "work_relation_id", ("work_relation_id", "source_work_id", "target_work_id", "relation_kind", "relation_scope", "directness", "continuity_scope", "certainty", "verification_status", "notes")),
    TableSpec("sources", "data/library/sources.csv", "source_id", ("source_id", "purpose", "official_source", "checked_point", "url")),
    TableSpec("evidence", "data/library/evidence.csv", "evidence_id", ("evidence_id", "fact_table", "fact_id", "source_id", "evidence_role", "quoted_or_paraphrased_note", "verified_at")),
    TableSpec("reviews", "data/content_audit/reviews.csv", "review_id", ("review_id", "fact_table", "fact_id", "previous_verification_status", "new_verification_status", "review_action", "evidence_ids", "reviewed_at", "notes")),
)


def canonical_table_names() -> tuple[str, ...]:
    return tuple(spec.name for spec in TABLE_SPECS)


DDL: tuple[str, ...] = (
    """
    CREATE TABLE works (
        work_id TEXT PRIMARY KEY CHECK(length(trim(work_id)) > 0),
        title_ja TEXT NOT NULL DEFAULT '',
        title_en TEXT NOT NULL DEFAULT '',
        title_official TEXT NOT NULL DEFAULT '',
        release TEXT NOT NULL DEFAULT '',
        release_raw TEXT NOT NULL DEFAULT '',
        format TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT '',
        classification TEXT NOT NULL DEFAULT '',
        ja_status TEXT NOT NULL DEFAULT '',
        japan_date TEXT NOT NULL DEFAULT '',
        japan_type TEXT NOT NULL DEFAULT '',
        source_url TEXT NOT NULL DEFAULT '',
        source_note TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        release_sort_date TEXT NOT NULL DEFAULT '',
        release_display_date TEXT NOT NULL DEFAULT '',
        release_kind TEXT NOT NULL DEFAULT '',
        release_certainty TEXT NOT NULL DEFAULT '',
        release_precision TEXT NOT NULL DEFAULT '',
        release_source_note TEXT NOT NULL DEFAULT '',
        aliases_ja TEXT NOT NULL DEFAULT '',
        title_audit_status TEXT NOT NULL DEFAULT '',
        title_audit_source_url TEXT NOT NULL DEFAULT '',
        title_last_verified TEXT NOT NULL DEFAULT '',
        title_management_note TEXT NOT NULL DEFAULT '',
        stable_id_note TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE entities (
        entity_id TEXT PRIMARY KEY CHECK(length(trim(entity_id)) > 0),
        name_ja TEXT NOT NULL DEFAULT '',
        name_en TEXT NOT NULL DEFAULT '',
        entity_type TEXT NOT NULL {_in_check('entity_type', ENTITY_TYPES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE entity_relations (
        entity_relation_id TEXT PRIMARY KEY CHECK(length(trim(entity_relation_id)) > 0),
        source_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
        relation_kind TEXT NOT NULL {_in_check('relation_kind', ENTITY_RELATION_KINDS)},
        target_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE appearances (
        appearance_id TEXT PRIMARY KEY CHECK(length(trim(appearance_id)) > 0),
        work_id TEXT NOT NULL REFERENCES works(work_id),
        entity_id TEXT NOT NULL REFERENCES entities(entity_id),
        appearance_kind TEXT NOT NULL {_in_check('appearance_kind', APPEARANCE_KINDS)},
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE people (
        person_id TEXT PRIMARY KEY CHECK(length(trim(person_id)) > 0),
        name TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE portrayals (
        portrayal_id TEXT PRIMARY KEY CHECK(length(trim(portrayal_id)) > 0),
        work_id TEXT NOT NULL REFERENCES works(work_id),
        person_id TEXT NOT NULL REFERENCES people(person_id),
        entity_id TEXT REFERENCES entities(entity_id),
        portrayal_kind TEXT NOT NULL {_in_check('portrayal_kind', PORTRAYAL_KINDS)},
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE continuities (
        continuity_id TEXT PRIMARY KEY CHECK(length(trim(continuity_id)) > 0),
        label_ja TEXT NOT NULL DEFAULT '',
        label_en TEXT NOT NULL DEFAULT '',
        continuity_kind TEXT NOT NULL DEFAULT '',
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE work_continuities (
        work_continuity_id TEXT PRIMARY KEY CHECK(length(trim(work_continuity_id)) > 0),
        work_id TEXT NOT NULL REFERENCES works(work_id),
        continuity_id TEXT NOT NULL REFERENCES continuities(continuity_id),
        relation_to_continuity TEXT NOT NULL DEFAULT '',
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE chronology_assertions (
        chronology_assertion_id TEXT PRIMARY KEY CHECK(length(trim(chronology_assertion_id)) > 0),
        continuity_id TEXT NOT NULL REFERENCES continuities(continuity_id),
        earlier_work_id TEXT NOT NULL REFERENCES works(work_id),
        later_work_id TEXT NOT NULL REFERENCES works(work_id),
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE work_relations (
        work_relation_id TEXT PRIMARY KEY CHECK(length(trim(work_relation_id)) > 0),
        source_work_id TEXT NOT NULL REFERENCES works(work_id),
        target_work_id TEXT NOT NULL REFERENCES works(work_id),
        relation_kind TEXT NOT NULL {_in_check('relation_kind', WORK_RELATION_KINDS)},
        relation_scope TEXT NOT NULL {_in_check('relation_scope', RELATION_SCOPES)},
        directness TEXT NOT NULL {_in_check('directness', DIRECTNESSES)},
        continuity_scope TEXT NOT NULL {_in_check('continuity_scope', CONTINUITY_SCOPES)},
        certainty TEXT NOT NULL {_in_check('certainty', CERTAINTIES)},
        verification_status TEXT NOT NULL {_in_check('verification_status', VERIFICATION_STATUSES)},
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE sources (
        source_id TEXT PRIMARY KEY CHECK(length(trim(source_id)) > 0),
        purpose TEXT NOT NULL DEFAULT '',
        official_source TEXT NOT NULL DEFAULT '',
        checked_point TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL DEFAULT ''
    )
    """,
    f"""
    CREATE TABLE evidence (
        evidence_id TEXT PRIMARY KEY CHECK(length(trim(evidence_id)) > 0),
        fact_table TEXT NOT NULL DEFAULT '',
        fact_id TEXT NOT NULL DEFAULT '',
        source_id TEXT NOT NULL REFERENCES sources(source_id),
        evidence_role TEXT NOT NULL {_in_check('evidence_role', EVIDENCE_ROLES)},
        quoted_or_paraphrased_note TEXT NOT NULL DEFAULT '',
        verified_at TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE reviews (
        review_id TEXT PRIMARY KEY CHECK(length(trim(review_id)) > 0),
        fact_table TEXT NOT NULL DEFAULT '',
        fact_id TEXT NOT NULL DEFAULT '',
        previous_verification_status TEXT NOT NULL DEFAULT '',
        new_verification_status TEXT NOT NULL DEFAULT '',
        review_action TEXT NOT NULL DEFAULT '',
        evidence_ids TEXT NOT NULL DEFAULT '',
        reviewed_at TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT ''
    )
    """,
)


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in DDL:
        connection.execute(statement)
