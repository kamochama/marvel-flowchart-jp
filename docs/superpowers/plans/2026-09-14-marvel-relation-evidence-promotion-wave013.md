# Marvel Library v5 relation evidence promotion — Wave013

## Boundary

This wave promotes exactly one existing `work_relations.csv` tuple:

- `Daredevil: Born Again` Season 2 (2026) → Season 3 (TBA)

The Disney UK Press source dated 2025-10-14 states that Season 3 was already in the works while covering Season 2. The evidence is restricted to the existing adjacent `sequel` relation. It does not add a release date, production milestone, Netflix-era continuity assertion, or identity claim.

The registered source URL is the canonical Disney UK Press article URL: `https://press.disney.co.uk/news/marvel-television-and-marvel-animation-new-york-comic-con-panel-gives-a-first-look-at-upcoming-disney%2B-slate-with-exclusive-footage-and-surprise-guests`.

The following candidates remain deferred because their official wording is not relation-specific enough for this strict wave: Spider-Man 2 → Spider-Man 3, Iron Man 2 → Iron Man 3, the original Fox X-Men sequence, Blade II, and Fantastic Four (2005) → Rise of the Silver Surfer. No release/status/events/transitions rows are changed.

## Required provenance

- one source row for the exact Disney UK Press URL;
- one primary evidence row whose fact is the exact work-relation ID;
- one `legacy_seed` → `source_verified` review transition for that relation;
- no reuse of the source for unrelated facts.

## Verification

The RED test in `test_relation_evidence_promotion_wave013.py` must fail before the rows are added. GREEN requires the exact source/evidence/review linkage and preservation of the existing graph shape (355 edges, 562 reasons). Full unit tests, deterministic build, audit/content-audit/review-integrity checks, and browser CI are required before merge.
