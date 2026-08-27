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

`data/library/` remains canonical. SQLite is rebuilt deterministically from canonical text input.

Reasons:

- Git diffs remain human-readable;
- evidence and audit decisions are reviewable line by line;
- accidental database binary rewrites do not obscure factual changes;
- the database can be deleted and rebuilt without losing knowledge;
- CI can compare deterministic database/query outputs against canonical hashes.

The generated SQLite file must never be edited as the authoritative source.

### 2.2 One fact, one semantic home

Facts are stored in the table matching what actually happened.

Examples:

- “First Steps is set on Earth-828” → continuity membership;
- “the Fantastic Four ship travels from Earth-828 to Earth-616” → multiverse transition;
- “the ship's arrival is shown in Thunderbolts*” → transition occurrence in a containing work/event;
- “First Steps directly leads into Doomsday” → explicit work relation;
- “Michael Keaton plays Adrian Toomes in Homecoming and Morbius” → portrayal facts;
- “Adrian Toomes is the same individual after crossing universes” → same entity ID across appearances, supported by evidence.

No one `work_relations` row should be forced to carry all of those meanings.

### 2.3 Derived edges are views, not canonical facts

A rendered line may be derived from:

- explicit work relations;
- shared entity appearances;
- an entity moving between universes;
- a shared event or causal event relation;
- organization membership;
- artifact transfer/ownership;
- a verified production/meta relation when the selected view requests it.

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

The implementation may avoid committing the SQLite binary if binary churn is undesirable; CI may create it as an artifact. The semantic requirement is that every HTML/data export is produced by querying this compiled database rather than directly re-implementing joins over canonical CSV in the HTML generator.

### 3.4 Derived exports — `data/derived/`

Generated graph edges, reason tables, prewatch data, chronology views, audit summaries, and static JSON payloads.

### 3.5 Flowchart view configuration — `views/flowchart/`

Presentation policy only: lanes, labels, line strength, glow, dimming, filters, layout, route geometry, mobile behavior.

## 4. Database domains and canonical tables

DB v1 is organized by domain rather than by one giant generic triple table.

### 4.1 Works and release/production metadata

#### `works`

Existing stable `work_id` remains the primary key.

Core fields include titles, format/type, franchise/label metadata that is factual rather than layout-specific, and stable identifiers.

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

This avoids collapsing Japanese release date, US release date, streaming date, and rerelease into one work field.

#### `production_status_assertions`

Tracks current production/release status as auditable assertions rather than overwriting history.

Examples: announced, filming, completed, delayed, cancelled, released.

Fields include assertion ID, work ID, status, effective/checked date, certainty, verification status, and notes.

### 4.2 Real-world people and credits

#### `people`

Existing performer/person registry.

#### `credits`

General real-world credits not limited to acting.

Fields:

- `credit_id` PK
- `work_id` FK
- `person_id` FK
- `credit_kind` (`director`, `writer`, `producer`, `composer`, etc.)
- `credit_detail`
- `certainty`
- `verification_status`
- `notes`

#### `portrayals`

Retained as the acting-specific bridge between real people and fictional entities.

A person appearing in a cast announcement with an unknown role may exist as a person/cast credit while `entity_id` remains unset until role evidence exists.

### 4.3 Fictional entities and identity

#### `entities`

One row per fictional entity identity.

Initial entity types:

- character
- organization
- artifact
- place
- species
- vehicle
- abstract_concept

`event` is removed from the long-term entity taxonomy because events become first-class rows in `events`.

#### `entity_aliases`

Names are separated from identity.

Fields:

- `entity_alias_id` PK
- `entity_id` FK
- `alias`
- `language`
- `alias_kind` (`name`, `title`, `mantle`, `codename`, `legacy_label`)
- `validity_notes`

This allows “Frank Castle”, “Punisher”, localized names, and mantles to be indexed without creating duplicate entities.

#### `entity_relations`

Typed relationships between entity identities.

Identity-oriented kinds include:

- `identity_of`
- `variant_of`
- `successor_identity_of`
- `clone_of`
- `alternate_form_of`

