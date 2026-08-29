# Marvel Library DB v1 Phase 2 — reconciled handoff (2026-08-28)

> **Historical snapshot notice (updated 2026-08-30):** This file records the pre-integration reconciliation of PR #9/#10. The latest semantic production baseline is `main` at `19134e187d40e808f926fd32607b0a2deebac8f1`; later docs-only commits do not alter code/data. PR #10, #11, #12, #13, #21, and #22 are now merged. For current execution state, use `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md` and `AGENTS.md`. The statements below that say production `main` is untouched or that PR #10 must not be merged are historical instructions from that earlier gate.

## Canonical forward line

Continue from branch:

- `library-v5-phase2-db6`

History reconciliation commit:

- `8fcdc53578c5d2f022572698eea1306d3945502f`
- message: `merge: reconcile PR9 phase2 history into db6`

This is a history-only merge: its tree is byte-identical to first parent `c32c7e0104d5410319bf60beb8b42cc5c3494a31`.

Second parent / former PR #9 head:

- `6bed3c37b136ccae11e2d8dd89f7a46b923928b6`
- branch: `library-v5-canonical-freeze`
- draft PR #9

The common pre-reconciliation ancestor was:

- `81bd50bace16782b4b79716652299c679924f701`

PR #9 is now an ancestor of the forward `db6` history. Do not restart from PR #9 or merge it again.

Production `main` remains untouched. Do not merge draft PR #10 or publish `main` without explicit user approval.

## Phase 1 status

DB v1 Phase 1 is complete before the Phase 2 boundary. Completed and regression-tested:

- canonical CSV freeze / read-only build discipline
- SQLite schema and canonical-to-SQLite compiler
- identity resolution (`identity_of` aliases collapse; variants do not collapse by default)
- SQL public views
- semantic parity with the legacy Python reason derivation
- logical DB fingerprint
- SQLite exporter for `work_pair_reasons.csv` and `work_edges_all.csv`
- ordinary build switched to the SQLite-backed graph path
- deterministic DB / graph / ordinary-build CI
- SQLite FK and integrity checks
- bootstrap isolation from canonical data

Phase 2 may add new semantic reasons, but existing graph pair identity remains protected. Stable edge projection (`edge_id`, source, target, row order) is explicitly regression-tested against the Phase 1 Python oracle.

## PR #9 semantic reconciliation

The former PR #9 unique commits did not mutate canonical CSV facts. Its important safety contracts are carried forward explicitly:

1. invalid Phase 2 `event_kind` values are rejected by SQLite CHECK constraints;
2. an unrelated active multiverse `work_relation` does not receive a transition reason merely because a transition exists elsewhere;
3. Phase 2 reason growth must not change legacy edge IDs, source/target pairs, or edge ordering.

These guards live in:

- `tests/library_v5/test_phase2_pr9_reconciliation.py`
- `tests/library_v5/test_db_export_parity.py`

Architectural decisions retained from the PR #9 Phase 2 handoff:

- a work-to-work edge is a derived view, not the semantic home of a multiverse crossing;
- event / occurrence / transition / participant facts are the semantic home;
- graph/reason counts are observations, not correctness targets;
- do not infer film chronology from a crossing;
- do not invent Earth numbers without source support;
- proxy `work_relations` are retired only after first-class replacement semantics independently preserve the intended graph pair;
- retain a `work_relation` if it still carries an independent editorial/story assertion after transition migration.

## Phase 2 schema / views

Canonical fact tables:

- `events.csv`
- `event_occurrences.csv`
- `event_participants.csv`
- `event_relations.csv`
- `multiverse_transitions.csv`
- `transition_participants.csv`

SQLite schema version:

- `1.1-phase2-events`

Public views include:

- `v_event_history`
- `v_multiverse_crossings`
- `v_work_connection_reasons`
- `v_work_connections_all`

Transition reasons are conservative: shared continuity alone cannot invent a new work pair.

## Phase 2 Tasks 1–4

Complete and verified:

1. canonical event / transition schema;
2. SQLite compilation and semantic integrity;
3. public event / multiverse views;
4. conservative `multiverse_transition` work reasons.

A performance regression caused by repeated correlated rollup evaluation was fixed. `scripts/library_v5/db_rollup.py` installs a one-pass ordered rollup.

## Task 5 — Thunderbolts* / Fantastic Four ship arrival

