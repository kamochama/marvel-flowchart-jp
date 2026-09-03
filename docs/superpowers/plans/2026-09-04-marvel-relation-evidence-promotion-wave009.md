# Marvel Library v5 relation evidence promotion wave009 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote four existing work relations to `source_verified` using relation-specific official primary sources, without changing relation semantics or graph topology.

**Architecture:** Keep the existing relation rows and derived graph as the semantic contract. Register one official source, one primary evidence row, and one auditable `legacy_seed -> source_verified` review row per selected relation; regenerate deterministic exports only to carry the verification metadata.

**Tech Stack:** UTF-8 CSV canonical data, Python `unittest`, bundled Codex Python runtime, deterministic SQLite/JSON/CSV build, GitHub Actions, and Chrome/CDP audits.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`

## Global Constraints

- Preserve existing relation IDs, directions, kinds, scopes, directness, continuity scopes, certainty, and notes.
- Use only relation-specific official primary sources; do not reuse release/status listing sources as relation evidence.
- Do not infer release/status, chronology facts, identity, Earth numbers, multiverse transitions, or new work pairs.
- Use `C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` with PowerShell's `&` call operator.
- Ordinary builds must leave canonical CSVs and persistent review history unchanged except for the intentional promotion rows.

---

### Task 1: Add the wave009 regression contract

**Files:**
- Create: `tests/library_v5/test_relation_evidence_promotion_wave009.py`
- Read: `data/library/work_relations.csv`, `data/library/sources.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, `data/derived/work_pair_reasons.csv`

**Interfaces:**
- Consumes the four existing relation IDs and their canonical endpoint/semantic fields.
- Produces exact assertions for source URLs, evidence links, review transitions, and unchanged graph counts.

- [ ] **Step 1: Write the failing test**

  Require these four relation IDs to be `source_verified` with exact source/evidence/review records while preserving their existing semantic fields:

  - `work-relation-avengers-endgame-2019-spider-man-far-from-home-2019-aftermath`
  - `work-relation-wandavision-2021-doctor-strange-in-the-multiverse-of-madness-2022-story-link`
  - `work-relation-ant-man-2015-ant-man-and-the-wasp-2018-sequel`
  - `work-relation-x-men-first-class-2011-x-men-days-of-future-past-2014-crossover`

  Also require `131` nodes, `355` edges, and `562` reason rows, with each selected explicit relation reason reporting `source_verified`.

- [ ] **Step 2: Run the focused test to verify RED**

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  & $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave009 -v
  ```

  Expected: FAIL because all four relations are still `legacy_seed` and their source/evidence/review IDs are absent.

### Task 2: Add source, evidence, and review records

**Files:**
- Modify: `data/library/work_relations.csv`
- Modify: `data/library/sources.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`

**Interfaces:**
- Existing relation rows remain keyed by their original IDs.
- Each source is referenced by exactly one primary evidence row; each review references that evidence ID.

- [ ] **Step 1: Promote only the four selected relation statuses**

  Change only `verification_status` from `legacy_seed` to `source_verified` for the four IDs in Task 1.

- [ ] **Step 2: Register official relation sources**

  Append these exact source IDs and URLs:

  - `marvel-spider-man-far-from-home-endgame-aftermath-2019` → `https://www.marvel.com/movies/spider-man-far-from-home?__=undefined`
  - `marvel-wandavision-mom-direct-connection-2019` → `https://www.marvel.com/articles/movies/sdcc-2019-marvel-studios-doctor-strange-in-the-multi-verse-of-Madness-announced`
  - `marvel-ant-man-ant-man-wasp-sequel-2017` → `https://www.marvel.com/articles/movies/marvel-studios-ant-man-and-the-wasp-begins-production`
  - `twentieth-xmen-first-class-days-crossover-2014` → `https://www.20thcenturystudios.com/movies/x-men-days-of-future-past`

- [ ] **Step 3: Append primary evidence rows**

  Use exact relation fact IDs and state only the supported relation: Far From Home follows Endgame; WandaVision connects directly to the Multiverse of Madness storyline; Ant-Man and the Wasp is the sequel/next chapter to Ant-Man; and Days of Future Past brings the original-trilogy characters together with the younger First Class characters. Do not add release, date, universe, variant, or chronology assertions.

- [ ] **Step 4: Append review transitions**

  Add one `verified_source` review dated `2026-09-04` per relation with `previous_verification_status=legacy_seed`, `new_verification_status=source_verified`, and the exact primary evidence ID.

### Task 3: Regenerate and verify deterministic outputs

**Files:**
- Modify generated `data/derived/work_pair_reasons.csv` and `data/derived/flowchart.json` only if the deterministic build changes them.

- [ ] **Step 1: Run focused wave009 tests**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave009 -v
  ```

- [ ] **Step 2: Run the complete bundled suite and build**

  ```powershell
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

  Expected: all tests pass; audit/content-audit issues remain zero; graph remains `131/355/562`; story paths remain `83/83`; FK and SQLite integrity remain clean.

- [ ] **Step 3: Run independent connectivity and browser audits**

  Confirm no projection mismatch, reason orphan, or unsupported transition edge, then run the real Chrome selection and interaction audits when the environment is available. CI remains authoritative if local Chrome is unavailable.

### Task 4: Review and integrate

**Files:**
- Create: `docs/superpowers/reviews/2026-09-04-marvel-relation-evidence-promotion-wave009.md`
- Update after semantic merge: `AGENTS.md`, `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`, `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`

- [ ] **Step 1: Inspect the complete diff**

  Run `git diff --check`, inspect every changed CSV row and generated artifact, and remove only known transient build outputs.

- [ ] **Step 2: Commit, push, and open a PR**

  Use branch `codex/relation-evidence-wave009`, commit message `feat: promote relation evidence wave009`, push to origin, and create a PR against `main`.

- [ ] **Step 3: Wait for CI and merge**

  Wait for all required checks, rerun only transient browser failures, merge through the normal PR path, and verify the resulting `main` SHA and Pages deployment.

- [ ] **Step 4: Record the new production baseline**

  Create a docs-only follow-up branch/PR with the merged SHA, CI/Pages run IDs, updated counts, and deferred queue; merge it and finish with a clean worktree.
