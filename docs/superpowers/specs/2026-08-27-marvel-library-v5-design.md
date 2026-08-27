# Marvel Library v5 Canonical Model Design

## Status

- Date: 2026-08-27
- Base: `main` at `3af097b72c174077c83d7091f79222a72fc7134f` (`v5.20.5`)
- Design branch: `library-v5-design`
- Production `main` remains unchanged until migration and audit complete.

## 1. Goal

The canonical repository data becomes a reusable **Marvel audiovisual works library**, not a set of rows tailored to one HTML flowchart.

The library stores source-backed facts about works, fictional entities, appearances, performers, continuities, chronology claims, and explicit work-to-work relations. Flowchart edges, prewatch graphs, story paths, line styling, glow strength, bundling, and layout are derived products.

Fixed counts such as `199 connections`, `83 story-path edges`, `416 rendered edges`, or any later edge count are **not** correctness targets for the canonical library.

## 2. Non-goals

This migration does not:

- redesign the final flowchart UI;
- choose final line opacity or selection glow strength;
- make crossing reduction a correctness criterion;
- force ambiguous legacy continuities into one timeline;
- infer that two fictional characters are identical because the same actor plays them;
- require a complete external re-research of all 131 works before the schema can be adopted.

## 3. Repository layers

The repository is split into three layers.

### 3.1 Canonical fact layer — `data/library/`

Human-audited facts with stable IDs and evidence. This is the new source of truth.

### 3.2 Derived graph layer — `data/derived/`

Deterministically generated relationships for specific uses, including shared-character work pairs, prewatch traversal, chronology paths, and flowchart candidate edges.

Derived files are never edited by hand.

### 3.3 View layer — `views/flowchart/`

HTML-specific choices: lanes, labels, geometry, line visibility, line strength, glow, dimming, bundling, filters, and interaction behavior.

A relationship may exist in the fact and derived layers even when a view renders it faintly or hides it by default.

## 4. Canonical files

### 4.1 `works.csv`

One row per audiovisual work. Existing 131 stable `work_id` values are preserved.

Contains titles, format, release information, production/status fields, aliases, and source-backed release metadata.

Flowchart lane placement and display-specific chronology fields do not belong here.

### 4.2 `entities.csv`

One row per fictional or in-universe entity.

Fields:

- `entity_id`
- `name_ja`
- `name_en`
- `entity_type`
- `notes`

Initial `entity_type` enum:

- `character`
- `organization`
- `artifact`
- `place`
- `species`
- `event`
- `concept`

Examples include Tony Stark, Avengers, TVA, Infinity Stones, Wakanda, the Blip, and the Battle of New York.

### 4.3 `entity_relations.csv`

Typed relations between fictional entities where identity distinctions matter.

Fields:

- `entity_relation_id`
- `source_entity_id`
- `relation_kind`
- `target_entity_id`
- `certainty`
- `notes`

Initial `relation_kind` enum:

- `variant_of`
- `identity_of`
- `successor_identity_of`
- `member_of`

This prevents variants, aliases, or mantle succession from being collapsed into false same-character identity.

### 4.4 `appearances.csv`

The canonical answer to **which entity appears in which work?**

Fields:

- `appearance_id`
- `work_id`
- `entity_id`
- `appearance_kind`
- `certainty`
- `verification_status`
- `notes`

Initial `appearance_kind` enum:

- `onscreen`
- `voice`
- `post_credit`
- `archive`
- `mention`
- `photo_or_recording`
- `unknown`

`appearances.csv` replaces the current situation where `CHAR_LINKS` exists only inside generated `index.html`.

A character variant uses a distinct variant entity ID plus `entity_relations.variant_of`; it does not silently reuse the main entity ID.

### 4.5 `people.csv`

One row per real-world performer used by portrayal facts.

Fields:

- `person_id`
- `name`
- `notes`

### 4.6 `portrayals.csv`

Maps a real-world person to a fictional entity in a particular work.

Fields:

