# Marvel Library DB v1 Design

## Status

- Date: 2026-08-27
- Working branch: `library-v5-canonical-freeze`
- Production baseline remains `main` at `3af097b72c174077c83d7091f79222a72fc7134f` (`v5.20.5`).
- Depends on:
  - `docs/superpowers/specs/2026-08-27-marvel-library-v5-design.md`
  - `docs/superpowers/specs/2026-08-27-marvel-library-v5-canonical-bootstrap-separation-design.md`
- Decision: evolve the project from a flowchart-oriented dataset into a reusable Marvel audiovisual works library whose canonical facts compile into SQLite, and generate the flowchart/HTML as one downstream view.
- Production `main` remains unchanged until explicit integration approval.

## 1. Goal

Build a durable, queryable Marvel audiovisual works database that can answer questions from multiple perspectives without encoding those answers as hand-maintained flowchart edges.

The project architecture becomes:

```text
Git-auditable canonical facts
        ↓
validate / compile
        ↓
Marvel SQLite database
        ↓
SQL views + deterministic derivation
        ↓
JSON / graph products / reports
        ↓
static HTML viewer on GitHub Pages
```

The database is a **compiled query layer**, not the Git source of truth. Human-audited facts remain stored as diff-friendly text files under `data/library/` and persistent audit records under `data/content_audit/`.

The HTML flowchart must stop being a place where facts exist independently. It becomes one consumer of the library.

## 2. Core principles

### 2.1 Canonical text, compiled database

`data/library/` remains canonical. SQLite is rebuilt from canonical text input.

Reasons:

- Git diffs remain human-readable;
- evidence and audit decisions are reviewable line by line;
- accidental database binary rewrites do not obscure factual changes;
- the database can be deleted and rebuilt without losing knowledge;
- CI can compare stable schema/data fingerprints and query outputs against canonical hashes.

The generated SQLite file must never be edited as the authoritative source.

### 2.2 One fact, one semantic home

Facts are stored in the table matching what actually happened.

Examples:

- “First Steps is set on Earth-828” → continuity membership;
- “the Fantastic Four ship travels from Earth-828 to Earth-616” → multiverse transition;
- “the ship's arrival is shown in Thunderbolts*” → event occurrence;
- “First Steps directly leads into Doomsday” → explicit work relation;
- “Michael Keaton plays Adrian Toomes in Homecoming and Morbius” → portrayal facts;
- “Adrian Toomes is the same individual after crossing universes” → same entity ID across appearances, supported by evidence.

No one `work_relations` row should be forced to carry all of those meanings.

### 2.3 Derived edges are views, not canonical facts

A rendered line may be derived from explicit work relations, shared entity appearances, universe transitions, shared/causal events, organization membership, artifact transfer/ownership, or verified production/meta relations when a view requests them.

The reason list remains available so the UI can explain **why** a line exists.

### 2.4 Fictional-world facts and production/meta facts are separate domains

The same library contains both, but they must not be conflated.

A cast announcement must never imply character identity unless a portrayal/role fact separately supports it. A franchise label must never imply same-universe continuity. A returning actor must never imply that the same fictional individual crossed universes.

## 3. Repository layers

### 3.1 Canonical facts — `data/library/`

Human-audited fact tables. Ordinary build is read-only with respect to this directory.

### 3.2 Persistent content audit — `data/content_audit/`

Review history and approved/pending canonical patches. `reviews.csv` is persistent input. Generated queues/reports are derived.

### 3.3 Compiled database — `data/derived/db/marvel.sqlite`

Generated from canonical facts. Safe to delete and rebuild. Not authoritative.

The SQLite binary does **not** need to be byte-identical across environments. Determinism is measured by canonical input hashes, schema version, ordered logical table contents, versioned view outputs, and a stable logical database fingerprint. CI may store the binary as an artifact rather than commit it.

Every HTML/data export must be produced by querying the compiled database rather than re-implementing canonical joins independently in the HTML generator.

### 3.4 Derived exports — `data/derived/`

