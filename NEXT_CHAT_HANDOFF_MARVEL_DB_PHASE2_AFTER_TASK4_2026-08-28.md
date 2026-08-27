# NEXT CHAT HANDOFF — Marvel Library DB v1 Phase 2 after Task 4

Date: 2026-08-28 JST

## Canonical repository state

- Repository: `kamochama/marvel-flowchart-jp`
- Working branch: `library-v5-canonical-freeze`
- Implementation checkpoint SHA before this handoff document: `5cefa1379653bd7c9ee980c372262a277c06f498`
- Checkpoint commit: `feat: install multiverse transition graph reasons during DB compile`
- PR: #9, base `main`
- Production `main` baseline remains `3af097b72c174077c83d7091f79222a72fc7134f` (`v5.20.5`). Do not modify/merge main without explicit user approval.
- Fresh CI for checkpoint SHA: Library v5 canonical freeze CI run #163 / run id `33091855426` = SUCCESS.

## User-approved architecture

Treat this as a Marvel audiovisual knowledge library, not an HTML-first project.

Pipeline:

`Git-auditable canonical CSV facts -> compiled SQLite query DB -> SQL public views -> derived JSON/CSV graph -> static HTML viewer`

Rules:

- `data/library/**` remains human-auditable source of truth.
- SQLite is generated query state, never canonical.
- ordinary build is read-only for canonical library and `data/content_audit/reviews.csv`.
- HTML must eventually consume DB-derived outputs, not embed or invent canonical facts.
- shared actor does not imply same fictional identity.
- `identity_of` may collapse aliases; `variant_of` does not collapse by default.
- work-to-work edges are derived views, not the semantic home of multiverse movement.
- counts are observations, never correctness targets.
- every semantic correction is evidence-backed and recorded in review history.

## DB v1 Phase 1 — complete baseline

Plan:
`docs/superpowers/plans/2026-08-27-marvel-library-db-v1-phase1.md`

Review:
`docs/superpowers/reviews/2026-08-27-marvel-library-db-v1-phase1-review.md`

Implemented:

- explicit SQLite schema + FK/CHECK constraints
- transactional canonical CSV -> SQLite compiler
- canonical identity helper (`identity_of` only)
- versioned public SQL views
- logical DB fingerprinting
- DB exporter reproducing existing graph rows/IDs deterministically
- ordinary build routed through SQLite rather than `write_derived_edges`
- canonical SHA guard retained
- raw `data/derived/db/marvel.sqlite` excluded from byte-oriented library manifest; logical `library_db_manifest.json` is the reproducibility contract
- Phase 1 parity review committed

Important defect found/fixed during DB work:

- `First Steps -> Doomsday` had invalid `continuity_scope=crossover`; corrected with review history to `continuity_scope=multiverse`. Direct `lead_in` remains source verified.
- review ledger supports `verified_rechecked` for evidence-backed semantic corrections without changing verification status.

## Content fixes already preserved

- Frank Castle duplicate identities linked through `identity_of`; Brand New Day Punisher appearance/portrayal source verified.
- `The Fantastic Four: First Steps` setting corrected to Earth-828; old MCU-main continuity membership superseded.
- `First Steps -> Doomsday` direct lead-in source verified.
- `Thunderbolts* -> First Steps` multiverse crossover proxy exists from earlier audit, but Phase 2 is intended to replace proxy semantics with first-class transition facts.
- No Way Home multiverse arrivals, Venom crossing, Loki/TVA connection, Morbius Vulture transfer, etc. have had targeted audits; actor reuse alone is never treated as crossing.

## DB v1 Phase 2 — Events & Multiverse

Plan:
`docs/superpowers/plans/2026-08-27-marvel-library-db-v1-phase2-events-multiverse.md`

Goal: represent physical cross-universe movement as first-class facts instead of forcing everything into `work_relations.csv`.

### Tasks 1–4: infrastructure checkpoint reached

The current branch contains the Phase 2 event/multiverse infrastructure:

Canonical tables:

- `events.csv`
- `event_occurrences.csv`
- `event_participants.csv`
- `event_relations.csv`
- `multiverse_transitions.csv`
- `transition_participants.csv`

Audit/compiler support includes:

- new table PK/FK/evidence checks
- event/transition semantic checks
- DB schema/compiler/fingerprint coverage
- public event and crossing views
- conservative `multiverse_transition` work-connection reason support

Latest commits immediately before handoff include:

- `a02eb18...` — RED tests for conservative multiverse transition edge reasons
- `e62c92b...` — derive conservative work reasons from multiverse transitions
- `5cefa137...` — install multiverse transition graph reasons during DB compile

Fresh CI on `5cefa137...` is SUCCESS.

## EXACT NEXT STEP

Resume Phase 2 at **Task 5 — pilot canonical migration: Thunderbolts* F4 ship arrival**.

Do this one problem at a time with TDD:

1. Refresh evidence for the `Thunderbolts*` post-credit scene.
2. Preserve `The Fantastic Four: First Steps` origin context as Earth-828.
3. Destination is MCU main/Earth-616 only if evidence/model support remains explicit.
4. Create an event for the F4-marked ship arrival.
5. Create occurrence in `thunderbolts-2025`, post-credit.
6. Create `multiverse_transition` Earth-828 -> Earth-616.
7. Add the F4-marked ship as vehicle participant only if evidence supports that identity.
8. DO NOT add Reed/Sue/Johnny/Ben as travelers merely because it is the F4 ship; only add people confirmed aboard.
9. Verify `v_multiverse_crossings` and derived `multiverse_transition` reason.
10. Only after replacement semantics are proven, decide whether the old explicit `Thunderbolts* -> First Steps` proxy work relation should be superseded with review history.
11. Run full CI before moving to Task 6.

Task 6 after that is separate: No Way Home Raimi/Webb Peter arrivals. Do not batch it together with Task 5.

## Important modeling interpretation

For multiverse data, keep these distinct:

- work setting/origin continuity
- an event occurring inside a work
- a traveler/object crossing source continuity -> destination continuity
- actor portrayal
- variant identity
- a derived work-to-work relation used by the flowchart

Example intended model:

`Thunderbolts*` contains event `F4-marked ship arrival`
-> transition `Earth-828 -> Earth-616`
-> participant `F4-marked ship` as vehicle
-> DB may derive an appropriate graph reason

This MUST NOT be encoded as “First Steps takes place in Earth-616”.

## Guardrails for next chat

- Read latest branch HEAD first; do not assume this document is newest if branch advanced.
- Run/inspect fresh CI before claiming a task complete.
- Fix discovered canonical defects as part of the work, using RED test -> evidence/review patch -> full CI.
- Do not silently edit `source_verified` rows.
- Do not infer continuity identity from actors, costumes, logos, or audience expectation alone.
- Do not invent Earth numbers.
- Do not touch `main`.
- Do not start HTML cutover/release/credits/membership/possession phases yet.

## User preference

Proceed carefully and autonomously, repairing problems as found. The user explicitly asked for the database/library to support many dimensions of Marvel facts and for HTML to be generated from that data layer.