Social/organizational relationships that need temporal/event context should normally use dedicated membership/relationship tables rather than overloading identity relations.

### 4.4 Appearances and fictional participation

#### `appearances`

Canonical work × entity appearance facts.

Appearance kind remains explicit: onscreen, voice, post-credit, archive, mention, recording/photo, unknown.

An appearance does not by itself say whether the entity belongs to the same universe as another appearance. Continuity membership and transitions provide that context.

#### `entity_memberships`

Tracks fictional membership/affiliation such as Avengers, Thunderbolts/New Avengers, TVA, X-Men, Illuminati, Wakandan institutions, etc.

Fields:

- `membership_id` PK
- `member_entity_id` FK
- `group_entity_id` FK
- optional `work_id` FK or `event_id` FK giving observation/context
- `membership_kind`
- `certainty`
- `verification_status`
- `notes`

Membership must not automatically create a work-to-work edge unless a derived view explicitly asks for that relation.

### 4.5 Continuities, universes, timelines

#### `continuities`

One row per named or intentionally unnamed continuity context.

Examples include Earth-616/MCU main universe, Earth-828, Earth-838, Raimi Spider-Man universe, Webb Spider-Man universe, a Sony/Venom/Morbius universe, TVA/outside-timeline context, and explicitly unresolved legacy return buckets.

A continuity row may be named only as specifically as evidence supports. Unknown universe numbers are not invented.

#### `work_continuities`

Maps works to their primary/depicted continuity context.

A franchise being produced by Marvel Studios is not sufficient to assert `same universe` membership.

#### `chronology_assertions`

Retained for source-backed relative ordering. Layout order is not chronology.

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

Examples:

- Battle of New York
- Blip / Snap-related events
- Battle of Earth
- Westview Hex
- universe-incursion events
- TVA pruning/intervention events
- the Thunderbolts* post-credit F4 ship arrival

#### `event_occurrences`

Links an event to the work in which it is depicted, referenced, or caused.

Fields:

- `event_occurrence_id` PK
- `event_id` FK
- `work_id` FK
- `occurrence_kind` (`depicted`, `post_credit`, `referenced`, `flashback`, `caused`, `aftermath`)
- `certainty`
- `verification_status`
- `notes`

This prevents the containing work from being confused with the event itself.

#### `event_participants`

Links fictional entities to events.

Fields include event, entity, participant role, certainty, verification status, notes.

#### `event_relations`

Typed event-to-event causal or temporal relations.

Initial kinds:

- `causes`
- `enables`
- `prevents`
- `aftermath_of`
- `part_of`
- `precedes`

This supports event-level causal queries without inventing work edges.

### 4.7 Multiverse transitions

#### `multiverse_transitions`

This is a required DB v1 table, introduced because a universe crossing is not fundamentally a work-to-work relation.

Fields:

- `transition_id` PK
- `containing_work_id` FK — work in which the transition is depicted/revealed
- optional `event_id` FK — associated event when modeled
- `traveler_entity_id` FK — character, object, vehicle, organization proxy, etc.
- optional `source_continuity_id` FK
- optional `destination_continuity_id` FK
- `transition_kind` (`physical_crossing`, `summoning`, `portal`, `spell_displacement`, `tva_transfer`, `incursion_contact`, `universe_exchange`, `unknown`)
- `direction_certainty`
- `identity_certainty` — certainty that the traveler is the same individual/object rather than a variant
- `verification_status`
- `notes`

Unknown source/destination is allowed. Unknown facts stay null rather than receiving invented Earth numbers.

Examples the model must represent cleanly:

- Raimi Peter Parker → MCU main universe in No Way Home;
- Webb Peter Parker → MCU main universe in No Way Home;
- Eddie Brock/Venom → MCU and return in the No Way Home/Let There Be Carnage crossover sequence;
- Adrian Toomes → Sony/Venom/Morbius universe after No Way Home events;
- Monica Rambeau → an alternate universe in The Marvels;
- Doctor Strange/America Chavez traversing multiple universes in Multiverse of Madness;
- Wade Wilson moving via TVA/multiverse mechanisms in Deadpool & Wolverine;
- Earth-828 Fantastic Four-marked ship arriving in Earth-616 in Thunderbolts*.

