# Marvel Library DB v1 Production Status Evidence Promotion Batch 007

**Goal:** Promote the existing Avengers: Doomsday announced-status snapshot using the official Marvel Japan page while preserving all uncertainty boundaries.

**Scope:** `production-status-avengers-doomsday-2026-12-18-snapshot-2026-08-28` only. The matching U.S. theatrical release fact is already source-verified; the separate JP release row remains a legacy seed with a blank date.

**Evidence:** Marvel Japan's official Doomsday page lists the announced theatrical date of 2026-12-18: https://marvel.disney.co.jp/movie/avengers-doomsday

## Constraints

- Keep `status=announced`, `certainty=confirmed`, and `asserted_at=2026-08-28`.
- Add one primary evidence row and one `legacy_seed -> source_verified` review transition.
- Do not infer production milestones, territory changes, Japanese date precision, chronology, or graph edges.
- Keep canonical CSV rows RFC4180-shaped and record post-write hashes in the applied batch record.

## Verification

- RED contract: `tests/library_v5/test_production_status_evidence_promotion_batch007.py`.
- Full bundled-Python suite: 253 tests.
- Deterministic build: audit issues 0; content-audit issues 0; `work_edges_all=361`, `work_pair_reasons=569`, prewatch edges 199, story paths 83/83.
