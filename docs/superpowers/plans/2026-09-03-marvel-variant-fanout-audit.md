# Marvel Library v5 Variant Fan-out Audit Plan

## Goal

Audit the known Logan/Wolverine and Loki shared-entity fan-out before any
canonical edit. Determine whether a source-backed `variant_of` boundary is
needed, and ensure that any later graph correction is limited to the affected
reasons.

## Scope

- `entity-x-680db112c0` (Logan/Wolverine) and `deadpool-wolverine-2024`
- `entity-x-55e230260e` (Loki) and Loki/Thor/Avengers appearances
- `entities.csv`, `entity_relations.csv`, `appearances.csv`,
  `work_relations.csv`, `work_continuities.csv`, events/transitions,
  evidence/reviews, and derived reason/export rows

Out of scope: release/status promotion, chronology redesign, UI tier policy,
and speculative additions based only on title, actor, or franchise membership.

## Method

1. Capture a fresh `main` baseline and canonical hash.
2. Run independent read-only audits for the Wolverine and Loki clusters and a
   source-backed relation queue.
3. Reconcile exact entity/appearance/reason IDs and classify each finding as
   `retain`, `needs-source`, `explicit-conflict`, or `defer`.
4. If and only if a concrete source-backed boundary is confirmed, add a RED
   regression test first, then apply the smallest canonical/evidence/review
   batch and regenerate the derived graph.
5. Run the full bundled-Python suite, build, connectivity audit, browser
   audits, and diff/hash checks before integration.

## Safety invariants

- Do not split an entity merely because a work is a multiverse crossover.
- `variant_of` is not `identity_of`; no alias collapse without explicit proof.
- Preserve existing fact IDs and keep unresolved legacy rows visible as
  deferred seeds.
- Do not use a shared entity or continuity membership to invent a missing
  work pair.
- Do not edit canonical CSVs concurrently from multiple agents.

## Current batch decision

- Wolverine/Logan: source-backed boundary confirmed by the official Deadpool & Wolverine screenplay. The grave's exhumed Logan remains and the recruited “other/wrong Wolverine” are distinct. The D&W appearance is therefore represented by `entity-x-dw-wolverine-variant-2024` with a verified `variant_of` relation to the legacy Logan/Wolverine entity. The old migration appearance remains as `superseded` for history.
- Loki: defer. The S1/S2 branch is plausible, but no qualifying primary evidence currently binds the canonical appearance rows to a distinct variant entity. Do not split on inference alone.
- Relation queue: defer to a subsequent bounded evidence batch; source registration alone is not fact-level proof.

## Verification target

The Wolverine boundary intentionally changes the derived shape from 361 to 355 work pairs and from 569 to 562 reasons: six unsupported D&W shared-entity pairs disappear, while the independently source-verified Logan story-link pair remains. This is a semantic correction, not a release/status or UI change.