A transition may create a derived work connection, but the canonical fact remains the transition itself.

### 4.8 Artifacts, possession, and transfer

#### `entity_possessions`

Tracks possession/custody/use of artifacts or other entities.

Examples: Captain America's shield, Mjolnir, Infinity Stones, Ten Rings.

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

This allows succession/transfer queries without encoding them as work relations.

### 4.9 Explicit work relations

#### `work_relations`

Retained, but narrowed.

Use it only when the relation is inherently between works or is an explicit editorial/story relationship that cannot be reduced to more primitive facts.

Good examples:

- direct sequel
- spinoff
- explicitly stated direct lead-in
- explicit aftermath relationship
- explicit story trilogy membership/order when source-backed
- official promotion association as a production/meta fact

Not appropriate as sole storage for:

- a character merely appearing in both works;
- a person/object crossing universes;
- actor reuse;
- an artifact passing between characters;
- two works depicting the same event.

### 4.10 Evidence and review

#### `sources`
#### `evidence`
#### `reviews`

Existing evidence model remains normative.

Every `source_verified` auditable fact requires qualifying evidence. Contradictory evidence remains recorded. Review history is not deleted when a fact is superseded.

## 5. SQLite schema and constraints

The SQLite compiler creates tables mirroring the canonical semantic model and applies stronger runtime constraints than CSV alone can express.

Required constraints include:

- primary-key uniqueness;
- foreign keys enabled with `PRAGMA foreign_keys = ON`;
- enum-style `CHECK` constraints where stable;
- non-empty stable IDs;
- uniqueness for semantically duplicate facts where safe;
- source-verified fact/evidence integrity checked before DB publication;
- no silently dangling appearance, portrayal, continuity, event, transition, or evidence references.

The compiler must fail rather than partially publish a broken DB.

## 6. SQL views as the public query contract

Consumers should prefer named SQL views over hard-coding table joins.

Initial DB v1 views:

### `v_work_connections_all`

One logical work pair per connection, with aggregated reasons.

Reasons can originate from explicit relations, shared entity identity, verified transitions, shared events, or other approved fact types.

### `v_work_connection_reasons`

One row per reason supporting a work pair, preserving originating fact IDs, verification status, certainty, and reason type.

### `v_entity_work_history`

All works for a fictional entity, with appearance kind, continuity context, portrayal info when available, and verification status.

### `v_multiverse_crossings`

Human-readable source/destination continuity, traveler identity, containing work, event, and evidence status.

### `v_continuity_works`

Works and events belonging to/depicting each continuity context.

### `v_prewatch_candidates`

Input view for the existing prewatch policy engine. The final prewatch graph remains policy-derived rather than a fact table.

### `v_flowchart_nodes`

Work metadata needed by the HTML generator, excluding layout coordinates.

### `v_flowchart_edge_candidates`

All potential physical work edges with reason summaries and verification/strength inputs. Visibility and visual strength remain view policy decisions outside canonical SQL facts.

Views are versioned contracts. HTML generation should depend on these views, not arbitrary ad hoc SQL over internal tables.

## 7. HTML generation boundary

GitHub Pages remains a static site.

The browser does not need a live server database.

Build pipeline:

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

The HTML must not contain manually maintained character/relation fact arrays such as legacy `CHAR_LINKS`.

The browser receives only the data required for interaction. Large evidence/source payloads may be split into lazy-load JSON if needed later.

SQLite-in-the-browser/WASM is explicitly out of scope for DB v1 because it adds runtime weight without improving canonical correctness. It may be reconsidered only if future interactive query requirements justify it.

## 8. Derived edge policy

The database exposes **what relationships can be derived**, not how strongly the UI must show them.

Every candidate edge carries reason metadata such as:

- reason type;
- source fact ID(s);
- fact verification status;
- certainty;
- directness where applicable;
- continuity/variant interpretation;
- human-readable reason summary.

Examples:

