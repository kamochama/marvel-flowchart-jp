# Marvel Library v5 relation evidence promotion — Wave015

## Boundary

This wave promotes exactly one existing `work_relations.csv` tuple:

- The Defenders (2017) → Daredevil Season 3 (2018) aftermath

Marvel's official Season 3 article describes Matt's condition at the end of *The Defenders* and the care that leads into Season 3. That wording directly supports the existing `aftermath` tuple. It does not add a release date, a broader continuity/relaunch assertion, or a new identity fact.

The registered source URL is the Marvel article URL: `https://www.marvel.com/amp/articles/tv-shows/marvel-daredevil-season-3-creating-the-look`.

Daredevil Season 2 → The Defenders and other crossover/relaunch candidates remain separate bounded audits; no release/status/events/transitions rows are changed.

## Required provenance

- one source row for the exact Marvel article URL;
- one primary evidence row whose fact is the exact work-relation ID;
- one `legacy_seed` → `source_verified` review transition for that relation;
- no reuse of the source for unrelated facts.

## Verification

The RED test in `test_relation_evidence_promotion_wave015.py` must fail before the rows are added. GREEN requires the exact source/evidence/review linkage and preservation of the existing graph shape (355 edges, 562 reasons). Full unit tests, deterministic build, audit/content-audit/review-integrity checks, and browser CI are required before merge.
