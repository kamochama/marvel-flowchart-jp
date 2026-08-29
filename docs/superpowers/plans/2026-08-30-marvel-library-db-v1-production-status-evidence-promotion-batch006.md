# Marvel Library DB v1 Release and Production Status Evidence Promotion Batch 006

**Goal:** Promote the existing VisionQuest announced-status snapshot with official Marvel evidence while preserving its announced status and avoiding unsupported production, territory, or Japanese-date claims.

**Scope:** `production-status-visionquest-2026-10-14-snapshot-2026-08-28` only. The matching release fact remains source-verified from batch001, with `territory=unknown`, `release_kind=streaming`, and `release_date=2026-10-14`.

**Evidence:** Marvel Television's official VisionQuest announcement states that the series will premiere on Disney+ on 2026-10-14: https://www.marvel.com/articles/tv-shows/marvel-television-visionquest-release-date?pubDate=20260513

## Constraints

- Keep `status=announced`, `certainty=confirmed`, and `asserted_at=2026-08-28`.
- Add one primary evidence row and one `legacy_seed -> source_verified` review transition.
- Do not infer production milestones, Japanese availability/date, territory, chronology, or graph edges.
- Keep canonical CSV rows RFC4180-shaped and record post-write hashes in the applied batch record.

## Verification

- RED contract: `tests/library_v5/test_release_status_evidence_promotion_batch006.py`.
- Full bundled-Python suite: 250 tests.
- Deterministic build: audit issues 0; content-audit issues 0; `work_edges_all=361`, `work_pair_reasons=569`, prewatch edges 199, story paths 83/83.
