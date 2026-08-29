# Marvel Library DB v1 Release and Production Status Evidence Promotion Batch 005

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the existing X-Men '97 Season 2 release date and current released-status snapshot using official Marvel/Disney evidence, without inferring a Japanese release date or territory.

**Architecture:** Preserve both existing fact IDs and all semantic fields (`unknown` territory, streaming, `2026-07-01`, `released`, `confirmed`, and `asserted_at=2026-08-28`). Add one release evidence/review pair tied to the existing Marvel announcement and one status evidence/review pair tied to an official Disney+ availability article. Keep the JP release row legacy_seed with its blank date; release/status facts remain outside graph derivation.

**Tech Stack:** Bundled Python 3.13, CSV, JSON, SHA-256, unittest, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` and `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md`.

## Global Constraints

- Canonical rows remain under `data/library/`; generated SQLite/audit outputs are disposable.
- A `source_verified` fact requires qualifying evidence and an auditable review transition.
- Do not infer JP date or territory from a non-JP source; preserve the JP row's blank `release_date` and `legacy_seed` status.
- Keep release `territory=unknown`; the Disney+ Australia page is availability evidence, not a Japanese-release assertion.
- Do not create graph edges, work-pair reasons, or chronology from release/status promotion.
- Use RED test, minimal canonical/evidence/review changes, strict CSV shape checks, full verification, and remote CI.

---

### Task 1: Add the RED contract

**Files:** Create `tests/library_v5/test_release_status_evidence_promotion_batch005.py`.

- [x] Assert the X-Men '97 S2 primary release and status snapshot fields, exact evidence source IDs, exact `legacy_seed -> source_verified` reviews, and the unchanged JP row.
- [x] Run the focused test with the bundled Python runtime and confirm it fails because the target rows have no evidence/review and remain `legacy_seed`.

---

### Task 2: Install the evidence-backed promotions

**Files:** Modify `data/library/sources.csv`, `data/library/releases.csv`, `data/library/production_status_assertions.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`; create `data/content_audit/applied/2026-08-30-release-status-evidence-promotion-batch005.json`.

- [x] Add `xmen97-s2-current-2026-08` for the official Disney+ article stating that Season 2 premiered on 2026-07-01 and is currently streaming.
- [x] Promote only the existing primary release and status snapshot; retain all dates, precision, certainty, territory, and JP-row boundaries.
- [x] Append one `primary` evidence row and one `verified_source` review for each fact, dated `2026-08-30`.
- [x] Record exact row counts and SHA-256 hashes in the applied record; every CSV row matches its header column count.

---

### Task 3: Verify, publish, and integrate

- [x] Update cumulative promotion contracts for the new verified status.
- [x] Run focused tests, the exact full bundled-Python suite, deterministic build, strict CSV shape scan, and `git diff --check`.
- [x] Confirm compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, prewatch edges `199`, and story paths `83/83`.
- [ ] Commit, push/open a PR against `main`, wait for CI, merge under the standing user authorization, confirm main and Pages, and rerun the clean post-merge verification.

