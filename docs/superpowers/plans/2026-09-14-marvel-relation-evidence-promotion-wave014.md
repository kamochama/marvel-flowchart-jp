# Marvel Library v5 relation evidence promotion — Wave014

## Boundary

This wave promotes exactly one existing `work_relations.csv` tuple:

- Daredevil Season 2 (2016) → The Punisher Season 1 (2017)

Netflix's official series-order announcement says that Frank Castle/the Punisher was introduced to viewers in the second season of *Daredevil* and is being expanded into “a show of his own.” That wording directly supports the existing `spinoff` tuple. It does not add a release date, chronology assertion, character-identity fact, or additional continuity claim.

The registered source URL is the canonical About Netflix announcement URL: `https://about.netflix.com/en/news/netflix-orders-marvels-the-punisher-to-series`.

The other Daredevil crossover/aftermath candidates remain separate bounded audits; no release/status/events/transitions rows are changed.

## Required provenance

- one source row for the exact Netflix announcement URL;
- one primary evidence row whose fact is the exact work-relation ID;
- one `legacy_seed` → `source_verified` review transition for that relation;
- no reuse of the source for unrelated facts.

## Verification

The RED test in `test_relation_evidence_promotion_wave014.py` must fail before the rows are added. GREEN requires the exact source/evidence/review linkage and preservation of the existing graph shape (355 edges, 562 reasons). Full unit tests, deterministic build, audit/content-audit/review-integrity checks, and browser CI are required before merge.
