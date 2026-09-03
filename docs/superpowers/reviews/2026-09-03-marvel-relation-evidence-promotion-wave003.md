# Marvel Library v5 relation evidence promotion wave003 review

Date: 2026-09-03

Scope: five existing direct sequel rows in `work_relations.csv`; no new graph pair or semantic relation was created.

## Decision

Promote the following existing relations from `legacy_seed` to `source_verified` after registering an official source, relation-specific evidence, and a review transition for each:

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| `work-relation-the-avengers-2012-avengers-age-of-ultron-2015-sequel` | `disney-avengers-age-of-ultron-sequel-2015` | `evidence-avengers-age-of-ultron-sequel-disney-2015` | `review-2026-09-03-avengers-age-of-ultron-sequel` |
| `work-relation-captain-america-the-first-avenger-2011-captain-america-the-winter-soldier-2014-sequel` | `disney-captain-america-winter-soldier-sequel-2013` | `evidence-captain-america-winter-soldier-sequel-disney-2013` | `review-2026-09-03-captain-america-winter-soldier-sequel` |
| `work-relation-thor-2011-thor-the-dark-world-2013-sequel` | `disney-thor-dark-world-sequel-2013` | `evidence-thor-dark-world-sequel-disney-2013` | `review-2026-09-03-thor-dark-world-sequel` |
| `work-relation-guardians-of-the-galaxy-2014-guardians-of-the-galaxy-vol-2-2017-sequel` | `marvel-guardians-vol2-sequel-2017` | `evidence-guardians-vol2-sequel-marvel-2017` | `review-2026-09-03-guardians-vol2-sequel` |
| `work-relation-black-panther-2018-black-panther-wakanda-forever-2022-sequel` | `marvel-black-panther-wakanda-forever-sequel-2022` | `evidence-black-panther-wakanda-forever-sequel-marvel-2022` | `review-2026-09-03-black-panther-wakanda-forever-sequel` |

## Evidence boundaries

- Walt Disney Company transcripts explicitly describe *Age of Ultron*, *The Winter Soldier*, and *The Dark World* as sequels to their respective earlier films. The *Age of Ultron* row intentionally retains its existing `probable` certainty; source verification does not silently upgrade certainty.
- Marvel describes *Guardians of the Galaxy Vol. 2* as a long-awaited sequel to the 2014 film.
- Marvel describes *Wakanda Forever* as a sequel continuing the world and characters of *Black Panther*.

These sources support the existing direct sequel relations only. They do not add release/status, production, chronology ordering beyond the relation kind, character identity, continuity, or multiverse transition facts. The intervening Avengers appearances in the Thor and Captain America branches remain separate edges and are not rewritten.

## Verification impact

The relation table remains 164 rows; five rows are added to the source-verified count, producing `18 source_verified`, `143 legacy_seed`, and `3 superseded`. Sources, evidence, and reviews become 55, 145, and 119. The derived graph remains 131 nodes, 355 edges, and 562 pair-reason rows; only the verification statuses of the five explicit relation reasons change.

Across→Beyond and the remaining legacy relation queue remain deferred until relation-specific official evidence is available.