- `portrayal_id`
- `work_id`
- `person_id`
- `entity_id`
- `portrayal_kind`
- `certainty`
- `verification_status`
- `notes`

Initial `portrayal_kind` enum:

- `same_character`
- `variant`
- `voice`
- `archive`
- `unknown_role`

This explicitly separates Robert Downey Jr. as Tony Stark from Robert Downey Jr. as Doctor Doom. Shared performer identity alone must never generate a same-character work edge.

### 4.7 `continuities.csv`

One row per continuity, universe, timeline family, or intentionally ambiguous continuity bucket.

Fields:

- `continuity_id`
- `label_ja`
- `label_en`
- `continuity_kind`
- `certainty`
- `notes`

### 4.8 `work_continuities.csv`

Many-to-many mapping between works and continuities.

Fields:

- `work_continuity_id`
- `work_id`
- `continuity_id`
- `relation_to_continuity`
- `certainty`
- `notes`

A work may belong to multiple continuity contexts when that is more accurate than forcing a single universe label.

### 4.9 `chronology_assertions.csv`

Source-backed in-universe ordering claims, separate from release order and layout.

Fields:

- `chronology_assertion_id`
- `continuity_id`
- `earlier_work_id`
- `later_work_id`
- `certainty`
- `notes`

Chronology uncertainty is represented as data rather than forced placement.

### 4.10 `work_relations.csv`

Explicit work-to-work facts that cannot be safely reduced to shared appearances.

Examples include direct sequel, spinoff, direct lead-in, explicit aftermath, explicit crossover, official world/lore relation, and promotional association when intentionally retained as a fact of promotion rather than story continuity.

Fields:

- `work_relation_id`
- `source_work_id`
- `target_work_id`
- `relation_kind`
- `relation_scope`
- `directness`
- `continuity_scope`
- `certainty`
- `notes`

A relation that merely says “the same character appears in both works” is normally represented by `appearances.csv`, not duplicated here.

### 4.11 `sources.csv`

The existing source registry is retained and normalized as needed.

### 4.12 `evidence.csv`

Links facts to one or more sources.

Fields:

- `evidence_id`
- `fact_table`
- `fact_id`
- `source_id`
- `evidence_role`
- `quoted_or_paraphrased_note`
- `verified_at`

Initial `evidence_role` enum:

- `primary`
- `supporting`
- `conflicting`
- `legacy_seed`

The same fact may have multiple evidence rows. Tests validate that `fact_table + fact_id` resolves to an actual canonical row.

## 5. ID and audit-status conventions

IDs are stable identifiers, not display strings.

### 5.1 Stable ID format

- existing `work_id`: preserved exactly;
- character entity: `char-<slug>`;
- organization: `org-<slug>`;
- artifact: `artifact-<slug>`;
- place: `place-<slug>`;
- event: `event-<slug>`;
- other entity types follow `<entity_type>-<slug>`;
- person: `person-<slug>`.

Variant entities add a disambiguator, for example `char-black-bolt-earth-838`, and point to the base entity using `variant_of`.

Fact-row IDs are deterministic composites encoded as stable strings by migration/generation helpers rather than hand-numbered counters. Exact escaping rules are implemented once and tested; changing a Japanese or English display name must not change an existing stable ID.

### 5.2 `certainty`

Canonical certainty enum:

- `confirmed`
- `probable`
- `uncertain`
- `unknown`

### 5.3 `verification_status`

Canonical verification enum:

- `legacy_seed` — migrated from old generated/internal data but not independently reverified;
- `source_verified` — supported by canonical evidence under the source policy;
- `conflicted` — credible sources disagree or identity is unresolved;
- `superseded` — retained only for migration history, not current fact generation.

A `legacy_seed` row cannot be silently upgraded. Promotion to `source_verified` requires at least one non-legacy evidence row.

## 6. Derived files

Generated files live under `data/derived/` and are never hand-edited.

### 6.1 `work_pair_reasons.csv`

One row per reason that two works are related. A work pair may have multiple rows because it can share multiple characters and also have an explicit story relation.

