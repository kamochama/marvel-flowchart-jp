# Marvel Library v5 relation evidence promotion wave004

Date: 2026-09-03

## Scope

Promote only four existing `work_relations.csv` rows whose relation semantics are directly stated by an official Disney or Marvel source:

1. `work-relation-hawkeye-2021-echo-2024-spinoff`
2. `work-relation-daredevil-born-again-s1-2025-daredevil-born-again-s2-2026-sequel`
3. `work-relation-daredevil-born-again-s2-2026-the-punisher-one-last-kill-2026-05-12-crossover`
4. `work-relation-the-punisher-s1-2017-the-punisher-s2-2019-sequel`

Keep existing IDs, endpoint direction, relation kind, directness, continuity scope, certainty, and notes unchanged. Add one relation-specific primary evidence row and one auditable `legacy_seed -> source_verified` review transition per relation. Do not infer release/status, chronology, identity, multiverse transitions, or new work pairs.

The Daredevil: Born Again Season 2 → The Punisher: One Last Kill relation remains a `crossover`/`indirect` relation: the Disney+ source describes the special as taking place before and during Season 2, so it must not be rewritten as a simple chronological sequel.

## Source registrations

- `disney-echo-hawkeye-spinoff-2024` — Walt Disney Company, official *Echo* article describing Maya Lopez's story after *Hawkeye* and its continuation of that branch.
- `disney-daredevil-born-again-s2-continuation-2025` — Walt Disney Company, official Season 2 article describing continuation from Season 1.
- `disneyplus-daredevil-born-again-s2-punisher-crossover-2026` — Disney+, official viewing guide describing *The Punisher: One Last Kill* in relation to Season 2 and the “before and during” placement.
- `marvel-punisher-s2-renewal-2017` — Marvel, official Season 2 announcement identifying the returning *The Punisher* series.

## RED/GREEN contract

The regression test must fail before the evidence and review rows exist. After the minimal data change it must verify:

- all four exact relation IDs are `source_verified` with unchanged endpoints and semantics;
- each relation has exactly one `work_relations.csv` primary evidence row tied to its intended source;
- each relation has exactly one review transition from `legacy_seed` to `source_verified` with the exact evidence ID;
- each explicit derived reason keeps its pair and reason ID while changing only its verification status to `source_verified`;
- graph cardinalities stay at 131 nodes, 355 edges, and 562 reasons;
- no release/status, event, transition, chronology, identity, or new source-domain fact is promoted by this batch.

## Verification and integration

Run the focused test in RED before data edits, then GREEN, the bundled-Python full test suite, ordinary build, connectivity audit, and real Chrome selection/interaction/chronology/publication-order audits. Review the complete diff and merge through a PR only after all required checks pass. Across→Beyond, X-Men: The Animated Series → X-Men '97 S1, and the remaining legacy relation queue stay deferred.
