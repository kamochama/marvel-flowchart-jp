# Relation evidence Wave018 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline; bounded independent source and full-diff reviewers remain read-only. Steps use checkbox syntax.

**Goal:** Verify only directly supported existing work relations without manufacturing connections.

**Architecture:** Preserve relation tuples and attach exact primary source/evidence/review transitions. Regenerate existing exports; existing policy may change strength/importance, never topology.

**Tech Stack:** Canonical CSV, bundled Python unittest/build, Chrome/CDP, GitHub Actions and Pages.

**Spec:** `AGENTS.md` canonical and integration rules; approved all-work connection audit continuation.

## Global Constraints

- Base `3506aeeb07ada4bae52d951ae69c5112a3cf6b85`, integrated Wave017, CI seven jobs green, Pages run 37174090086 succeeded.
- No viewer/export-policy changes or new identity, Earth, chronology, release/status, event/transition assertions.
- Candidate `work-relation-venom-let-there-be-carnage-2021-venom-the-last-dance-2024-story-link`: preserve story_link/story/direct/same_or_intended/probable and notes.
- Sony collection explicitly names both earlier adventures and the final trilogy film: https://www.sonypictures.com/movies/venom3moviecollection . Registration alone is not evidence.
- Iron Man 2 -> 3 and Fox Fantastic Four 2005 -> 2007 are independent source-audit candidates only; do not add them without a separately pinned exact regression and explicit support decision.
- Normal feature PR only; merge after independent and ordinary ChatGPT reviews and all seven CI jobs green.

## Review Focus

- Generic collection membership without story continuation must not promote a relation.
- Keep story_link and probable; do not silently upgrade to sequel or confirmed.
- Exact fact_table/fact_id provenance must not fan out to neighboring relations.
- Preserve all unrelated canonical rows and graph node/edge/reason IDs.
- Computed importance/strength differences must arise only from existing exporter policy.

## Task 1: Exact provenance regression and minimal promotion

**Files:** Create `tests/library_v5/test_relation_evidence_promotion_wave018.py`; modify only qualifying rows in sources.csv/evidence.csv/work_relations.csv and reviews.csv.

**Interfaces:** Consumes the fixed relation tuple above; produces one primary evidence and one legacy_seed -> source_verified / verified_source review.

- [ ] Write regression asserting exact tuple/notes, unique Sony source URL, primary evidence join and exact review transition; catches accidental ungrounded verification or endpoint rewrite.
- [ ] Run bundled Python `-B -m unittest tests.library_v5.test_relation_evidence_promotion_wave018 -v`; expect status assertion RED on legacy_seed.
- [ ] After source/ChatGPT support review, add source `sony-venom-trilogy-story-continuation-current`, evidence `evidence-venom-ltbc-last-dance-story-link-sony-current`, review `review-2026-10-04-venom-ltbc-last-dance-story-link`; status-only relation edit.
- [ ] Rerun exact regression GREEN, inspect every canonical diff and strict CSV shapes.

## Task 2: Full verification, review and integration

**Files:** Regenerate existing derived graph/inventory outputs; update inventory count observation and add review record/handoff checkpoint.

**Interfaces:** Consumes Task 1 provenance; produces reviewed feature commit and published normal merge only after all gates.

- [ ] Run full unittest suite; preserve unrelated historical deferred guards.
- [ ] Run deterministic read-only build and inventory after build; canonical/review hashes unchanged across rebuild; audit/content/review/FK 0 and integrity ok.
- [ ] Compare full JSON topology/metadata to base and verify 131 works / 355 edges / 562 reasons, prewatch 199 and 83 story paths.
- [ ] Commit bounded full diff after CRLF-aware whitespace check. Obtain independent read-only and ordinary non-Work ChatGPT final review on exact SHA.
- [ ] Push feature branch, attach PR, wait all seven CI jobs green; normal PR merge, fresh merged-main suite, exact-SHA Pages success and HTTPS HTTP 200.
- [ ] Record actual production verification in PR comments; never call broader audit complete solely from verified counts.
