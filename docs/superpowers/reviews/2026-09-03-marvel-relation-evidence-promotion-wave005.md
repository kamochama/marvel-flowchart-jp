# Marvel Library v5 relation evidence promotion wave005 review

Date: 2026-09-03

## Decision

Promote five existing relations from `legacy_seed` to `source_verified` with one official relation-specific source, primary evidence row, and review transition each:

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| `work-relation-iron-man-2008-iron-man-2-2010-sequel` | `paramount-iron-man-2-sequel-2010` | `evidence-iron-man-iron-man-2-sequel-paramount-2010` | `review-2026-09-03-iron-man-iron-man-2-sequel` |
| `work-relation-avengers-infinity-war-2018-avengers-endgame-2019-sequel` | `disney-infinity-war-endgame-sequel-2019` | `evidence-infinity-war-endgame-sequel-disney-2019` | `review-2026-09-03-infinity-war-endgame-sequel` |
| `work-relation-daredevil-s1-2015-daredevil-s2-2016-sequel` | `disney-daredevil-s1-s2-renewal-2015` | `evidence-daredevil-s1-s2-sequel-disney-2015` | `review-2026-09-03-daredevil-s1-s2-sequel` |
| `work-relation-what-if-s1-2021-what-if-s2-2023-sequel` | `marvel-what-if-s1-s2-continuation-2023` | `evidence-what-if-s1-s2-sequel-marvel-2023` | `review-2026-09-03-what-if-s1-s2-sequel` |
| `work-relation-loki-s1-2021-loki-s2-2023-sequel` | `marvel-loki-s1-s2-continuation-2023` | `evidence-loki-s1-s2-sequel-marvel-2023` | `review-2026-09-03-loki-s1-s2-sequel` |

## Boundaries

The official sources support only the existing sequel/season-continuation relations. Existing certainty values remain unchanged: Infinity War → Endgame and What If? S1 → S2 remain `probable`; all other targeted rows retain their existing values. What If? is an anthology/multiverse series, so no same-world or same-timeline claim is made. No release/status, chronology, identity, multiverse-transition, or new work-pair fact is added.

## Verification impact

The relation table remains 164 rows; five rows move to `source_verified`, producing `27 source_verified`, `134 legacy_seed`, and `3 superseded`. Sources, evidence, and reviews become 64, 154, and 128. Derived graph cardinality remains 131 nodes, 355 edges, and 562 pair-reason rows.

Spider-Verse, X-Men legacy, Across→Beyond, and other unreviewed relations remain deferred pending dedicated source-specific audits.
