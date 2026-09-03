# Marvel Library v5 variant fan-out audit

## Scope

This batch audits the two known shared-entity fan-out clusters identified by
the full connectivity audit: Logan/Wolverine around `deadpool-wolverine-2024`
and Loki across the Thor/Avengers and Loki seasons. It does not alter release
or production-status facts, chronology assertions, or UI tier policy.

## Wolverine decision

The Marvel Studios screenplay at
`https://assets.debut.disney.com/documents/Deadpool_Book_Single_Pages.pdf`
separates the exhumed Logan remains at the Logan grave from the Wolverine who
is later recruited. Mr. Paradox calls the recruit “any other Wolverine” and
“the worst Wolverine”; later dialogue refers to “the other Wolverine” and
“the wrong guy”. This is sufficient for a non-collapsing variant boundary but
does not establish an exact Earth number for the recruit.

Canonical correction:

- Added `entity-x-dw-wolverine-variant-2024`.
- Added verified `variant_of` relation
  `entity-relation-dw-wolverine-variant-of-logan-2017` to
  `entity-x-680db112c0`.
- Superseded the migration appearance
  `appearance-deadpool-wolverine-2024-entity-x-680db112c0` with review history,
  retaining its ID, and added the verified appearance
  `appearance-deadpool-wolverine-2024-entity-x-dw-wolverine-variant-2024`.
- Added qualifying evidence and created/superseding reviews for each changed
  fact. The existing source-verified Logan story-link relation remains active
  and is not replaced by a variant relation.

The correction removes six unsupported work-pair projections and seven shared
entity reasons involving the D&W recruit. The Logan 2017 → D&W pair remains
because its independent explicit story-link relation is still active. Derived
counts therefore change from 361 to 355 pairs and from 569 to 562 reasons.

## Loki decision

Defer the Loki split. The S1/S2 story plausibly follows the 2012 branch, but
the current canonical appearance rows are all legacy seeds and no qualifying
primary source is registered for a distinct Loki variant entity. The existing
Loki S1 → S2 sequel, Endgame → Loki S1 story-link, and Loki S2 → D&W TVA
institutional relation remain untouched. No TVA continuity or additional
transition is inferred.

## Verification

- RED regression tests were added before the canonical edit.
- Full bundled-Python suite: 437 tests passed, 4 environment-gated browser
  tests skipped.
- Build: audit issues 0, content-audit issues 0, SQLite export succeeded.
- Connectivity audit: structural failures 0, edge-pair mismatches 0, reason
  orphans 0, unsupported transition pairs 0.
