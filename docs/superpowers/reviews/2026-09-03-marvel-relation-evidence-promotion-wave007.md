# Marvel Library v5 relation evidence promotion wave007 review

Date: 2026-09-03

## Decision

Promote four existing relations from `legacy_seed` to `source_verified` with official relation-specific evidence and review transitions:

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| `work-relation-the-amazing-spider-man-2012-the-amazing-spider-man-2-2014-sequel` | `sony-amazing-spider-man-1-2-sequel-2013` | `evidence-amazing-spider-man-1-2-sequel-sony-2013` | `review-2026-09-03-amazing-spider-man-1-2-sequel` |
| `work-relation-spider-man-far-from-home-2019-spider-man-no-way-home-2021-sequel` | `sony-spider-man-homecoming-third-film-2020` | `evidence-spider-man-far-from-home-no-way-home-sequel-sony-2020` | `review-2026-09-03-spider-man-far-from-home-no-way-home-sequel` |
| `work-relation-deadpool-2016-deadpool-2-2018-sequel` | `twentieth-deadpool2-sequel-2018` | `evidence-deadpool-deadpool2-sequel-twentieth-2018` | `review-2026-09-03-deadpool-deadpool2-sequel` |
| `work-relation-captain-marvel-2019-the-marvels-2023-sequel` | `disney-the-marvels-captain-marvel-sequel-2023` | `evidence-captain-marvel-the-marvels-sequel-disney-2023` | `review-2026-09-03-captain-marvel-the-marvels-sequel` |

## Boundaries

Sony explicitly calls *The Amazing Spider-Man 2* a sequel to *The Amazing Spider-Man*. Sony/Disney identify the third *Spider-Man: Homecoming* series film and reference the story turn in *Far From Home*. 20th Century Studios calls *Deadpool 2* the sequel to the first film. The Walt Disney Company describes *The Marvels* as a sequel to *Captain Marvel*. Existing certainty values remain unchanged. No release/status, chronology, identity, Earth number, multiverse-transition, or new work-pair fact is inferred. The *Spider-Man* (2002) → *Spider-Man 2* relation remains deferred because the available official catalog wording was not direct enough for this strict wave.

## Verification impact

The relation table remains 164 rows; four rows move to `source_verified`, producing 35 source_verified, 126 legacy_seed, 3 superseded. Sources/evidence/reviews become 72/162/136. Derived graph remains 131 nodes, 355 edges, 562 pair-reason rows.

Other Spider-Man, X-Men/FOX, Marvel TV, and remaining relation queues remain deferred pending dedicated evidence audits.
