# Marvel Library DB v1 Phase 2 — Events & Multiverse Implementation Plan

> **Execution:** Implement task-by-task with TDD. Fix discovered canonical defects through evidence-backed review patches; never silently mutate audited facts.

**Goal:** Introduce first-class event and multiverse-transition facts into the Git-auditable Marvel Library canonical model, compile them into SQLite with strong constraints, expose stable public views, and derive work-connection reasons from transition facts without treating work-to-work edges as the semantic source of truth.

**Approved architecture:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`

**Phase 1 baseline:** `docs/superpowers/reviews/2026-08-27-marvel-library-db-v1-phase1-review.md`

## Scope

Phase 2 adds only the fictional-event / multiverse domain required to model cross-universe movement correctly:

- `events.csv`
- `event_occurrences.csv`
- `event_participants.csv`
- `event_relations.csv`
- `multiverse_transitions.csv`
- `transition_participants.csv`

It also extends continuity/entity vocabulary only where required by these facts.

Phase 2 does **not** yet add releases, production status assertions, general credits, memberships, aliases, possessions, or final HTML generation. Those remain separate later phases.

## Non-negotiable constraints

- `main` remains unchanged until explicit merge approval.
- `data/library/**` remains the human-auditable canonical source of truth.
- Ordinary build remains read-only for `data/library/**` and `data/content_audit/reviews.csv`.
- SQLite remains generated query state.
- No Earth number is invented when evidence does not provide one.
- A returning actor does not imply same fictional identity.
- A variant does not imply the original individual crossed universes.
- A work relation is not used as the sole semantic home of a physical universe crossing once a transition fact exists.
- Existing `source_verified` facts are corrected/superseded only through persistent review history.
- New `source_verified` facts require qualifying evidence.
- Counts are observations, never correctness targets.

---

## Task 1 — Extend canonical schema with event/transition tables

**Files**
- Modify `data/library/schema.json`
- Add empty-header canonical CSVs under `data/library/`
- Modify `scripts/library_v5/audit.py`
- Modify `scripts/library_v5/apply_review_patch.py`
- Add `tests/library_v5/test_phase2_event_schema.py`

### RED contract

Require six new canonical tables and exact required columns/FKs.

#### `events.csv`
- `event_id` PK
- `name_ja`
- `name_en`
- `event_kind`
- `primary_continuity_id` nullable FK -> `continuities.continuity_id`
- `certainty`
- `verification_status`
- `notes`

#### `event_occurrences.csv`
- `event_occurrence_id` PK
- `event_id` FK
- `work_id` FK
- `occurrence_kind`
- `certainty`
- `verification_status`
- `notes`

#### `event_participants.csv`
- `event_participant_id` PK
- `event_id` FK
- `entity_id` FK
- `participant_role`
- `certainty`
- `verification_status`
- `notes`

#### `event_relations.csv`
- `event_relation_id` PK
- `source_event_id` FK
- `relation_kind`
- `target_event_id` FK
- `certainty`
- `verification_status`
- `notes`

#### `multiverse_transitions.csv`
- `transition_id` PK and FK -> `events.event_id`
- `source_continuity_id` nullable FK
- `destination_continuity_id` nullable FK
- `transition_kind`
- `direction_certainty`
- `verification_status`
- `notes`

#### `transition_participants.csv`
- `transition_participant_id` PK
- `transition_id` FK -> `multiverse_transitions.transition_id`
- `entity_id` FK
- `participant_role`
- `identity_certainty`
- `verification_status`
- `notes`

Additional required checks:
- `transition_id` must resolve to an `events` row whose `event_kind` is `multiverse_transition`.
- source and destination may be blank; blank means unknown, not “same universe”.
- when both source and destination are nonblank, they must not be identical for `physical_crossing`, `summoning`, `spell_displacement`, or `tva_transfer`.
- `source_verified` rows require evidence like existing auditable fact tables.
- maintenance patches may target all six new canonical tables.

Expected GREEN: existing Phase 1 tests plus new schema/audit tests pass with empty new tables.

---

## Task 2 — Compile Phase 2 semantic tables into SQLite

**Files**
- Modify `scripts/library_v5/db_schema.py`
- Modify `scripts/library_v5/db_compile.py`
- Modify `scripts/library_v5/db_fingerprint.py`
- Add `tests/library_v5/test_phase2_db_compile.py`

### RED contract

- bump DB schema version from `1.0-phase1` to `1.1-phase2-events`;
- load all six new canonical tables;
- enforce PK/FK/CHECK constraints;
- invalid event/transition linkage aborts atomic publish;
- logical fingerprint includes all new tables;
- ordinary build remains canonical/review read-only.

Implement a post-load semantic integrity check for the `events.event_kind='multiverse_transition'` invariant.

---

## Task 3 — Add public event and multiverse SQL views

**Files**
- Modify `scripts/library_v5/db_views.py`
- Modify `scripts/library_v5/db_fingerprint.py`
- Add `tests/library_v5/test_phase2_db_views.py`

### Public views

#### `v_event_history`
One row per occurrence/participant combination with:
- event identity/name/kind
- primary continuity
- containing work
- occurrence kind
- participant entity/role where present
- event/occurrence/participant verification metadata

#### `v_multiverse_crossings`
One row per transition participant, with transitions lacking known participants still represented through a participant-null row in the view.

Columns include:
- `transition_id`
- transition event names
- source continuity id/labels
- destination continuity id/labels
- transition kind
- containing work and occurrence kind
- participant entity id/name/type nullable
- participant role nullable
- identity certainty nullable
- transition/event/occurrence/participant verification metadata

Deterministic ordering and logical fingerprint coverage are mandatory.

---

## Task 4 — Derive work-connection reasons from transition facts

**Files**
- Modify `scripts/library_v5/db_views.py`
- Modify `scripts/library_v5/db_export.py`
- Add `tests/library_v5/test_phase2_transition_edge_reasons.py`

Add a third reason class to `v_work_connection_reasons`: `multiverse_transition`.

Rules:
- A transition occurrence may connect the containing work to another work only through canonical, explainable context.
- The transition reason must preserve `transition_id`, occurrence/event fact IDs, verification states, certainty, source/destination continuity, and participant facts.
- Do not create edges merely because two works share a continuity.
- Do not create an edge from a transition participant to every historical/future appearance of that entity without an explicit derivation rule.
- During pilot migration, preserve current graph compatibility with explicit legacy work relations until each replacement reason is proven equivalent.

The initial derivation rule for Phase 2 is conservative: transition facts generate reason metadata for an already-supported work pair; removal/supersession of redundant explicit work relations happens only in Task 6 after parity review.

---

## Task 5 — Pilot canonical migration: Thunderbolts* F4 ship arrival

**Research/evidence prerequisite:** re-check current official/primary or strong secondary evidence before applying the patch.

**Canonical target model**

- verified `continuity-earth-828` remains F4 origin context;
- verified MCU main/Earth-616 continuity is destination context;
- add a vehicle entity for the Fantastic Four-marked ship only if evidence supports the object identity at that level;
- add event: F4-marked ship arrival;
- occurrence: depicted/post-credit in `thunderbolts-2025`;
- transition: Earth-828 -> MCU main/Earth-616;
- participant: ship as `vehicle`;
- do **not** add Reed/Sue/Johnny/Ben as travelers unless evidence confirms they are aboard;
- keep `First Steps -> Doomsday` explicit `lead_in` relation unchanged;
- supersede the existing `Thunderbolts* -> First Steps` work relation only after DB-derived transition reason reproduces the intended connection without implying that the F4 film itself occurs after Thunderbolts*.

### TDD

Write RED tests for:
- event/transition existence and verification;
- Earth-828 source + Earth-616 destination;
- only confirmed participants recorded;
- `v_multiverse_crossings` row correctness;
- flowchart reason notes explicitly distinguish “post-credit arrival depicted in Thunderbolts*” from film chronology.

Apply via approved content-audit patch, evidence, and reviews; then run full CI.

---

## Task 6 — Pilot canonical migration: No Way Home Raimi/Webb Peter arrivals

**Research/evidence prerequisite:** refresh official Marvel/Sony evidence before patching.

Create separate transition events for:
- Raimi Peter Parker -> MCU main universe;
- Webb Peter Parker -> MCU main universe.

Model each with:
- source continuity only as specifically as existing audited evidence supports;
- destination MCU main/Earth-616;
- occurrence depicted in `spider-man-no-way-home-2021`;
- participant entity corresponding to the specific legacy Spider-Man identity/variant;
- identity certainty that does not collapse Raimi/Webb Peter into MCU Peter.

After transition-view/export parity is proven:
- re-evaluate existing explicit work relations from the Raimi/Webb films to No Way Home;
- if those rows exist solely as proxies for the crossings, supersede them with review history;
- if a row contains an independent editorial/story relation, retain it separately.

Full CI must show no unexplained graph loss.

---

## Task 7 — Second migration batch candidates, one problem at a time

Do not batch-promote automatically. Each case gets evidence refresh, RED test, patch, review, CI.

Priority order:
1. Eddie Brock/Venom Sony universe -> MCU and return.
2. Adrian Toomes Earth-616 -> Sony/Venom/Morbius universe.
3. Monica Rambeau MCU -> unnamed/identified-as-supported alternate universe in `The Marvels`.
4. `Doctor Strange in the Multiverse of Madness` traversals where source/destination can be represented without inventing unsupported continuity IDs.
5. `Deadpool & Wolverine` TVA/multiverse transfers; exact individual continuity must remain uncertain where evidence is insufficient.

A separate continuity may be created for an unnamed destination only when needed as an intentional context node and labeled descriptively, never with an invented Earth number.

---

## Task 8 — Phase 2 completion audit

Create `docs/superpowers/reviews/2026-08-27-marvel-library-db-v1-phase2-events-multiverse-review.md`.

Required verification:
- all tests PASS;
- audit issue count 0;
- canonical/reviews unchanged by ordinary build;
- SQLite FK/integrity checks PASS;
- DB logical fingerprint deterministic;
- `v_event_history` and `v_multiverse_crossings` deterministic;
- graph exporter deterministic;
- every superseded proxy work relation has a replacement semantic reason and review history;
- no transition is inferred from actor reuse alone;
- no variant is incorrectly treated as same individual;
- main remains unchanged.

Review must list migrated and deferred multiverse cases explicitly.

Stop before releases/credits/memberships/possessions/HTML phase unless separately approved.

## Initial implementation boundary

Begin with Tasks 1–4 (infrastructure) before modifying Marvel semantic facts. Then migrate Task 5 and Task 6 independently with fresh evidence and CI between them.
