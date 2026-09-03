# Marvel Library v5 relation evidence promotion wave006 review

Date: 2026-09-03

## Decision

Promote four existing relations from `legacy_seed` to `source_verified` with official relation-specific evidence and review transitions:

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| `work-relation-spider-man-across-the-spider-verse-2023-spider-man-beyond-the-spider-verse-tba-sequel` | `sony-spider-verse-trilogy-beyond-2026` | `evidence-spider-man-across-beyond-trilogy-sony-2026` | `review-2026-09-03-spider-man-across-beyond-trilogy` |
| `work-relation-spider-man-into-the-spider-verse-2018-spider-man-across-the-spider-verse-2023-sequel` | `sony-spider-man-across-sequel-2024` | `evidence-spider-man-into-across-sequel-sony-2024` | `review-2026-09-03-spider-man-into-across-sequel` |
| `work-relation-x-men-the-animated-series-19921997-x-men-97-s1-2024-sequel` | `marvel-xmen97-original-series-timeline-2022` | `evidence-x-men-animated-series-x-men97-s1-timeline-marvel-2022` | `review-2026-09-03-x-men-animated-series-xmen97-s1` |
| `work-relation-spider-man-homecoming-2017-spider-man-far-from-home-2019-sequel` | `marvel-spider-man-far-from-home-homecoming-series-2019` | `evidence-spider-man-homecoming-far-from-home-next-chapter-marvel-2019` | `review-2026-09-03-spider-man-homecoming-far-from-home-sequel` |

## Boundaries

Sony describes *Beyond* as the conclusion of the Spider-Verse trilogy including *Across* and *Into*; a Sony release identifies *Across* as the sequel to *Into*. Marvel describes *X-Men '97* as new stories in the original series' iconic 90s timeline and calls *Far From Home* the next chapter of the *Homecoming* series. Existing certainty values remain unchanged: the *Into* → *Across* and X-Men relation remain `probable`. No MCU/legacy continuity equivalence, release/status, chronology, identity, Earth number, or multiverse-transition fact is inferred.

## Verification impact

The relation table remains 164 rows; four rows move to `source_verified`, producing `31 source_verified`, `130 legacy_seed`, and `3 superseded`. Sources, evidence, and reviews become 68, 158, and 132. The derived graph remains 131 nodes, 355 edges, and 562 pair-reason rows.

Other Spider-Verse, X-Men legacy, and remaining relation queues remain deferred pending dedicated evidence audits.
