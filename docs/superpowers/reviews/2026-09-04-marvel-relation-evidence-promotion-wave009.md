# Marvel Library v5 relation evidence promotion wave009 review

Date: 2026-09-04

## Decision

Four existing work relations were promoted from `legacy_seed` to `source_verified` using relation-specific official primary sources, primary evidence, and auditable review transitions. Their IDs, directions, relation kinds, scopes, directness, continuity scopes, certainty values, notes, and graph topology were preserved.

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| Avengers: Endgame → Spider-Man: Far From Home | `marvel-spider-man-far-from-home-endgame-aftermath-2019` | `evidence-endgame-far-from-home-aftermath-marvel-2019` | `review-2026-09-04-endgame-far-from-home-aftermath` |
| WandaVision → Doctor Strange in the Multiverse of Madness | `marvel-wandavision-mom-direct-connection-2019` | `evidence-wandavision-mom-direct-connection-marvel-2019` | `review-2026-09-04-wandavision-mom-story-link` |
| Ant-Man → Ant-Man and the Wasp | `marvel-ant-man-ant-man-wasp-sequel-2017` | `evidence-ant-man-ant-man-wasp-sequel-marvel-2017` | `review-2026-09-04-ant-man-ant-man-wasp-sequel` |
| X-Men: First Class → X-Men: Days of Future Past | `twentieth-xmen-first-class-days-crossover-2014` | `evidence-xmen-first-class-days-crossover-twentieth-2014` | `review-2026-09-04-xmen-first-class-days-crossover` |

## Evidence boundaries

- Marvel's *Spider-Man: Far From Home* page states that the film follows the events of *Avengers: Endgame*.
- Marvel's 2019 SDCC announcement states that *WandaVision* connects directly to *Doctor Strange in the Multiverse of Madness*'s storyline.
- Marvel's production announcement describes *Ant-Man and the Wasp* as the next chapter and sequel to *Ant-Man*.
- 20th Century Studios states that the original trilogy characters join their younger selves from *X-Men: First Class* in *Days of Future Past*.

The evidence supports only the existing relation semantics. No release/status, exact chronology, identity merge, Earth number, multiverse-transition, or new work-pair fact was inferred. The X-Men evidence does not collapse the Fox timelines; it only supports the existing crossover relation.

## Independent audit disposition

Three parallel read-only audits agreed that the selected relations were safe to promote only with provenance changes. Other candidates remain deferred when official wording was generic, pair-specific support was absent, or a relation would require a semantic inference (for example, catalog listing, shared cast, or a release-order claim).

## Verification impact

- Relations: 164 total (`source_verified=43`, `legacy_seed=118`, `superseded=3`).
- Sources/evidence/reviews: `80 / 170 / 144`.
- Derived graph: `131` nodes, `355` edges, `562` reasons; prewatch edges `199`; story paths `83/83`.
- Connectivity audit: `51` pass, `524` deferred; projection mismatches `0`, reason orphans `0`, unsupported transition edges `0`.
- Bundled full suite: `455` tests passed, `4` environment-gated skips.
- Real Chrome/CDP audits: selection, interaction, chronology, and publication-order contracts all passed; failures `0`, synthetic edges `0`.