First-class facts now model the `Excelsior` / Fantastic Four-marked spacecraft crossing from Earth-828 context into Earth-616, depicted in the `Thunderbolts*` post-credit scene.

Safety boundaries:

- `continuity-earth-616` is distinct from legacy grouping `continuity-mcu`;
- no Reed / Sue / Johnny / Ben traveler fact is asserted merely from the ship arrival;
- film chronology is not inferred from the crossing.

The legacy relation

- `work-relation-thunderbolts-new-avengers-2025-the-fantastic-four-first-steps-2025-crossover`

remains active for now. Do **not** supersede it until an explicit fixture proves the transition-derived pair survives independently; unlike the NWH Peter cases, current support may still depend on the proxy relation because the ship does not yet provide an origin-work appearance trail.

## Task 6 — No Way Home Raimi / Webb Peter transitions

Complete including proxy retirement.

First-class transitions:

- `event-nwh-raimi-peter-arrival`
  - source `continuity-spider-man-raimi`
  - destination `continuity-earth-616`
  - `spell_displacement`
  - traveler `entity-x-f162d4b4b2`
  - representative source work `spider-man-3-2007`

- `event-nwh-webb-peter-arrival`
  - source `continuity-spider-man-amazing`
  - destination `continuity-earth-616`
  - `spell_displacement`
  - traveler `entity-x-f8b1d323de`
  - representative source work `the-amazing-spider-man-2-2014`

MCU Peter remains a distinct entity. No numbered Earth is invented for the Raimi or Amazing worlds.

A fan-out bug that initially attached the transition reason to every earlier Peter appearance was fixed by selecting the latest supported participant/source-continuity work.

Parity was explicitly tested with the old proxy relations temporarily superseded; transition reasons still reproduced both pairs. Therefore these pure crossing proxies are now canonically `superseded`:

- `work-relation-spider-man-3-2007-spider-man-no-way-home-2021-crossover`
- `work-relation-the-amazing-spider-man-2-2014-spider-man-no-way-home-2021-crossover`

Audit history:

- `review-2026-08-28-nwh-raimi-proxy-relation-retired`
- `review-2026-08-28-nwh-webb-proxy-relation-retired`
- `data/content_audit/applied/2026-08-28-nwh-proxy-relation-retirement-phase2.json`

## Last fully verified content state before history-only reconciliation

GitHub Actions run #199 on commit `c32c7e0104d5410319bf60beb8b42cc5c3494a31` completed successfully.

Observed:

- 138 / 138 unit tests PASS
- audit issues: 0
- review integrity issues: 0
- FK check rows: 0
- SQLite integrity: `ok`
- prewatch edges: 199
- story paths reproduced: 83 / 83
- `work_edges_all`: 361
- `work_pair_reasons`: 566
- events: 3
- event occurrences: 3
- multiverse transitions: 3
- transition participants: 3
- reviews: 41
- canonical read-only check: PASS
- DB determinism: PASS
- graph regeneration without `index.html`: PASS
- ordinary build determinism: PASS
- bootstrap isolation / determinism: PASS

The history-only merge must be reverified by CI before treating the reconciled head as the new verified checkpoint.

## Next approved work — Task 7

Proceed one migration at a time with TDD, evidence, and review history. Approved order:

1. Eddie Brock / Venom: Sony/Venom universe -> Earth-616 and return;
2. Adrian Toomes / Vulture: Earth-616 -> Sony/Morbius universe;
3. Monica Rambeau: MCU -> alternate universe in `The Marvels`;
4. `Doctor Strange in the Multiverse of Madness` traversals;
5. `Deadpool & Wolverine` TVA / multiverse transfers.

Start with Venom. Model the two directional movements separately if the source evidence supports both:

- Sony/Venom context -> Earth-616 in the `Venom: Let There Be Carnage` post-credit;
- Earth-616 -> Sony/Venom context in the `Spider-Man: No Way Home` mid-credit.

Before writing canonical facts:

- inspect the existing continuity ID for the Sony/Venom context;
- inspect the existing Eddie Brock / Venom entity identity model;
- refresh official / source evidence;
- do not invent a Sony-universe Earth number;
- write RED tests first;
- after first-class transition parity, re-evaluate the old Venom->NWH work relation and supersede it only if it is a pure crossing proxy and the pair survives independently.
