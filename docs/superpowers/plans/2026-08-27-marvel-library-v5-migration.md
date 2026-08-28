# Marvel Library v5 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, auditable v5 canonical Marvel library from the v5.20.5 data without changing production `main` or treating HTML-specific edges as canonical facts.

**Architecture:** Add a Python-standard-library migration toolchain under `scripts/library_v5/`. Canonical facts live in `data/library/`, generated graph products in `data/derived/`, migration ledgers in `data/migration/`, and flowchart-only policy in `views/flowchart/`. Legacy v4 files remain untouched during migration and are read only as inputs/baselines.

**Tech Stack:** Python 3 standard library (`csv`, `json`, `re`, `hashlib`, `pathlib`, `unittest`), CSV/JSON, GitHub static repository.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-v5-design.md`

## Global Constraints

- Production `main` remains unchanged until migration and audit complete.
- Existing 131 `work_id` values are preserved.
- Legacy HTML `CHAR_LINKS` is migration seed data, not canonical evidence.
- Shared performer identity never implies shared fictional-character identity.
- `data/library/` is human-audited fact storage; `data/derived/` and legacy compatibility exports are generated only.
- No fixed work-edge count (`199`, `416`, or otherwise) is a correctness target.
- Every legacy `connections.csv`, `CHAR_LINKS`, and `entity_returns.csv` row must receive a migration disposition.
- User-facing flowchart lane/region labels remain Japanese; internal stable IDs may be English slugs.
- Implementation is dependency-free and deterministic.

---

### Task 1: Canonical v5 schema and IDs

**Files:**
- Create: `data/library/schema.json`
- Create: `scripts/library_v5/__init__.py`
- Create: `scripts/library_v5/ids.py`
- Create: `tests/library_v5/test_ids_and_schema.py`

**Interfaces:**
- Produces: `slug_id(prefix: str, *parts: str) -> str`
- Produces: canonical table headers/enums in `data/library/schema.json`

- [ ] **Step 1: Write failing tests** asserting deterministic Unicode-to-ASCII-safe stable slugs, prefix preservation, no empty IDs, schema version `5.0`, required tables, and the RDJ/Tony/Doom identity separation fields.
- [ ] **Step 2: Run** `python -m unittest tests.library_v5.test_ids_and_schema -v` and verify failures are caused by missing v5 schema/ID code.
- [ ] **Step 3: Implement** `ids.py` and `data/library/schema.json` minimally to satisfy the tests. IDs must normalize case/whitespace/punctuation deterministically and use a short SHA-256 suffix when normalization would otherwise be empty or ambiguous.
- [ ] **Step 4: Re-run the test module** and verify PASS.
- [ ] **Step 5: Commit** `feat: add library v5 schema and stable ids`.

### Task 2: Legacy seed extraction without treating HTML as evidence

**Files:**
- Create: `scripts/library_v5/extract_legacy.py`
- Create: `tests/library_v5/test_extract_legacy.py`
- Generate: `data/migration/legacy_char_links.csv`
- Generate: `data/migration/legacy_entity_returns.csv`

**Interfaces:**
- Consumes: legacy `index.html`, `data/entity_returns.csv`
- Produces: `extract_char_links(html: str) -> list[dict[str,str]]`
- Produces: `extract_entity_returns(csv_text: str) -> list[dict[str,str]]`

- [ ] **Step 1: Write failing fixture tests** with representative `CHAR_LINKS` JavaScript syntax and an `entity_returns.csv` row. Assert exact extraction, source order preservation, deduplication, and `verification_status=legacy_seed`.
- [ ] **Step 2: Run** `python -m unittest tests.library_v5.test_extract_legacy -v` and verify RED.
- [ ] **Step 3: Implement** a narrow parser for the existing v5.20.5 `CHAR_LINKS` structure. It must reject malformed/unknown structures instead of guessing.
- [ ] **Step 4: Generate migration seed CSVs** from the pinned v5.20.5 inputs; do not modify legacy inputs.
- [ ] **Step 5: Test** extraction and assert generated row counts are recorded in a machine-readable summary rather than hard-coded as future correctness targets.
- [ ] **Step 6: Commit** `feat: extract legacy character and return seeds`.

### Task 3: Normalize legacy entities, appearances, people, portrayals, and evidence

**Files:**
- Create: `scripts/library_v5/migrate_entities.py`
- Create: `tests/library_v5/test_migrate_entities.py`
- Generate: `data/library/entities.csv`
- Generate: `data/library/appearances.csv`
- Generate: `data/library/people.csv`
- Generate: `data/library/portrayals.csv`
- Generate: `data/library/entity_relations.csv`
- Generate: `data/library/evidence.csv`
- Generate: `data/migration/entity_seed_dispositions.csv`

**Interfaces:**
- Consumes: Task 2 seed rows and existing `data/sources.csv`
- Produces: normalized canonical fact rows plus one disposition row per legacy seed

- [ ] **Step 1: Write failing tests** for duplicate appearance collapse, variant distinction, actor reuse, and one-to-many evidence links. Include explicit regression: Robert Downey Jr. portraying Tony Stark in an earlier work and Doctor Doom in Doomsday must create two portrayal facts but no `identity_of` entity relation.
- [ ] **Step 2: Run tests** and verify RED for missing migration behavior.
- [ ] **Step 3: Implement** normalization and deterministic IDs. `legacy_seed` stays unverified until an independent evidence row exists.
- [ ] **Step 4: Generate** canonical seed tables and disposition ledger.
- [ ] **Step 5: Verify** every extracted `CHAR_LINKS` and `entity_returns` row has exactly one disposition.
- [ ] **Step 6: Commit** `feat: normalize legacy entity facts`.

### Task 4: Migrate works and classify all legacy connections

**Files:**
- Create: `scripts/library_v5/migrate_works_relations.py`
- Create: `tests/library_v5/test_migrate_work_relations.py`
- Generate: `data/library/works.csv`
- Generate: `data/library/work_relations.csv`
- Generate: `data/library/continuities.csv`
- Generate: `data/library/work_continuities.csv`
- Generate: `data/library/chronology_assertions.csv`
- Generate: `data/migration/connection_dispositions.csv`
- Generate: `data/migration/chronology_dispositions.csv`

**Interfaces:**
- Consumes: legacy `works.csv`, `connections.csv`, `chronology.csv`, schema enums
- Produces: preserved work facts, explicit work relations only, and a disposition for every legacy connection

- [ ] **Step 1: Write failing tests** for preserving all work IDs, classifying a direct sequel as explicit relation, classifying a pure shared-character proxy as appearance-derived, separating promotional/prewatch policy, and recording invalid/superseded rows without silent deletion.
- [ ] **Step 2: Run tests** and verify RED.
- [ ] **Step 3: Implement** deterministic migration classification using explicit legacy fields (`relation_scope`, `relation_kind`, `directness`, `continuity_scope`, promotion flags) plus a small documented override table for ambiguous legacy cases. Do not infer content from titles.
- [ ] **Step 4: Generate** v5 work/relation/continuity tables and ledgers from the pinned v5.20.5 inputs.
- [ ] **Step 5: Assert** exactly every legacy connection row has one disposition; the numeric legacy count is reported from input rather than baked into the canonical schema.
- [ ] **Step 6: Commit** `feat: migrate works and explicit relations`.

### Task 5: Deterministic reason and edge derivation

**Files:**
- Create: `scripts/library_v5/derive_edges.py`
- Create: `tests/library_v5/test_derive_edges.py`
- Generate: `data/derived/work_pair_reasons.csv`
- Generate: `data/derived/work_edges_all.csv`

**Interfaces:**
- Produces: `derive_reasons(works, appearances, explicit_relations, entity_relations, mode) -> list[dict]`
- Produces modes: `all_pairs`, `adjacent_release`, `target_centric`, `explicit_only`, and deterministic combined mode

- [ ] **Step 1: Write failing tests** with A/B/C/D appearances for one entity. Assert `all_pairs` yields all six unordered work pairs, `adjacent_release` yields three adjacent pairs, explicit relation reasons coexist with shared-character reasons, and different source works entering one target are never silently merged.
- [ ] **Step 2: Add regression tests** that same performer/different entity yields no character reason and variants only connect when `entity_relations.csv` permits the selected derivation policy.
- [ ] **Step 3: Run tests** and verify RED.
- [ ] **Step 4: Implement** derivation with stable reason IDs, deterministic sort order, complete reason retention, and edge-level reason lists.
- [ ] **Step 5: Generate** derived CSVs and verify a second clean generation is byte-identical.
- [ ] **Step 6: Commit** `feat: derive complete work relation graph`.

### Task 6: Legacy story/prewatch compatibility as generated products

**Files:**
- Create: `scripts/library_v5/derive_compat.py`
- Create: `tests/library_v5/test_derive_compat.py`
- Generate: `data/derived/story_paths.csv`
- Generate: `data/derived/prewatch_edges.csv`
- Generate: `data/migration/story_path_dispositions.csv`
- Create: `views/flowchart/README.md`
- Create: `views/flowchart/policy.json`

**Interfaces:**
- Consumes: canonical/derived facts plus existing prewatch policy and legacy story path baseline
- Produces: compatibility/regression exports without making view policy canonical facts

- [ ] **Step 1: Write failing tests** that all legacy story-path rows are either reproduced or receive an explicit changed/corrected disposition, and that prewatch tier is derived policy rather than stored on appearance facts.
- [ ] **Step 2: Run tests** and verify RED.
- [ ] **Step 3: Implement** generated compatibility exports and a minimal flowchart view policy containing Japanese user-facing label requirements and edge display modes only.
- [ ] **Step 4: Generate** compatibility files and dispositions.
- [ ] **Step 5: Commit** `feat: derive story and prewatch compatibility views`.

### Task 7: Repository-wide v5 audit and deterministic manifest

**Files:**
- Create: `scripts/library_v5/audit.py`
- Create: `scripts/library_v5/build.py`
- Create: `tests/library_v5/test_audit.py`
- Generate: `data/library/manifest.json`
- Generate: `data/migration/MIGRATION_AUDIT.md`
- Generate: `data/migration/audit.json`

**Interfaces:**
- Produces: one-command `python -m scripts.library_v5.build --repo-root .`
- Produces nonzero exit on schema/FK/coverage/determinism failure

- [ ] **Step 1: Write failing audit tests** for broken FKs, duplicate fact IDs, missing evidence state, missing migration disposition, actor-character false inference, and nondeterministic ordering.
- [ ] **Step 2: Run tests** and verify RED.
- [ ] **Step 3: Implement** full audit and manifest SHA-256 generation.
- [ ] **Step 4: Run** complete test suite and build twice from a clean generated-output state; compare SHA-256 manifests byte-for-byte.
- [ ] **Step 5: Confirm** production `main` still points to `3af097b72c174077c83d7091f79222a72fc7134f`.
- [ ] **Step 6: Commit** `test: audit library v5 migration determinism`.

### Task 8: Migration review checkpoint

**Files:**
- Update: `data/migration/MIGRATION_AUDIT.md`
- Update: `docs/superpowers/specs/2026-08-27-marvel-library-v5-design.md` only if implementation reveals a necessary clarification; no silent spec drift.

**Interfaces:**
- Produces: reviewable migration branch; no merge to `main`

- [ ] **Step 1: Review** every migration ledger for unresolved/ambiguous rows and list them explicitly.
- [ ] **Step 2: Review** generated counts as observations only, not correctness gates.
- [ ] **Step 3: Verify** the new canonical library can generate an all-relations work graph without reading `index.html` after migration output exists.
- [ ] **Step 4: Run final verification** using the verification-before-completion skill.
- [ ] **Step 5: Stop before merge** and present branch/audit results for user approval. Do not update production `main` in this task.
