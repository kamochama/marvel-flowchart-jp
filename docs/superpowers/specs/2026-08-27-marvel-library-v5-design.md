# Marvel Library v5 Canonical Model Design

## Status

- Date: 2026-08-27
- Base: `main` at `3af097b72c174077c83d7091f79222a72fc7134f` (`v5.20.5`)
- Design branch: `library-v5-design`
- Production `main` remains unchanged until migration and audit complete.

## 1. Goal

The canonical repository data must become a reusable **Marvel audiovisual works library**, not a set of rows tailored to one HTML flowchart.

The library stores source-backed facts about works, fictional entities, appearances, performers, continuities, chronology claims, and explicit work-to-work relations. Flowchart edges, prewatch graphs, story paths, line styling, glow strength, bundling, and layout are derived products.

The fixed counts `199 connections`, `83 story-path edges`, `416 rendered edges`, or any later edge count are **not** correctness targets for the canonical library.

## 2. Non-goals

This migration does not:

- redesign the final flowchart UI;
- choose final line opacity or selection glow strength;
- make crossing reduction a correctness criterion;
- force ambiguous legacy continuities into one timeline;
- infer that two fictional characters are identical because the same actor plays them;
- require every data table to be fully populated before the schema can be adopted.

## 3. Core principle: facts first, views later

The repository is split into three layers.

### 3.1 Canonical fact layer

Human-audited facts with stable IDs and evidence.

### 3.2 Derived graph layer

Deterministically generated relationships for specific uses, such as all shared-character work pairs, prewatch traversal, chronology paths, and flowchart candidate edges.

Derived files are never edited by hand.

### 3.3 View layer

HTML-specific choices: lanes, labels, geometry, line visibility, line strength, glow, dimming, bundling, filters, and interaction behavior.

A relationship may exist in the fact and derived layers even when a view renders it faintly or hides it by default.

## 4. Canonical files

Canonical files live under `data/library/` after migration.

### 4.1 `works.csv`

One row per audiovisual work.

Required stable field:

- `work_id`

Contains work facts such as titles, format, release information, production/status fields, aliases, and source-backed release metadata.

The existing 131 stable `work_id` values are preserved.

Display-placement fields such as flowchart lanes do not belong here.

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

Typed relations between fictional entities when identity distinctions matter.

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

This table prevents variant or mantle relationships from being collapsed into false same-character identity.

### 4.4 `appearances.csv`

The canonical answer to: **which entity appears in which work?**

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

A character variant must use the appropriate variant entity rather than silently reusing the main entity ID.

### 4.5 `people.csv`

One row per real-world performer or creator identity used by portrayal facts.

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

This explicitly separates, for example, Robert Downey Jr. as Tony Stark from Robert Downey Jr. as Doctor Doom. Shared performer identity alone must never generate a same-character work edge.

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

A work may belong to multiple continuity contexts where that is the most accurate representation.

### 4.9 `chronology_assertions.csv`

Source-backed in-universe ordering claims, kept separate from release order and from layout.

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

Examples:

- direct sequel;
- spinoff;
- direct lead-in;
- explicit aftermath;
- explicit crossover;
- official world/lore relation;
- promotional relation, when intentionally retained as a fact of promotion rather than story continuity.

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

A relation that merely says “the same character appears in both works” should normally be represented by `appearances.csv`, not duplicated here.

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

The same fact may have multiple evidence rows.

## 5. Derived files

Generated files live under `derived/` and are never hand-edited.

### 5.1 `work_pair_reasons.csv`

One row per reason that two works are related.

A work pair may have multiple rows because it can share multiple characters and also have an explicit story relation.

### 5.2 `work_edges_all.csv`

Unique work-pair edges generated from `work_pair_reasons.csv`.

The generator records all supporting reason IDs rather than discarding them.

### 5.3 `prewatch_edges.csv`

Purpose-specific traversal graph generated from canonical facts plus explicit prewatch policy.

Prewatch tier is not a property of an appearance fact.

### 5.4 `story_paths.csv`

Generated continuous-story paths. The current manually curated 83-edge file becomes a migration baseline and regression reference, not the long-term fact store.

### 5.5 Compatibility exports

During migration, generated compatibility exports may reproduce the legacy v4 shapes (`connections.csv`, `story_paths.csv`, etc.) so old tooling can be compared without making those formats canonical.

## 6. View configuration

Flowchart-specific configuration moves under `views/flowchart/`.

It may contain:

- display regions and lane labels;
- Japanese left-side labels;
- card placement hints;
- edge visibility policy;
- opacity and glow policy;
- bundling policy;
- crossing treatment;
- interaction rules;
- default filters.

Internal IDs may remain English; user-facing lane and region labels are Japanese.

No view setting may delete a fact from the canonical layer.

## 7. Edge derivation semantics

The library does **not** store every possible work-to-work character edge as canonical rows.

Instead, generators may produce several legitimate edge modes from the same appearances:

- `all_pairs`: every pair of works sharing an entity;
- `adjacent_release`: consecutive appearances by release order;
- `adjacent_chronology`: consecutive appearances within a selected chronology assertion set;
- `target_centric`: all prior appearances relevant to a selected target;
- `explicit_only`: only rows from `work_relations.csv`;
- combined modes.

The flowchart may use `all_pairs` or another mode without changing the fact library.

Direction imposed for rendering is a derived/view property unless the underlying fact itself is directional.

## 8. Multiple reasons and physical lines

For a work pair connected by multiple characters or relation types:

- canonical facts remain separate;
- `work_pair_reasons.csv` keeps every reason;
- `work_edges_all.csv` may collapse the pair to one logical edge with multiple reason IDs;
- the view decides whether to draw one physical line with multiple reasons or parallel reason-specific lines.

