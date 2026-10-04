# Relation evidence promotion Wave016

Base: `bb982ad495caf16c789c6935c4ba8586caf1a68e` (PR #102).

## Boundary

Audit the existing Defenders -> Luke Cage S2, Iron Fist S2, and Jessica Jones S2 story-link tuples. Promote only relations directly supported by a work-specific primary source. Keep all IDs, directions, kinds, strength, continuity scope, certainty, and notes unchanged. No new edges, identity, chronology, release/status, event, or transition facts; no viewer changes.

Marvel's 2016 Luke Cage Season 2 announcement explicitly places Luke's return after his Defenders appearance. This supports the existing story-link only; it does not establish a specific causal event or exact chronology. The other two candidates require independent direct support and otherwise remain deferred.

## Tasks

1. Confirm exact source text and classify each candidate independently.
2. Add a regression test for the exact preserved tuple and source/evidence/review join. Run bundled Python and observe RED before canonical edits.
3. Add minimal qualifying provenance and promote only supported rows; run focused GREEN tests.
4. Regenerate explicit-relation inventory and graph exports, preserving directed graph topology. Update the observed inventory counts, not audit thresholds.
5. Run full unit suite, deterministic build, canonical read-only checks, CSV shape checks, FK/integrity and diff checks. Obtain independent and ordinary non-Work ChatGPT review.
6. Push normal feature PR; require all hosted jobs GREEN before merge. Verify main and Pages after normal integration.

## Commands

Use the bundled Python executable with PowerShell `&` and `-B`. Focused command: `-m unittest tests.library_v5.test_relation_evidence_promotion_wave016 -v`. Full suite and build follow AGENTS.md. CI is the final real-Chrome verification gate. Do not weaken tests or promote unsupported neighboring tuples.
