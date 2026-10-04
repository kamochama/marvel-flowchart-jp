# Relation evidence promotion wave023 — local verification

Base: `e6e70c2fb3433aa007f4312e0f4b044b968b712d` (PR111).
Plan: `docs/superpowers/plans/2026-10-05-marvel-relation-evidence-promotion-wave023.md`.

## Exact scope

Three existing relations changed only from `legacy_seed` to `source_verified`:

- Captain Marvel -> Endgame: crossover/story/direct, Carol joining the Avengers side.
- Endgame -> Loki S1: story_link/story/direct, the 2012 Tesseract branch starting point.
- Captain Marvel -> Secret Invasion: world_lore/world_lore/indirect, Fury/Talos and the unresolved Skrull homeland problem.

IDs, directions, certainty, continuity scope and complete original notes are
unchanged. Four official sources, four primary evidence rows and three exact
`verified_source` review transitions were added. The Endgame relation's review
references both evidence rows. Registry URLs/IDs are unique.

Disney's 2019 next-appearance article and Disney+ Press's 2023 Carol LEGENDS
synopsis support the first relation jointly, not formal team membership.
Loki's official production brief printed p.1 supports the second without
collapsing the 2012 variant into the mainline identity. Secret Invasion's 2023
production brief printed pp.2-3,5 supports the third; evidence explicitly
excludes same rebel faction, same invasion event, direct sequel and new
event/identity/chronology facts. The ambiguous 2021 comic-event source is not used.
Official URLs and paraphrase locators are recorded in sources/evidence CSVs.

## Fresh verification

- Baseline: 634 tests OK / seven skips, 32.829 seconds.
- New exact-fact regression: RED, three failures solely at verification status;
  minimal CSV update -> GREEN, three tests.
- First full candidate run: 637 tests, one failure from the inventory test's
  historical 76/86 status snapshot. Updated to the actual 79/83 split; total,
  active, superseded and provenance/projection checks remain unchanged.
- Final full candidate suite: 637 tests OK / seven skips, 32.717 seconds.
- Two deterministic builds: canonical/review hashes unchanged by ordinary
  build; flowchart, edge/reason CSVs and logical DB manifest hashes identical.
- Strict shapes and entire canonical comparison against base: only the three
  status fields and the additive four sources/four evidence/three reviews.
- Build audit/content issues 0; SQLite FK0 and integrity `ok`.
- Connection and explicit-relation inventories: all structural/provenance
  failures 0. Inventories are regenerated scratch outputs, not new source facts.
- `git diff --check`: clean.

## Complete graph comparison

Recursive comparison of every field against base yields exactly 16 leaf changes:
four presentation fields (importance/Japanese label/explanation/strength) on
each of the three intended existing edges, three corresponding explicit-reason
verification statuses, and the canonical-derived logical fingerprint.
The three edges change `reference/weak` -> `recommended/strong` under unchanged
export policy. This includes the indirect world-lore edge: stronger display
does not turn it into a direct sequel.

All other graph fields, ordering, edge/reason IDs and endpoints are identical.
Nodes/edges/reasons remain 131/356/563; prewatch199 and story paths83/83.
Relations165 = verified79 / seeds83 / superseded3; sources/evidence/reviews
118/208/180. Graph SHA256:
`91ADEF689A97FCE1708F1F0F322B1CABDB9CFEC6E6F794FA03223685D233E7CC`.
No viewer, workflow, export-policy or other canonical-domain changes.

## Remaining gates and limits

Local opt-in Chrome audits are not rerun at the user's explicit request.
All seven existing required CI jobs remain unchanged integration gates.
Independent Luna and ordinary ChatGPT exact-head full-diff implementation
reviews, CI, normal PR integration, Pages and public-artifact verification
are pending. Plan approval is not implementation approval.

All131-work semantic audit remains unfinished. Structural coverage/projection
success does not establish semantic completeness. Unexamined cases remain
research_open, not automatically deferred. Existing deferred/conflict history
is preserved; no unrelated relation was removed.
