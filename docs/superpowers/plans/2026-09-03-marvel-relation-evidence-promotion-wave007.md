# Marvel Library v5 relation evidence promotion wave007 plan

Date: 2026-09-03

## Scope

Promote exactly four existing `work_relations.csv` rows from `legacy_seed` to
`source_verified` after registering one official, relation-specific source,
one primary evidence row, and one `legacy_seed -> source_verified` review
transition per relation:

1. *The Amazing Spider-Man* -> *The Amazing Spider-Man 2*;
2. *Spider-Man: Far From Home* -> *Spider-Man: No Way Home*;
3. *Deadpool* -> *Deadpool 2*; and
4. *Captain Marvel* -> *The Marvels*.

Existing IDs, directions, relation kinds, directness, continuity scope,
certainty, and graph projection remain unchanged. No release/status,
chronology, character identity, universe, or multiverse-transition fact is
added. The candidate *Spider-Man* (2002) -> *Spider-Man 2* remains deferred in
this strict wave because the available official catalog wording does not
directly identify the predecessor pair.

## Evidence boundaries

- Sony's 2013 production release explicitly calls *The Amazing Spider-Man 2*
  the sequel to *The Amazing Spider-Man*.
- Sony/Disney's 2020 announcement identifies the third film in the
  *Spider-Man: Homecoming* series and explicitly references the story turn in
  *Far From Home*; this supports the existing Far From Home -> No Way Home
  relation without rewriting its semantics.
- 20th Century Studios calls *Deadpool 2* the sequel to the first film.
- The Walt Disney Company describes *The Marvels* as the sequel to *Captain
  Marvel*.

## Verification gate

Add a focused regression test before data edits. It must fail while the
relation rows/evidence/reviews are absent and pass after the exact records are
added. Run the bundled-Python full suite, ordinary build, independent
connectivity audit, and all real Chrome selection/interaction/chronology/
publication-order audits. Review the complete diff, then merge only through a
PR after all required CI checks pass.