Each reason identifies its source fact(s), such as appearance IDs or work-relation IDs.

### 6.2 `work_edges_all.csv`

Unique work-pair edges generated from `work_pair_reasons.csv`. The generator records all supporting reason IDs rather than discarding them.

### 6.3 `prewatch_edges.csv`

Purpose-specific traversal graph generated from canonical facts plus explicit prewatch policy. Prewatch tier is not a property of an appearance fact.

### 6.4 `story_paths.csv`

Generated continuous-story paths. The current manually curated 83-edge file becomes a migration baseline and regression reference, not the long-term fact store.

### 6.5 Compatibility exports

During migration, generated compatibility exports may reproduce legacy v4 shapes (`connections.csv`, `story_paths.csv`, etc.) so old tooling can be compared without making those formats canonical.

## 7. View configuration

Flowchart-specific configuration lives under `views/flowchart/` and may contain display regions, Japanese lane labels, placement hints, edge visibility policy, opacity/glow policy, bundling policy, crossing treatment, interactions, and default filters.

Internal IDs may remain English; user-facing lane and region labels are Japanese.

No view setting may delete a canonical fact.

## 8. Edge derivation semantics

The canonical library does **not** store every possible work-to-work character edge as fact rows.

Generators may produce legitimate edge modes from the same appearances:

- `all_pairs`: every pair of works sharing an entity;
- `adjacent_release`: consecutive appearances by release order;
- `adjacent_chronology`: consecutive appearances within selected chronology assertions;
- `target_centric`: all prior appearances relevant to a selected target;
- `explicit_only`: only `work_relations.csv`;
- combined modes.

Rendering direction is derived/view data unless the underlying fact is itself directional.

All appearance kinds remain canonical facts. Derived generators preserve the appearance kind in the reason row, allowing views to include, dim, or filter mention/archive/photo-only reasons without deleting them.

## 9. Multiple reasons and physical lines

For a work pair connected by multiple characters or relation types:

- canonical facts remain separate;
- `work_pair_reasons.csv` keeps every reason;
- `work_edges_all.csv` may collapse the pair to one logical edge with multiple reason IDs;
- the view decides whether to draw one physical line with multiple reasons or parallel reason-specific lines.

Different source works entering the same target remain distinct work-pair edges and must not be silently merged into one edge. This is a regression requirement for dense targets such as Doomsday.

## 10. Migration from v4 / v5.20.5

Migration files live under `data/migration/v4/`. Migration is evidence-preserving and reversible until audit completion.

### 10.1 Baseline preservation

`main` at `3af097b72c174077c83d7091f79222a72fc7134f` remains the immutable production baseline during migration.

### 10.2 `works.csv`

Preserve all 131 stable work IDs and work facts. Move layout/chronology-placement concerns out of the work table where appropriate.

### 10.3 `CHAR_LINKS`

Extract `CHAR_LINKS` from v5.20.5 `index.html` into migration seed rows for `entities.csv` and `appearances.csv`.

Every extracted row is `verification_status=legacy_seed` until independently audited. Generated HTML is a migration source, not external evidence.

`data/migration/v4/char_links_disposition.csv` records every source row and its resulting v5 fact IDs.

### 10.4 Local 416-edge experiment

The local 416-edge graph is diagnostic only and is not canonical input. Its reasons must be reconstructible from migrated legacy data plus independently audited new facts.

### 10.5 `entity_returns.csv`

Decompose each legacy proxy row into the appropriate combination of appearance, portrayal, entity identity/variant relation, and evidence facts.

The “representative prior work” concept does not survive as a canonical character fact; a view or prewatch policy may derive it later.

`data/migration/v4/entity_returns_disposition.csv` records all eight legacy rows and resulting v5 fact IDs.

### 10.6 `connections.csv`

Audit all 199 rows. Each row receives exactly one primary disposition:

