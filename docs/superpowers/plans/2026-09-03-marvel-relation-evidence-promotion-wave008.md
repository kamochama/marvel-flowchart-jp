# Marvel Library v5 relation evidence promotion wave008 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote exactly four existing work relations to `source_verified` using official relation-specific evidence and auditable review transitions, without changing relation semantics or graph shape.

**Architecture:** Keep canonical relation rows as the semantic source of truth. Register one official source, one primary evidence row, and one `legacy_seed -> source_verified` review row for each selected relation; regenerate deterministic derived exports so verification metadata is traceable without creating or deleting work pairs.

**Tech Stack:** UTF-8 CSV canonical data, Python `unittest`, bundled Codex Python runtime, deterministic SQLite/JSON/CSV build, GitHub Actions and Chrome/CDP audits.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`

## Global Constraints

- Preserve existing primary keys, directions, relation kinds, scopes, directness, certainty, and notes.
- Add only work-specific official sources, primary evidence, and auditable review transitions; do not use release/status sources as relation evidence.
- Do not infer release/status, chronology, identity, Earth numbers, multiverse transitions, or new work pairs.
- Use the bundled runtime at `C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` with PowerShell's `&` call operator.
- Ordinary build must leave canonical CSVs and persistent review history unchanged except for the intentional promotion rows.

---

### Task 1: Add the wave008 regression contract

**Files:**
- Create: `tests/library_v5/test_relation_evidence_promotion_wave008.py`
- Test data: `data/library/work_relations.csv`, `data/library/sources.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, `data/derived/work_pair_reasons.csv`

**Interfaces:**
- Consumes the four existing relation IDs and their canonical endpoint/semantic fields.
- Produces assertions requiring exact source URLs, evidence links, review transitions, and unchanged graph counts after promotion.

- [ ] **Step 1: Write the failing test**

  Assert that these four relations have exact source/evidence/review records and `source_verified` status while preserving their existing semantics:

  - `work-relation-doctor-strange-2016-doctor-strange-in-the-multiverse-of-madness-2022-sequel`
  - `work-relation-black-panther-wakanda-forever-2022-ironheart-2025-spinoff`
  - `work-relation-what-if-s1-2021-marvel-zombies-s1-2025-spinoff`
  - `work-relation-i-am-groot-s1-2022-i-am-groot-s2-2023-sequel`

  Also assert that the derived exports still contain `131` nodes, `355` edges, and `562` reason rows, and that each explicit relation reason reports `source_verified`.

- [ ] **Step 2: Run the focused test to verify RED**

  Run:

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  & $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave008 -v
  ```

  Expected: FAIL because the four new source IDs, evidence IDs, and review IDs are not yet present and the relations remain `legacy_seed`.

### Task 2: Add source, evidence, and review records

**Files:**
- Modify: `data/library/work_relations.csv`
- Modify: `data/library/sources.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`

**Interfaces:**
- Existing relation rows remain keyed by their original `work_relation_id`.
- Each new source ID is referenced by exactly one primary evidence row; each review references that evidence ID.

- [ ] **Step 1: Promote only the four selected relation statuses**

  Change `verification_status` from `legacy_seed` to `source_verified` for the four IDs in Task 1. Leave every other field byte-for-byte unchanged.

- [ ] **Step 2: Register the official sources**

  Append these source records with the exact official URLs and relation-specific purposes:

  - `disney-doctor-strange-second-film-2019` → `https://thewaltdisneycompany.com/news/marvel-studios-reveals-plans-for-phase-four-at-san-diego-comic-con/`
  - `disney-ironheart-wakanda-forever-followup-2022` → `https://thewaltdisneycompany.com/news/lucasfilm-marvel-studios-and-20th-century-studios-showcase-electrifying-new-slate-at-d23-expo-2022/`
  - `disney-what-if-s1-marvel-zombies-spinoff-2025` → `https://thewaltdisneycompany.com/news/marvel-animation-2025-sneak-peek/`
  - `marvel-i-am-groot-s1-s2-continuation-2023` → `https://www.marvel.com/tv-shows/i-am-groot/1?mobile-app=true&theme=falseCampfire`

- [ ] **Step 3: Append primary evidence rows**

  Use evidence IDs and exact fact IDs from Task 1. Notes must state only the supported relation: Doctor Strange is the franchise's second film; Ironheart is set after Wakanda Forever; Marvel Zombies derives from the zombie What If...? concept without changing `spinoff` semantics; and I Am Groot Season 2 continues the series. Do not add chronology, continuity, identity, or release claims.

- [ ] **Step 4: Append review transitions**

  Add one `verified_source` review per relation dated `2026-09-03`, with `previous_verification_status=legacy_seed`, `new_verification_status=source_verified`, and the exact primary evidence ID.

### Task 3: Regenerate and verify deterministic derived outputs

**Files:**
- Modify: `data/derived/work_pair_reasons.csv`
- Modify: `data/derived/flowchart.json`

- [ ] **Step 1: Run the focused test**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave008 -v
  ```

  Expected: PASS after the canonical rows and build outputs are updated.

- [ ] **Step 2: Run the bundled full suite and build**

  ```powershell
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

  Expected: all tests pass; audit/content-audit issues are `0`; graph remains `131/355/562`; story paths remain `83/83`; no foreign-key or SQLite integrity failures.

- [ ] **Step 3: Run independent connectivity and real Chrome audits**

  Confirm `pass=47`/`deferred=528` after the four promotions, projection mismatches `0`, reason orphans `0`, unsupported transition edges `0`, plus real Chrome selection, interaction, chronology, and publication-order audits with zero failures and zero synthetic edges.

### Task 4: Review and integrate

**Files:**
- Create: `docs/superpowers/reviews/2026-09-03-marvel-relation-evidence-promotion-wave008.md`
- Update: `AGENTS.md`, `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`, and `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md` in a docs-only follow-up after semantic merge.

- [ ] **Step 1: Review the complete diff**

  Run `git diff --check`, inspect all canonical CSV rows and generated changes, and remove only known transient build outputs.

- [ ] **Step 2: Commit and push the semantic branch**

  Commit with `feat: promote relation evidence wave008`, create a PR against `main`, and wait for all required CI jobs.

- [ ] **Step 3: Merge and verify production**

  Merge after CI is green, verify the resulting `main` SHA and Pages deployment, then confirm the public site and `data/derived/flowchart.json` return HTTP `200` with the expected graph counts.

- [ ] **Step 4: Record the new baseline**

  Create a docs-only branch/PR updating the persistent handoff, roadmap, and `AGENTS.md` with the merged SHA, CI/Pages run IDs, counts, and remaining deferred queue. Merge it and verify the final worktree is clean.