Generated graph edges, reason tables, prewatch data, chronology views, audit summaries, database fingerprints, and static JSON payloads.

### 3.5 Flowchart view configuration — `views/flowchart/`

Presentation policy only: lanes, labels, line strength, glow, dimming, filters, layout, route geometry, mobile behavior.

## 4. Database domains and canonical tables

DB v1 uses practical normalized domain tables rather than one generic subject-predicate-object table.

### 4.1 Works and release/production metadata

#### `works`

Existing stable `work_id` remains the primary key. It stores work identity and core audiovisual metadata, not layout placement.

#### `releases`

One work may have multiple release facts.

Fields:

- `release_id` PK
- `work_id` FK
- `territory`
- `release_kind` (`theatrical`, `streaming`, `broadcast`, `festival`, `re_release`, etc.)
- `release_date`
- `status`
- `certainty`
- `verification_status`
- `notes`

This separates Japanese release date, US release date, streaming date, and rerelease.

#### `production_status_assertions`

Auditable time-stamped production/release status assertions such as announced, filming, completed, delayed, cancelled, and released. Historical assertions are retained instead of overwritten.

### 4.2 Real-world people and credits

#### `people`

Existing real-person registry.

#### `credits`

General real-world credits not limited to acting.

Fields:

- `credit_id` PK
- `work_id` FK
- `person_id` FK
- `credit_kind` (`director`, `writer`, `producer`, `composer`, `cast_announced`, etc.)
- `credit_detail`
- `certainty`
- `verification_status`
- `notes`

A cast announcement with an unknown role can be stored here without inventing a character identity.

#### `portrayals`

Acting-specific bridge between real people and fictional entities. A role with insufficient evidence may keep `entity_id` null/unknown according to the existing unknown-role rule.

### 4.3 Fictional entities and identity

#### `entities`

One row per fictional entity identity.

Initial entity types:

- `character`
- `organization`
- `artifact`
- `place`
- `species`
- `vehicle`
- `abstract_concept`

`event` is removed from the long-term entity taxonomy because events become first-class rows in `events`. Existing migrated event-like entities are superseded through a migration ledger rather than silently deleted.

#### `entity_aliases`

Names are separated from identity.

Fields:

- `entity_alias_id` PK
- `entity_id` FK
- `alias`
- `language`
- `alias_kind` (`name`, `title`, `mantle`, `codename`, `legacy_label`)
- `validity_notes`

This allows Frank Castle / Punisher, localized names, and mantles to be indexed without duplicate identities.

#### `entity_relations`

Identity-oriented entity relations:

- `identity_of`
- `variant_of`
- `successor_identity_of`
- `clone_of`
- `alternate_form_of`

Existing legacy alias entities may continue to resolve through `identity_of` during migration. New simple aliases should normally use `entity_aliases`, not create new entities.

### 4.4 Appearances and fictional participation

#### `appearances`

Canonical work × entity appearance facts.

Appearance kind remains explicit: onscreen, voice, post-credit, archive, mention, recording/photo, unknown.

An appearance does not itself assert same-universe continuity.

#### `entity_memberships`

Tracks membership/affiliation such as Avengers, Thunderbolts/New Avengers, TVA, X-Men, Illuminati, and organizations/institutions.

Fields:

- `membership_id` PK
- `member_entity_id` FK
- `group_entity_id` FK
- optional `work_id` FK
- optional `event_id` FK
- `membership_kind`
- `certainty`
- `verification_status`
- `notes`

Membership does not automatically create work edges unless a derived view requests that semantic relation.

### 4.5 Continuities, universes, timelines

#### `continuities`

One row per named or intentionally unnamed continuity context.

Examples include MCU main universe, Earth-828, Earth-838, Raimi Spider-Man universe, Webb Spider-Man universe, Sony/Venom/Morbius universe, TVA/outside-timeline context, and explicitly unresolved legacy-return contexts.

A continuity is named only as specifically as evidence supports. Unknown Earth numbers are not invented.

#### `work_continuities`