1. `explicit_relation` — migrate to `work_relations.csv`;
2. `appearance_derived` — represented by appearances/portrayals/entity relations and not duplicated as an explicit relation;
3. `policy_only` — move to prewatch/view policy;
4. `invalid_or_superseded` — excluded from current generation with an explicit audit reason.

A row may reference several resulting v5 fact IDs, but it has one migration disposition. No row disappears silently.

`data/migration/v4/connections_disposition.csv` records all 199 rows.

### 10.7 `story_paths.csv`

Preserve the current 83 rows as regression baseline. Rebuild the long-term derived file from canonical facts plus path policy.

### 10.8 `chronology.csv`

Separate source-backed chronology assertions from flowchart lane placement. Ambiguous placements remain ambiguous.

## 11. Audit invariants

### Identity and referential integrity

- every foreign key resolves;
- all 131 existing `work_id` values are preserved;
- stable entity/person IDs follow section 5;
- no duplicate canonical fact IDs;
- no duplicate identical fact rows.

### Evidence integrity

- current/future externally asserted facts have source-backed evidence;
- legacy seeds stay labeled until audited;
- conflicting evidence can coexist without overwriting history;
- actor-only identity never implies character identity.

### Semantic integrity

- character variants are distinguishable;
- mantle succession is distinguishable from same-person identity;
- shared appearance is not mislabeled as direct sequel;
- promotional association is not mislabeled as story continuity;
- view visibility does not affect canonical existence.

### Migration integrity

- all 199 legacy connections receive dispositions;
- every legacy `CHAR_LINKS` row receives a disposition;
- all eight `entity_returns` rows receive dispositions;
- every current story-path edge remains explainable by v5 facts or is documented as a changed/corrected decision;
- no production `main` update occurs until these ledgers are complete.

## 12. Tests

Implementation follows test-first development. Minimum test families:

1. schema/header tests for every canonical table;
2. foreign-key integrity;
3. uniqueness and stable-ID rules;
4. evidence coverage and `legacy_seed` promotion rules;
5. variant/performer false-inference regression, including RDJ Tony Stark vs Doctor Doom;
6. deterministic derivation of work-pair reasons;
7. no loss of distinct incoming work pairs at dense targets such as Doomsday;
8. migration coverage for all 199 legacy connections, all legacy `CHAR_LINKS`, and all eight `entity_returns` rows;
9. deterministic generated outputs across two clean runs;
10. legacy comparison reports for v5.20.5 baseline behavior.

## 13. Source policy

For current or changing Marvel facts, prefer first-party sources when available:

1. Marvel / Marvel Studios;
2. Disney / Disney+;
3. Sony Pictures for Sony-controlled releases;
4. other official studio/distributor sources;
5. high-quality trade press for facts not published first-party;
6. secondary/community sources only for candidate discovery, never as sole canonical evidence when stronger sources are available.

Source quality and uncertainty are recorded rather than hidden.

## 14. Versioning and compatibility

- v4 remains production baseline until v5 migration passes audit;
- v5 schema version begins at `5.0`;
- migration scripts are deterministic and rerunnable;
- generated compatibility files are clearly marked generated;
- old files are not deleted until the v5 audit report demonstrates complete migration coverage.

## 15. Definition of done

The canonical migration is complete when:

- all 131 existing works are represented with stable IDs;
- legacy character data is migrated into canonical entities/appearances with explicit audit status;
- all 199 legacy work edges have documented dispositions;
- all eight legacy `entity_returns` rows are decomposed into normalized facts;
- current story-path behavior is reproducible or every intentional difference is documented;
- canonical facts can regenerate an all-relations graph without using `index.html` as a runtime data source;
- actor reuse does not create false character continuity;
- every derived output is deterministic;
- repository-wide tests pass;
- a migration audit report is reviewed before any v5 data replaces the production `main` canonical set.

## 16. Immediate implementation boundary

The first implementation plan covers **schema + migration infrastructure + legacy extraction + migration ledgers + deterministic derived-edge generator**.

It does not yet perform complete external re-research of every entity in every one of the 131 works. That content audit follows once the normalized library and migration machinery are trustworthy.
