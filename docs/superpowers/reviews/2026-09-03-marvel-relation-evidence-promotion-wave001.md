# Marvel Library relation evidence promotion wave001 review

## Scope and disposition

This batch promotes exactly two existing `work_relations.csv` seeds. No source
registry rows, entities, appearances, release/status facts, events,
transitions, continuity memberships, or chronology assertions were changed.

| relation fact | source evidence | disposition |
|---|---|---|
| `work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in` | [Marvel Japan, 2025-05-14](https://marvel.disney.co.jp/movie/thunderbolts/news/20250514_01) (`thunderbolts-doomsday`) and [Marvel Japan, 2025-04-30](https://marvel.disney.co.jp/movie/thunderbolts/news/20250430_04) (`thunderbolts-doomsday-turningpoint`) | `legacy_seed -> source_verified` |
| `work-relation-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31-story-link` | [Sony Pictures Japan, 2026-03-18](https://www.sonypictures.jp/corp/press/2026-03-18-0) (`bnd-sony-2026`) | `legacy_seed -> source_verified` |

The Thunderbolts* articles explicitly connect the film to `Avengers: Doomsday`
and describe it as a lead-in/turning point. The Sony release announcement
places `Brand New Day` four years after the events of `No Way Home` and calls it
the new chapter of the Tom Holland Spider-Man story. These statements support
the existing broad story relations only; they do not assert release-order
semantics beyond the existing relation, a multiverse transition, character
identity, or a production milestone.

## Exact audit records

- Evidence: `evidence-thunderbolts-doomsday-lead-in-marvel-jp-2025-05-14` (`primary`), `evidence-thunderbolts-doomsday-key-turning-point-marvel-jp-2025-04-30` (`supporting`), and `evidence-nwh-brand-new-day-story-link-sony-2026` (`primary`).
- Reviews: `review-2026-09-03-thunderbolts-doomsday-lead-in` and `review-2026-09-03-nwh-brand-new-day-story-link`.
- All evidence rows point to `fact_table=work_relations.csv` and the exact canonical relation ID. Each review records `legacy_seed -> source_verified` and references the corresponding evidence IDs.

## Verification

The two relation IDs, endpoint direction, relation kinds, certainty, explicit
reason IDs, and edge IDs are unchanged. The derived graph remains `131` nodes,
`355` work pairs, and `562` reasons; the existing Logan/Wolverine variant
correction is unaffected. The full bundled-Python suite, build, CSV shape
checks, and required browser audits are run at the PR integration gate.
