# Marvel Library v5 relation evidence promotion wave005

Date: 2026-09-03

## Scope

Promote only these five existing `work_relations.csv` rows with relation-specific official primary evidence:

1. `work-relation-iron-man-2008-iron-man-2-2010-sequel`
2. `work-relation-avengers-infinity-war-2018-avengers-endgame-2019-sequel`
3. `work-relation-daredevil-s1-2015-daredevil-s2-2016-sequel`
4. `work-relation-what-if-s1-2021-what-if-s2-2023-sequel`
5. `work-relation-loki-s1-2021-loki-s2-2023-sequel`

Preserve existing IDs, endpoint direction, relation kind, directness, continuity, certainty, and notes. Add one primary `work_relations.csv` evidence row and one `legacy_seed -> source_verified` review transition per relation. Do not infer release/status, chronology, identity, multiverse transitions, or new work pairs. What If? remains a season-continuation display relation; no same-world or same-timeline claim is added.

## Sources

- Paramount's official Iron Man 2 release announcement (sequel to Iron Man).
- Walt Disney Company Investor Day 2019 transcript (Endgame follows Infinity War's fallout; existing certainty remains probable).
- Walt Disney Company FY15 earnings transcript (Daredevil Season 2 renewal after Season 1).
- Marvel's official What If...? Season 2 article (continues the journey).
- Marvel's official Loki article (Season 2 follows the Season 1 finale and opens a new chapter).

## RED/GREEN contract and verification

Focused tests must fail before data edits and pass afterward, checking exact source/evidence/review IDs, unchanged semantics, five explicit reason statuses, and fixed graph counts (131 nodes, 355 edges, 562 reasons). Run bundled-Python full tests, build, connectivity audit, and real Chrome selection/interaction/chronology/publication-order audits. Remaining Spider-Verse, X-Men legacy, and other relation queues remain deferred.
