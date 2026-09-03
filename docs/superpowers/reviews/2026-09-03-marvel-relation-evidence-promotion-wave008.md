# Marvel Library v5 relation evidence promotion wave008 review

Date: 2026-09-03

## Decision

Four existing work relations were promoted from `legacy_seed` to `source_verified` using relation-specific official sources, primary evidence, and auditable review transitions. Existing IDs, directions, relation kinds, scopes, directness, certainty, notes, and graph topology were preserved.

| Relation | Source | Evidence | Review |
| --- | --- | --- | --- |
| Doctor Strange → Doctor Strange in the Multiverse of Madness | `disney-doctor-strange-second-film-2019` | `evidence-doctor-strange-multiverse-sequel-disney-2019` | `review-2026-09-03-doctor-strange-multiverse-sequel` |
| Black Panther: Wakanda Forever → Ironheart | `disney-ironheart-wakanda-forever-followup-2022` | `evidence-wakanda-forever-ironheart-followup-disney-2022` | `review-2026-09-03-ironheart-wakanda-forever-spinoff` |
| What If...? Season 1 → Marvel Zombies | `disney-what-if-s1-marvel-zombies-spinoff-2025` | `evidence-what-if-s1-marvel-zombies-spinoff-disney-2025` | `review-2026-09-03-what-if-s1-marvel-zombies-spinoff` |
| I Am Groot Season 1 → Season 2 | `marvel-i-am-groot-s1-s2-continuation-2023` | `evidence-i-am-groot-s1-s2-continuation-marvel-2023` | `review-2026-09-03-i-am-groot-s1-s2-sequel` |

## Evidence boundaries

- Disney describes *Multiverse of Madness* as the second film in the Doctor Strange franchise.
- Disney's D23 article places *Ironheart* after *Black Panther: Wakanda Forever* and says Riri Williams returns.
- Disney's Marvel Animation preview says the zombie episode in *What If...?* Season 1 inspired *Marvel Zombies* and discusses a sequel to that episode; the canonical relation remains `spinoff` and was not rewritten as `sequel`.
- Marvel presents *I Am Groot* Season 2 as picking right back up with Groot's journey.

These sources support only the existing relation semantics. No release/status, chronology, identity, Earth, multiverse-transition, or new work-pair facts were inferred. Other audited candidates, including Spider-Man (2002) → Spider-Man 2, remain deferred where the strict relation-specific evidence boundary is not met.

## Verification impact

- Relations: 164 total (`source_verified=39`, `legacy_seed=122`, `superseded=3`).
- Sources/evidence/reviews: `76 / 166 / 140`.
- Derived graph: `131` nodes, `355` edges, `562` reasons; prewatch edges `199`; story paths `83/83`.
- Connectivity audit: `47` pass, `528` deferred; projection mismatches `0`, reason orphans `0`, unsupported transition edges `0`.
- Bundled full suite: `453` tests passed, `4` environment-gated skips.