This prevents loss of semantic information without forcing redundant geometry into every view.

Different source works entering the same target remain distinct work-pair edges and must not be silently merged into one edge.

## 9. Migration from v4 / v5.20.5

Migration is evidence-preserving and reversible until audit completion.

### 9.1 Baseline preservation

`main` at `3af097b72c174077c83d7091f79222a72fc7134f` remains the immutable production baseline during migration.

### 9.2 `works.csv`

Preserve all 131 stable work IDs and work facts. Move layout/chronology placement concerns out of the work table where appropriate.

### 9.3 `CHAR_LINKS`

Extract `CHAR_LINKS` from v5.20.5 `index.html` into migration seed rows for `entities.csv` and `appearances.csv`.

Every extracted row is marked `verification_status=legacy_seed` until independently audited. Extraction from generated HTML is not treated as external evidence.

### 9.4 Local 416-edge experiment

The local 416-edge graph is a diagnostic/migration aid only. It is not canonical input. Its reasons are recoverable from legacy `CHAR_LINKS`, current relations, and newly audited cast/appearance candidates.

### 9.5 `entity_returns.csv`

Decompose each legacy proxy row into the appropriate combination of:

- appearance fact;
- portrayal fact;
- entity identity/variant relation;
- evidence row.

The “representative prior work” concept does not survive as a canonical character fact. A view or prewatch policy may derive representative prior works later.

### 9.6 `connections.csv`

Audit all 199 rows.

Each row is classified as one of:

1. migrate to `work_relations.csv` because it expresses a genuine explicit work relation;
2. represented by appearances/portrayals/entity relations and therefore not duplicated as an explicit work relation;
3. promotional/view/prewatch policy and therefore moved out of canonical work relations;
4. invalid or superseded, with an audit record explaining removal.

No row disappears silently.

### 9.7 `story_paths.csv`

Preserve the current 83 rows as a regression baseline. Rebuild the long-term file from canonical facts and explicit path policy.

### 9.8 `chronology.csv`

Separate source-backed chronology assertions from flowchart lane placement. Ambiguous placements remain ambiguous.

## 10. Audit rules and invariants

The v5 canonical library must satisfy all of the following.

### Identity and referential integrity

- every foreign key resolves;
- stable `work_id` values are preserved;
- stable entity/person IDs are deterministic and documented;
- no duplicate canonical fact IDs;
- no duplicate identical fact rows.

### Evidence integrity

- externally asserted current/future facts have source-backed evidence;
- legacy seeds are explicitly labeled until audited;
- conflicting evidence can coexist without overwriting history;
- actor-only identity never implies character identity.

### Semantic integrity

- character variants are distinguishable;
- mantle succession is distinguishable from same-person identity;
- shared character appearance is not mislabeled as direct sequel;
- promotional association is not mislabeled as story continuity;
- view visibility does not affect canonical existence.

### Migration integrity

- every v4 `connections.csv` row receives a migration disposition;
- every legacy `CHAR_LINKS` row receives a migration disposition;
- every `entity_returns.csv` row receives a migration disposition;
- every current story-path edge remains explainable by the v5 library or is explicitly documented as a changed/corrected decision;
- no production `main` update occurs until these migration ledgers are complete.

## 11. Tests

Tests are required before implementation changes.

Minimum automated test families:

1. schema/header tests for every canonical table;
2. foreign-key integrity;
3. uniqueness and stable-ID rules;
4. evidence coverage rules;
5. variant/performer false-inference regression, including RDJ Tony Stark vs Doctor Doom;
6. deterministic derivation of work-pair reasons;
7. no loss of distinct incoming work pairs when many works connect to one target such as Doomsday;
8. migration coverage for all 199 legacy connections, all legacy `CHAR_LINKS`, and all eight `entity_returns` rows;
9. deterministic generated outputs across two clean runs;
10. legacy comparison reports for v5.20.5 baseline behavior.

## 12. Source policy

For current or changing Marvel facts, prefer first-party sources in this order when available:

1. Marvel / Marvel Studios;
2. Disney / Disney+;
3. Sony Pictures for Sony-controlled releases;
4. other official studio/distributor sources;
5. high-quality trade press for facts not published first-party;
6. secondary/community sources only as candidate discovery, never as sole canonical evidence when stronger sources are available.

Source quality and uncertainty are recorded rather than hidden.

## 13. Versioning and compatibility

- v4 remains the production baseline until v5 migration passes audit.
- v5 schema version begins at `5.0`.
- migration scripts must be deterministic and rerunnable.
- generated compatibility files must be clearly marked generated.
- old files are not deleted until the v5 audit report demonstrates complete migration coverage.

## 14. Definition of done for the canonical migration

The migration is complete when:

- all 131 existing works are represented with stable IDs;
- legacy character data is migrated into canonical entities/appearances with explicit audit status;
- all 199 legacy work edges have documented dispositions;
- all legacy `entity_returns` are decomposed into normalized facts;
- current story-path behavior is reproducible or every intentional difference is documented;
- canonical facts can regenerate an all-relations graph without using `index.html` as a data source;
- actor reuse does not create false character continuity;
- every derived output is deterministic;
- repository-wide tests pass;
- a migration audit report is reviewed before any v5 data replaces the production `main` canonical set.

## 15. Immediate implementation boundary

The first implementation plan covers **schema + migration infrastructure + legacy extraction + migration ledgers + deterministic derived-edge generator**.

It does not yet attempt a complete external re-research of every entity in every one of the 131 works. That content audit follows on top of the normalized library once the migration machinery is trustworthy.