Maps works to primary/depicted continuity contexts. Marvel Studios/MCU franchise inclusion is not sufficient to assert same-universe membership.

#### `chronology_assertions`

Source-backed relative ordering. Layout order remains separate.

### 4.6 Events

#### `events`

First-class fictional events.

Fields:

- `event_id` PK
- `name_ja`
- `name_en`
- `event_kind`
- optional `primary_continuity_id` FK
- `certainty`
- `verification_status`
- `notes`

Examples include Battle of New York, Blip-related events, Battle of Earth, Westview Hex, incursions, TVA interventions, and the Thunderbolts* post-credit Fantastic Four ship arrival.

#### `event_occurrences`

Links an event to the work in which it is depicted, referenced, caused, or revisited.

Fields:

- `event_occurrence_id` PK
- `event_id` FK
- `work_id` FK
- `occurrence_kind` (`depicted`, `post_credit`, `referenced`, `flashback`, `caused`, `aftermath`)
- `certainty`
- `verification_status`
- `notes`

The containing work is therefore not confused with the event itself.

#### `event_participants`

Links fictional entities to events, with participant role, certainty, verification status, and notes.

#### `event_relations`

Typed event-to-event relations such as `causes`, `enables`, `prevents`, `aftermath_of`, `part_of`, and `precedes`.

### 4.7 Multiverse transitions

A universe crossing is modeled as a specialized event, not fundamentally as a work-to-work edge.

#### `multiverse_transitions`

One-to-one specialized data for an `events` row whose `event_kind` is a multiverse transition.

Fields:

- `transition_id` PK and FK to `events.event_id`
- optional `source_continuity_id` FK
- optional `destination_continuity_id` FK
- `transition_kind` (`physical_crossing`, `summoning`, `portal`, `spell_displacement`, `tva_transfer`, `incursion_contact`, `universe_exchange`, `unknown`)
- `direction_certainty`
- `verification_status`
- `notes`

The containing work is obtained through `event_occurrences`; it is not duplicated in this table.

#### `transition_participants`

Many-to-many transition traveler/subject facts.

Fields:

- `transition_participant_id` PK
- `transition_id` FK
- `entity_id` FK
- `participant_role` (`traveler`, `vehicle`, `summoner`, `carrier`, `affected`, etc.)
- `identity_certainty` — certainty that this is the same individual/object rather than a variant
- `verification_status`
- `notes`

This avoids creating multiple duplicated transition rows when a team, several characters, or a vehicle carrying characters crosses universes together.

Unknown source/destination is allowed and stays null rather than receiving an invented universe number.

Examples the model must represent cleanly:

- Raimi Peter Parker → MCU main universe in No Way Home;
- Webb Peter Parker → MCU main universe in No Way Home;
- Eddie Brock/Venom → MCU and back in the Let There Be Carnage / No Way Home sequence;
- Adrian Toomes → Sony/Venom/Morbius universe after No Way Home events;
- Monica Rambeau → an alternate universe in The Marvels;
- Doctor Strange/America Chavez traversing multiple universes in Multiverse of Madness;
- Wade Wilson and other travelers moved through TVA/multiverse mechanisms in Deadpool & Wolverine;
- the Earth-828 Fantastic Four-marked ship arriving in Earth-616 in Thunderbolts*.

A transition may generate one or more derived work connections, but the canonical fact remains the transition/event.

### 4.8 Artifacts, possession, and transfer

#### `entity_possessions`

Tracks possession/custody/use of artifacts or other transferable fictional entities such as Captain America's shield, Mjolnir, Infinity Stones, and Ten Rings.

Fields:

- `possession_id` PK
- `holder_entity_id` FK
- `held_entity_id` FK
- optional `work_id` FK
- optional `event_id` FK
- `possession_kind`
- `certainty`
- `verification_status`
- `notes`

### 4.9 Explicit work relations

#### `work_relations`

Retained but narrowed to relations inherently between works or explicit editorial/story relationships that cannot be reduced to primitive facts.

Good uses:

- direct sequel
- spinoff
- explicitly stated lead-in
- explicit aftermath
- explicit story trilogy/order
- official promotion association as a production/meta fact

Not appropriate as sole storage for:

- a shared character appearance;
- a person/object crossing universes;
- actor reuse;
- artifact possession/transfer;
- two works depicting the same event.

### 4.10 Evidence and review

#### `sources`
#### `evidence`
#### `reviews`

Existing evidence model remains normative. Every `source_verified` auditable fact requires qualifying evidence. Conflicting evidence remains recorded. Review history is retained when facts are superseded.

## 5. SQLite schema and constraints

The SQLite compiler creates tables mirroring the canonical semantic model and applies stronger runtime constraints than CSV alone can express.

Required controls include:

- PK uniqueness;
- `PRAGMA foreign_keys = ON`;
- stable enum-style `CHECK` constraints where appropriate;
- non-empty stable IDs;
- safe semantic uniqueness constraints;
- source-verified fact/evidence integrity before DB publication;
- no dangling appearance, portrayal, continuity, event, transition, participant, or evidence references.

The compiler fails rather than partially publishing a broken DB.

## 6. Logical database fingerprint

DB reproducibility is defined semantically, not by raw `.sqlite` bytes.

The compiler produces `data/derived/db/library_db_manifest.json` containing:

- canonical input SHA-256 hashes;
- DB schema version;
- normalized SQL schema hash;
- ordered row count and content hash for every table;
- ordered content hash for every versioned public view;
- SQLite version as diagnostic metadata, not as a correctness key.

Two builds from identical canonical facts are equivalent when these logical fingerprints match. Raw SQLite byte equality is not required because page layout and environment details may differ without changing database meaning.

## 7. SQL views as the public query contract

Consumers should prefer named versioned views over hard-coded joins.

Initial DB v1 views:

### `v_work_connections_all`

One logical work pair per connection with aggregated reasons.

### `v_work_connection_reasons`

One row per reason supporting a work pair, preserving source fact IDs, verification status, certainty, and reason type.

### `v_entity_work_history`

Works for an entity with appearance kind, continuity context, portrayal data when available, and verification state.

### `v_multiverse_crossings`

Source/destination continuity, transition event, containing work(s), participants/travelers, identity certainty, and evidence status.

### `v_continuity_works`

Works/events associated with each continuity context.

### `v_event_history`

Event occurrences, participants, causes/aftermath links, and associated works.

### `v_prewatch_candidates`

Input view for the existing policy engine. Final prewatch remains derived policy, not canonical fact.

### `v_flowchart_nodes`

Work metadata needed by the HTML generator, excluding layout coordinates.

### `v_flowchart_edge_candidates`

All candidate physical work edges with reason summaries and verification/strength inputs. Visibility and visual strength remain view policy decisions.

These views are the database-facing interface for downstream exporters.

## 8. HTML generation boundary

GitHub Pages remains static. The browser does not require a live server DB.

```text
data/library + data/content_audit
          ↓
validate
          ↓
compile marvel.sqlite
          ↓
query versioned SQL views
          ↓
export compact static JSON
          ↓
generate/assemble index.html
```

The HTML must not contain manually maintained fact arrays such as legacy `CHAR_LINKS`.

Browser payloads contain only data required for interaction. Large evidence/source payloads may later be split into lazy-load JSON.

SQLite-in-browser/WASM is out of scope for DB v1 because it adds runtime weight without improving canonical correctness.

## 9. Derived edge policy

The database exposes what relationships can be derived, not how strongly the UI must show them.

Every edge reason carries source fact IDs, reason type, verification state, certainty, and continuity/variant interpretation.

Examples:

- verified explicit lead-in → strong candidate;
- confirmed same-individual multiverse transition → strong crossover candidate;
- shared canonical character identity → character-continuity candidate;
- same actor playing variants → variant/meta candidate, never same-character by default;
- unresolved legacy return identity → available but uncertain candidate.

Final opacity/glow/bundling remains `views/flowchart/` policy.

