# Relation evidence Wave019 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline with read-only independent source/full-diff review.

**Goal:** Verify the existing Iron Man 2 -> Iron Man 3 sequel from the official production-notes story discussion.

**Architecture:** Preserve the exact canonical tuple and attach primary evidence with an auditable status transition. Rebuild existing graph exports without viewer or policy changes.

**Tech Stack:** CSV, bundled Python unittest/build, Chrome/CDP and GitHub CI/Pages.

**Spec:** `AGENTS.md` canonical/integration rules and approved all-work evidence audit continuation.

## Global Constraints

- Base `e21a2606a22ad30473b16f53cd03ad187c1dbf05`, PR #105 published, merged-main 623 tests OK / 6 gated skips.
- Only `work-relation-iron-man-2-2010-iron-man-3-2013-sequel` status may change. Preserve sequel/story/direct/same_or_intended/confirmed and `Iron Man trilogy direct franchise line.` notes.
- Primary PDF https://i.annihil.us/u/prod/avengersmovie/ironman3/fullsite1/pdf/Iron_Man_3_Notes.pdf page 2 THE STORY, interpreted with the preceding named Iron Man / Iron Man 2 context.
- Preserve historical Wave012/013 documents; update only obsolete current-state assertions for this exact fact.
- Do not promote Avengers -> Iron Man 3, create Iron Man 1 -> 3 shortcut, or change release/status, chronology, identity, events/transitions, viewer or exporter policy.

## Review Focus

- Resolve first-two-films referent using named context, not title numbering alone.
- Keep Avengers follow-up support separate from the selected Iron Man pair.
- Exact source/evidence/review joins must not fan out to neighbors.
- Historical defer statements remain historical; unrelated seed guards remain intact.
- Preserve all graph IDs/topology; changes in strength/importance follow existing policy only.

## Task 1: Exact provenance contract and bounded promotion

**Files:** Create `tests/library_v5/test_relation_evidence_promotion_wave019.py`; modify exact rows in sources/evidence/work_relations/reviews CSV.
**Interfaces:** Fixed relation tuple -> source `marvel-iron-man-3-first-two-films-sequel-2013`, primary evidence `evidence-iron-man-2-iron-man-3-sequel-marvel-2013`, review `review-2026-10-04-iron-man-2-iron-man-3-sequel`.

- [ ] Add exact status/tuple/notes/provenance regression; catches unsupported verification, altered endpoint or evidence misjoin.
- [ ] Run bundled Python `-B -m unittest tests.library_v5.test_relation_evidence_promotion_wave019 -v`; expect RED on legacy_seed before edit.
- [ ] After source reviews, add three provenance rows and change only relation status to source_verified.
- [ ] Exact regression GREEN; inspect canonical diff/strict shapes.

## Task 2: Verification and reviewed production integration

**Files:** Existing derived/inventory exports, inventory count test, only necessary old current-state tests, new review/ledger, handoff/roadmap checkpoint.
**Interfaces:** Task 1 exact provenance -> deterministic audited exports and reviewed feature commit.

- [ ] Full suite; diagnose any historical guard failure before updating this fact only. Keep exact Wave019 provenance test and all unrelated guards.
- [ ] Build then inventory; rebuild canonical/review hashes and export hashes unchanged; audit/content/review/FK issues 0 and SQLite integrity ok.
- [ ] Full JSON structure comparison and 131/355/562 topology, prewatch 199, story paths 83/83 preserved.
- [ ] CRLF-aware whitespace check and small commit; independent/ordinary non-Work ChatGPT full-diff reviews on exact SHA.
- [ ] Push normal feature PR and attach; all seven CI jobs GREEN before normal merge; merged-main full suite and exact-SHA Pages/HTTPS HTTP 200 afterward.
- [ ] Record production evidence in PR comments; this is not completion of the whole-work audit.
