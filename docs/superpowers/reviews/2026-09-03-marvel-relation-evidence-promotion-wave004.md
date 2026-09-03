# Marvel Library v5 relation evidence promotion wave004 review

Date: 2026-09-03

## Decision

Promote the following four existing relations from `legacy_seed` to `source_verified` after registering an official source, relation-specific evidence, and a review transition for each:

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| `work-relation-hawkeye-2021-echo-2024-spinoff` | `disney-echo-hawkeye-spinoff-2024` | `evidence-echo-hawkeye-spinoff-disney-2024` | `review-2026-09-03-echo-hawkeye-spinoff` |
| `work-relation-daredevil-born-again-s1-2025-daredevil-born-again-s2-2026-sequel` | `disney-daredevil-born-again-s2-continuation-2025` | `evidence-daredevil-born-again-s1-s2-sequel-disney-2025` | `review-2026-09-03-daredevil-born-again-s1-s2-sequel` |
| `work-relation-daredevil-born-again-s2-2026-the-punisher-one-last-kill-2026-05-12-crossover` | `disneyplus-daredevil-born-again-s2-punisher-crossover-2026` | `evidence-daredevil-s2-punisher-one-last-kill-crossover-disneyplus-2026` | `review-2026-09-03-daredevil-s2-punisher-one-last-kill-crossover` |
| `work-relation-the-punisher-s1-2017-the-punisher-s2-2019-sequel` | `marvel-punisher-s2-renewal-2017` | `evidence-punisher-s1-s2-sequel-marvel-2017` | `review-2026-09-03-punisher-s1-s2-sequel` |

## Evidence boundaries

- The Walt Disney Company presents *Echo* as the continuation of Maya Lopez's story after *Hawkeye* and her move from supporting character to lead. The existing spinoff relation remains `strong` and `probable`; no certainty upgrade is made.
- The Walt Disney Company describes *Daredevil: Born Again* Season 2 as continuing the Season 1 story. This supports the existing direct sequel relation only.
- Disney+ places *The Punisher: One Last Kill* before and during *Daredevil: Born Again* Season 2. The existing relation remains an indirect `crossover`; it is not rewritten as simple chronology.
- Marvel's official announcement identifies *The Punisher* Season 2 as the returning season. This supports the existing direct sequel relation only.

These sources do not add release/status, chronology assertions, character identity, continuity, or multiverse transition facts. No new work pair is created.

## Verification impact

The relation table remains 164 rows. Four rows move from `legacy_seed` to `source_verified`, producing `22 source_verified`, `139 legacy_seed`, and `3 superseded`. Sources, evidence, and reviews become 59, 149, and 123. The derived graph remains 131 nodes, 355 edges, and 562 pair-reason rows; only the verification statuses of the four explicit relation reasons change.

Across→Beyond, X-Men: The Animated Series → X-Men '97 S1, and the remaining legacy relation queue remain deferred until relation-specific official evidence is available.