## 10. Migration from current Library v5

Migration is incremental and preserves current audited work.

### Phase 1 — DB compiler without semantic rewrite

- create SQLite schema matching existing canonical tables;
- load canonical facts read-only;
- reproduce the current derived graph through SQL views;
- prove logical DB fingerprint determinism;
- keep the existing derived builder only as a regression oracle.

No content facts change merely because DB v1 exists.

### Phase 2 — normalized canonical tables

Introduce with tests:

- `releases`
- `production_status_assertions`
- `credits`
- `entity_aliases`
- `entity_memberships`
- `events`
- `event_occurrences`
- `event_participants`
- `event_relations`
- `multiverse_transitions`
- `transition_participants`
- `entity_possessions`

Existing data moves only when the new table is semantically better. A migration ledger records each moved/superseded representation.

### Phase 3 — multiverse audit decomposition

Audited multiverse work relations are decomposed where appropriate.

For example, Thunderbolts* → First Steps may remain as a useful derived/display connection, while the canonical underlying crossing is an event/transition describing the Earth-828 Fantastic Four-marked ship arriving in Earth-616.

The explicit First Steps → Doomsday lead-in remains `work_relations` because it is inherently a source-backed work-to-work relation.

### Phase 4 — HTML switches to DB exports

- generate node JSON from `v_flowchart_nodes`;
- generate edge/reason JSON from `v_flowchart_edge_candidates` plus view policy;
- remove independent Marvel fact arrays from HTML;
- compare selected-path/prewatch behavior against existing implementation;
- preserve Pixel 6/mobile performance requirements.

### Phase 5 — broader content audit

Continue the 131-work audit using the richer semantic model. New facts enter their correct domain table rather than creating ad hoc edges.

## 11. Backward compatibility and main safety

- `main` remains unchanged during DB design/experimental migration.
- Existing stable `work_id` values remain stable.
- Existing audited fact IDs remain stable unless explicitly superseded through migration records.
- Old derived files may temporarily remain as regression outputs, not competing canonical sources.
- No fixed edge count is a correctness target.
- Static GitHub Pages deployment remains viable throughout migration.

## 12. Testing requirements

DB v1 implementation must use TDD and cover:

1. identical canonical input producing identical logical DB fingerprints and public-view outputs;
2. FK and CHECK enforcement;
3. canonical SHA immutability during ordinary build;
4. SQL view contract stability;
5. parity of existing audited relations before semantic migration;
6. multiverse transition derivation without false same-universe membership;
7. multiple transition participants without duplicated transition identity;
8. same actor / different entity never producing same-character continuity;
9. same individual moving between universes preserving identity only when evidence supports it;
10. unknown source/destination continuity staying null rather than fabricated;
11. HTML export containing no manual canonical fact arrays;
12. deterministic generated JSON;
13. Pixel-6-oriented static payload/performance regression checks when HTML generation switches.

## 13. Success criteria

DB v1 succeeds when:

- SQLite can be rebuilt from Git canonical facts with the same logical fingerprint;
- ordinary build never mutates canonical input;
- `index.html` no longer owns independent Marvel facts;
- HTML graph data comes through versioned DB views/exports;
- multiverse crossings are queryable independently from work-to-work relations;
- fictional identity, actor identity, continuity, events, production metadata, and evidence remain distinct;
- existing audited facts/IDs survive without silent loss;
- a reviewer can trace “why is this line here?” from derived edge → DB reason row → canonical fact → evidence;
- future views can be added without changing canonical facts solely for presentation.

## 14. Explicit non-goals for DB v1

DB v1 does not attempt to:

- model all Marvel Comics continuities;
- become a public writable server database;
- add user accounts or collaborative editing;
- run SQL directly in the browser;
- redesign the flowchart UI in the same step;
- infer unsupported Earth numbers or exact return identities;
- normalize every imaginable fictional relationship before a concrete query/use case exists.

The design intentionally prefers a normalized but practical audiovisual-works library over a fully generic knowledge graph.
