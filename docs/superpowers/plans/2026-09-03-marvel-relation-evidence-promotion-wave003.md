# Marvel Library v5 relation evidence promotion wave003

Date: 2026-09-03

## Scope

Promote only five existing `work_relations.csv` rows whose relation semantics are directly stated by an official Disney or Marvel source:

1. `work-relation-the-avengers-2012-avengers-age-of-ultron-2015-sequel`
2. `work-relation-captain-america-the-first-avenger-2011-captain-america-the-winter-soldier-2014-sequel`
3. `work-relation-thor-2011-thor-the-dark-world-2013-sequel`
4. `work-relation-guardians-of-the-galaxy-2014-guardians-of-the-galaxy-vol-2-2017-sequel`
5. `work-relation-black-panther-2018-black-panther-wakanda-forever-2022-sequel`

The existing IDs, endpoint direction, relation kind, directness, continuity scope, certainty, and notes remain unchanged. Each row receives relation-specific primary evidence and an auditable `legacy_seed -> source_verified` review transition. No release/status, chronology, identity, multiverse transition, or new work pair is inferred.

## Source registrations

- `disney-avengers-age-of-ultron-sequel-2015` — Walt Disney Company 2015 transcript describing *Avengers: Age of Ultron* as a sequel to *The Avengers*.
- `disney-captain-america-winter-soldier-sequel-2013` — Walt Disney Company 2013 transcript describing *The Winter Soldier* as a sequel to *Captain America: The First Avenger*.
- `disney-thor-dark-world-sequel-2013` — Walt Disney Company 2013 transcript describing *The Dark World* as a sequel to the first *Thor* origin film.
- `marvel-guardians-vol2-sequel-2017` — Marvel article describing Vol. 2 as a long-awaited sequel to the 2014 *Guardians of the Galaxy*.
- `marvel-black-panther-wakanda-forever-sequel-2022` — Marvel article describing *Wakanda Forever* as a sequel continuing the world and characters of *Black Panther*.

## RED/GREEN contract

The regression test must fail before the evidence and review rows exist. After the minimal data change it must verify:

- all five exact relation IDs are `source_verified` with unchanged endpoints and semantics;
- each relation has exactly one `work_relations.csv` primary evidence row tied to its intended source;
- each relation has exactly one review transition from `legacy_seed` to `source_verified` with the exact evidence ID;
- each explicit derived reason keeps its pair and reason ID while changing only its verification status to `source_verified`;
- graph cardinalities stay at 131 nodes, 355 edges, and 562 reasons;
- no release/status, event, transition, chronology, identity, or new source-domain fact is promoted by this batch.

## Verification and integration

Run the focused test in RED before data edits, then GREEN, the bundled-Python full test suite, the ordinary build, connectivity audit, and the real Chrome selection/interaction/chronology/publication-order audits. Review the complete diff and merge through a PR only after all required checks pass. The Across→Beyond relation and the remaining legacy relation queue stay deferred.
