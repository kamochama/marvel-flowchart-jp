# Relation evidence promotion Wave021

Base: `5e44ae2402816c9101034f3198d4d1571a64f7c3` (PR107). Part of the approved all-work audit closure plan, not its completion.

## Bounded change

Promote exactly three existing `work_relations.csv` rows from `legacy_seed` to `source_verified`; preserve IDs, endpoints, kind, scope, directness, continuity, certainty and notes.

- Endgame → The Falcon and the Winter Soldier: official production brief printed p.2 expressly roots the series in Steve handing Sam the shield in Endgame.
- Civil War → Homecoming: Sony's original ABOUT synopsis follows Peter's Civil War debut and experience with the Avengers into his return home. This is not formal Avengers membership.
- The Falcon and the Winter Soldier → Brave New World: Disney's July 12 2024 teaser and February 13 2025 producer interview explicitly continue Sam's Captain America story. Existing `strong` is retained, not newly inferred as a measurement from prose.

Sources: official Disney/Marvel production brief, Sony film synopsis, Disney teaser article and producer interview. Four sources and four primary evidence rows, three exact review transitions. No other fact or viewer changes.

## Execution

1. Exact-row provenance regression RED before CSV writes.
2. Minimal four-file CSV patch; strict shape check and independent full diff inspection.
3. GREEN focused/full suite, deterministic build, canonical immutability during build, graph/reason compatibility, audit/review/FK/integrity checks.
4. Regenerate independent connection and explicit-relation inventories; examine expected provenance/status-only changes.
5. Independent read-only diff review and ordinary ChatGPT full-diff review, all seven CI jobs, normal PR merge, main/Pages/public artifact checks.
6. Continue remaining relation research and separate missing-line/supporting-domain audits. This wave is not all-work semantic closure.

## Explicit exclusions

Civil War → FATWS new explicit relation is a separate batch. Civil War → Black Panther's Wakanda-first-appearance note and Endgame → Loki's not-yet-read primary passage are not promoted here. No chronology, character membership, shield event, transition, release/status or new work pair is created.

Ordinary ChatGPT reviewed the actual source plan on 2026-10-04: all three PROMOTE; recommended four sources/four evidence/three reviews and the exclusions above. Main agent independently read the primary text before that review.
