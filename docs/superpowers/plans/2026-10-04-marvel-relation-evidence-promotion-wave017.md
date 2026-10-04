# Relation evidence Wave017 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans with TDD and independent read-only source/diff review.

**Goal:** Verify the existing Spider-Man 2 -> Spider-Man 3 sequel relation without changing its meaning or graph topology.

**Architecture:** Canonical CSV remains authoritative; add exact source/evidence/review provenance, then regenerate existing DB exports. No viewer or exporter policy change.

**Tech Stack:** CSV, bundled Python unittest/SQLite, existing Chrome/CDP CI.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`, sections 4.9-4.10 and 9.

Base: `3d61b4e8343be2397a7080273e05cac54c7d1c25` (merged PR #103, Pages run 37172650137 success).

## Global Constraints

- Preserve IDs, direction, kind, scope, directness, continuity scope, certainty and notes.
- Change only qualifying existing relation verification; no identity, chronology, release/status, event, transition or UI changes.
- No promotion of already verified Spider-Man (2002) -> Spider-Man 2.
- Daredevil S3 -> Born Again S1 is an independently researched candidate, not automatically included; series-level continuation alone does not establish exact season-3 endpoint.
- Preserve canonical/review input hashes across builds; preserve graph topology and all unrelated rows.

## Review Focus

- Sony FAQ explicitly names both endpoint films and continuation, not merely cast or release order.
- Evidence applies only to the existing Raimi sequel tuple, not MCU identity or numbered worlds.
- Exact fact/source/evidence/review joins and complete quoted CSV fields.
- Derived strength/importance changes must be identified as existing policy effects, not silently omitted.
- Deferred neighboring facts retain their current lines and values.

## Task 1: Exact-fact promotion and regression

**Files:** create `tests/library_v5/test_relation_evidence_promotion_wave017.py`; modify `data/library/{work_relations,sources,evidence}.csv` and `data/content_audit/reviews.csv`.

**Interface:** source `sony-spider-man-3-raimi-continuation-current`, URL `https://www.sonypictures.com/movies/spiderman3`; evidence `evidence-spider-man-2-to-3-sequel-sony-current`; review `review-2026-10-04-spider-man-2-to-3-sequel`; fact `work-relation-spider-man-2-2004-spider-man-3-2007-sequel`.

- [ ] Write test asserting preserved tuple `(spider-man-2-2004, spider-man-3-2007, sequel, story, direct, same_or_intended, confirmed)`, notes `Raimi trilogy.`, source_verified and exact primary provenance/review transition.
- [ ] Run bundled Python `-B -m unittest tests.library_v5.test_relation_evidence_promotion_wave017 -v`; expected RED at legacy status.
- [ ] Add one source, evidence and review; change only the fact's status. Sony FAQ describes the third/final trilogy film continuing the first two and following Spider-Man 2's events; do not copy that into separate chronology facts.
- [ ] Run focused test; expected GREEN.

## Task 2: Export, independent review and integration

**Files:** regenerate existing derived graph and `data/content_audit/reports/explicit_relation_inventory.{json,md}`; update observed test counts; add review report and current handoff/roadmap checkpoint.

**Interface:** consumes Task 1 provenance; produces deterministic exports and reviewable PR.

- [ ] Regenerate inventory and build; compare complete diffs and JSON scalar changes; expected topology 131 works / 355 edges / 562 reasons unchanged.
- [ ] Full bundled unit suite, deterministic build, CSV shape, FK/integrity, canonical read-only, CRLF-aware diff check; expected no issues.
- [ ] Independent reviewer and ordinary non-Work ChatGPT review with exact base/head/full PR diff.
- [ ] Push normal feature PR; all seven CI jobs must succeed before normal merge. Verify resulting main, Pages deployment and HTTP 200. Never bypass an unresolved failure.

## Execution record

Baseline suite: 621 tests OK, 6 gated skips. Native managed clean worktree reused on `codex/relation-evidence-wave017`; parent main/user untracked files protected. Standing repository authorization covers routine execution, feature push and reviewed normal PR integration; no direct main commits or history rewrite.
