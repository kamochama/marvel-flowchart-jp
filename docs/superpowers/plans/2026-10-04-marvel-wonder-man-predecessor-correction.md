# Wonder Man predecessor correction implementation plan

> For agentic workers: use superpowers:executing-plans task-by-task, with independent read-only review and ordinary non-Work ChatGPT review before integration.

**Goal:** Add the primary-source-supported Shang-Chi → Wonder Man predecessor connection without manufacturing long-range shortcut edges.

**Architecture:** One canonical work_relation owns the continuation. Build/export use existing derivation and viewer policies. No new appearance, identity, continuity, event, chronology, release, or UI code is needed to create this pair.

**Tech stack:** Canonical CSV, Python unittest/build, static JSON viewer, Chrome/CDP CI.

**Spec:** `docs/superpowers/reviews/2026-10-04-marvel-missing-connection-candidates.md`, including ordinary ChatGPT's narrowed design ruling. The user's approved all-work missing-line correction requires predecessor flow through intermediate works, not shortcuts. This plan remains separate from Wave022's existing-status promotions.

## Constraints and review focus

- Start a fresh codex/ branch from merged Wave022 main only after its CI, ChatGPT review and public verification pass. Do not mix this change into PR109.
- New relation ID: `work-relation-shang-chi-and-the-legend-of-the-ten-rings-2021-wonder-man-s1-2026-story-link`.
- Exact tuple: Shang-Chi source, Wonder Man S1 target, story_link/story/indirect/same_or_intended/probable/source_verified. Preserve uncertainty: not a direct sequel.
- Full note: `公式Disney+がトレヴァーのターローでの冒険を経てワンダーマンでハリウッドへ戻る流れを説明。直接続編とは断定しない。`
- Primary: https://www.disneyplus.com/en-sg/explore/articles/marvels-wonder-man , 6 February 2026, Trevor Slattery section. Exclude comics material and mere shared cast/creator information. Re-read the passage before canonical edits.
- Do not add Iron Man 3 → Wonder Man or All Hail the King → Wonder Man shortcut pairs from the same recap. Retain the existing upstream chain, whose All Hail → Shang-Chi seed requires a separate full-note audit.
- Do not silently relax graph-count compatibility tests. This justified topology change must be measured and explained, including any effect of the independent oracle and recursive predecessor selection.

## Task 1: Exact new fact and predecessor regression

Files: create `tests/library_v5/test_wonder_man_predecessor_correction.py`; modify only `data/library/work_relations.csv`, `sources.csv`, `evidence.csv`, and `data/content_audit/reviews.csv`.

- [ ] Write a failing test asserting exactly one proposed full tuple/note, one registered primary source URL, exact-fact primary evidence, and a `created_verified` review with blank previous status and the same evidence ID.
- [ ] Add a failing predecessor test: Wonder Man S1's selected recursive history contains Shang-Chi, All Hail the King, and Iron Man 3 through the existing chain. Assert no newly created long-range shortcuts from the latter two works to Wonder Man. Check existing upstream assertions, not manufactured evidence.
- [ ] Run the focused tests with bundled Python `-B`; require failure specifically because the new relation/evidence/review is absent, not an unrelated harness failure.
- [ ] Register source `disneyplus-wonder-man-trevor-continuation-2026`, evidence `evidence-shang-chi-wonder-man-trevor-continuation-2026`, review `review-2026-10-05-shang-chi-wonder-man-created` and only the exact new relation. Strict-check CSV widths and full per-file diffs. Review date uses the actual local date after midnight.
- [ ] Rebuild, run focused tests and inspect all generated changes. Expected new pair/reason is one each (355→356, 562→563); treat these as a hypothesis until observed. No unrelated canonical changes.

## Task 2: Verification, reviews, integration

Files: regenerate committed derived graph and explicit inventory, update only observed count fixtures affected by the proven new pair; create a dedicated execution/review ledger.

- [ ] Update count fixtures only after measured diff review; retain all direction, identity, provenance, transition fan-out and exact-set assertions.
- [ ] Run the full unittest suite, deterministic builds, protected canonical hashes, audit/content/review integrity, FK/integrity, strict CSV and CRLF-aware diff checks. Compare full exported JSON against the production base, not merely totals.
- [ ] Run all-work real-Chrome selection parity and interaction/chronology/publication/mobile/ownership audits through the seven-job CI gate. A matching selection oracle is not proof that all story connections are complete.
- [ ] Obtain independent full-diff and ordinary ChatGPT reviews with exact base/head, all changes and verification evidence. Resolve real findings; do not downgrade tests or semantics to mask browser failures.
- [ ] Push a normal feature PR, attach it, merge only reviewed exact head after all gates pass, then verify merged main, Pages exact SHA, HTTP 200 and deployed graph bytes.
- [ ] Record this correction as one resolved omission; keep unfinished 131-work research open and independently track all fact dispositions.