- verified direct work relation → strong candidate;
- confirmed same-entity multiverse transition → strong crossover candidate;
- same character appearing in two works → character-continuity candidate;
- same actor playing variants → variant/meta candidate, never same-character by default;
- legacy seed with unresolved return continuity → available but weak/uncertain candidate.

Final opacity/glow/bundling is `views/flowchart/` policy.

## 9. Migration from current Library v5

Migration is incremental and preserves all current audited work.

### Phase 1 — DB compiler without semantic rewrite

- create SQLite schema matching existing canonical tables;
- load current canonical facts read-only;
- reproduce current derived work graph through SQL views;
- prove DB build determinism;
- keep existing CSV-driven derived builder as regression oracle only.

No content facts change solely because DB v1 exists.

### Phase 2 — Add new normalized canonical tables

Introduce, with tests:

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
- `entity_possessions`

Existing data moves only when the new table is semantically better. Migration ledger records each moved/superseded legacy representation.

### Phase 3 — Multiverse audit migration

Current audited multiverse relations are decomposed where appropriate.

For example, Thunderbolts* → First Steps remains useful as a derived/display connection, while the canonical underlying fact becomes a transition/event describing the Earth-828 Fantastic Four-marked ship arriving in Earth-616.

The explicit First Steps → Doomsday lead-in remains `work_relations` because it is inherently a source-backed relation between works.

### Phase 4 — HTML switches to DB exports

- generate flowchart node JSON from `v_flowchart_nodes`;
- generate edge/reason JSON from `v_flowchart_edge_candidates` and policy;
- remove independent fact arrays from HTML;
- compare old/new selected-path behavior and prewatch results;
- retain mobile performance requirements.

### Phase 5 — broader content audit

Continue the 131-work audit using the richer fact model. New information should enter the semantically correct table rather than creating ad hoc edges.

## 10. Backward compatibility and main-branch safety

- `main` is not changed during DB design or experimental migration.
- Existing `work_id` values stay stable.
- Existing audited fact IDs stay stable unless a migration ledger explicitly supersedes them.
- Old derived files may remain temporarily as regression outputs, but not as competing canonical sources.
- No fixed edge count is a correctness target.
- Current static GitHub Pages deployment remains viable throughout migration.

## 11. Testing requirements

DB v1 implementation must use TDD and add tests for:

1. deterministic SQLite compilation from identical canonical input;
2. FK and CHECK constraint enforcement;
3. canonical SHA immutability during ordinary build;
4. SQL view contract stability;
5. parity of existing audited relations before semantic migration;
6. multiverse transition derivation without asserting false same-universe membership;
7. same actor / different entity never creating same-character continuity;
8. same individual moving between universes preserving identity when evidence supports it;
9. unknown source/destination continuity staying null rather than fabricated;
10. HTML export containing no canonical-only manual fact arrays;
11. generated JSON determinism;
12. Pixel-6-oriented static payload/performance regression checks when HTML generation is switched.

## 12. Success criteria

DB v1 is successful when:

- a complete SQLite database can be deterministically rebuilt from Git canonical facts;
- ordinary build never mutates canonical input;
- `index.html` no longer owns independent Marvel facts;
- all HTML graph data comes through versioned DB views/exports;
- multiverse crossings are queryable independently from work-to-work relationships;
- fictional identity, actor identity, continuity, events, production metadata, and evidence remain distinct;
- existing audited facts and IDs survive migration without silent loss;
- a reviewer can answer “why is this line here?” by tracing a derived edge back through DB view rows to canonical fact/evidence IDs;
- future views can be built from the same library without modifying canonical facts merely to satisfy presentation needs.

## 13. Explicit non-goals for DB v1

DB v1 does not attempt to:

- model every Marvel Comics continuity;
- become a public writable server database;
- add user accounts or collaborative editing;
- run SQL directly in the browser;
- replace the current flowchart UI design in the same step;
- infer unsupported Earth numbers or exact return identities;
- normalize every possible fictional relationship before there is a concrete query/use case.

The design intentionally prefers a normalized but practical audiovisual-works library over a fully generic knowledge graph.
