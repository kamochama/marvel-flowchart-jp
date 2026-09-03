# Marvel Library relation evidence promotion wave001 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote only two existing work-relation seeds whose official source pages directly assert the relation, while preserving the derived graph and all semantic boundaries.

**Architecture:** Keep `work_relations.csv` as the canonical relation table. Attach exact fact-level evidence rows and auditable `legacy_seed -> source_verified` reviews using already registered official sources; do not add source rows, edges, transitions, chronology assertions, or character facts. Regenerate the deterministic DB/export and verify that relation IDs, pair direction, and graph shape remain unchanged.

**Tech Stack:** CSV, SQLite compiler/build, bundled Python `unittest`, GitHub Actions.

**Spec:** `AGENTS.md`, `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`, and `docs/superpowers/plans/2026-09-03-marvel-variant-fanout-audit.md`.

## Global Constraints

- Every promoted relation must have an exact `work_relations.csv` evidence row with `primary` or `supporting` role and a matching review transition.
- Use only the registered official sources `thunderbolts-doomsday`, `thunderbolts-doomsday-turningpoint`, and `bnd-sony-2026`; do not infer chronology, release/status, transition, identity, or continuity facts.
- Preserve existing relation IDs, source/target direction, relation kind, certainty, and notes.
- Canonical CSVs are edited only by the primary agent, sequentially; subagents remain read-only.
- The batch is limited to these two facts: Thunderbolts* -> Avengers: Doomsday and Spider-Man: No Way Home -> Spider-Man: Brand New Day.

---

### Task 1: Add the RED promotion contract

**Files:**
- Create: `tests/library_v5/test_relation_evidence_promotion_wave001.py`
- Create: this plan document

**Interfaces:**
- Consumes: `data/library/work_relations.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, and derived graph helpers.
- Produces: exact-ID assertions for the two relation promotions and graph-preservation checks.

- [ ] **Step 1: Write the failing test**

The test module must define these constants:

```python
THUNDERBOLTS = "work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in"
NWH_BND = "work-relation-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31-story-link"
```

Before the data change, assert both rows are `legacy_seed`, and assert that the exact evidence IDs and review IDs below are not yet present. A second test must derive the graph and require the two directed pairs, their existing explicit relation reason IDs, and the existing `355` edges / `562` reasons shape.

- [ ] **Step 2: Run the RED test**

Run:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave001 -v
```

Expected result: the promotion assertions fail because both relation rows are still `legacy_seed` and their evidence/review rows do not exist.

- [ ] **Step 3: Commit the RED test**

```powershell
git add tests/library_v5/test_relation_evidence_promotion_wave001.py docs/superpowers/plans/2026-09-03-marvel-relation-evidence-promotion-wave001.md
git commit -m "test: define relation evidence promotion wave001 contract"
```

### Task 2: Promote the two source-backed relation facts

**Files:**
- Modify: `data/library/work_relations.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`
- Create: `docs/superpowers/reviews/2026-09-03-marvel-relation-evidence-promotion-wave001.md`

**Interfaces:**
- Consumes: the exact relation IDs and source registrations from Task 1.
- Produces: two `source_verified` relation rows, three primary/supporting evidence rows, and two auditable reviews.

- [ ] **Step 1: Update only the two canonical relation statuses**

Change `verification_status` from `legacy_seed` to `source_verified` without changing any other field:

```text
work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in
work-relation-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31-story-link
```

- [ ] **Step 2: Add exact evidence rows**

Add these rows to `data/library/evidence.csv`:

```text
evidence-thunderbolts-doomsday-lead-in-marvel-jp-2025-05-14,work_relations.csv,work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in,thunderbolts-doomsday,primary,"Marvel Japan explicitly describes Thunderbolts* as a must-see work that leads into Avengers: Doomsday; this supports a broad story lead-in only.",2026-09-03
evidence-thunderbolts-doomsday-key-turning-point-marvel-jp-2025-04-30,work_relations.csv,work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in,thunderbolts-doomsday-turningpoint,supporting,"Marvel Japan describes Thunderbolts* as an important turning point connected to the Avengers: Doomsday project; no transition or chronology is inferred.",2026-09-03
evidence-nwh-brand-new-day-story-link-sony-2026,work_relations.csv,work-relation-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31-story-link,bnd-sony-2026,primary,"Sony Pictures Japan presents Brand New Day as the latest story four years after the events of No Way Home and identifies it as the new chapter of the Tom Holland Spider-Man story.",2026-09-03
```

- [ ] **Step 3: Add exact review transitions**

Add these reviews to `data/content_audit/reviews.csv`:

```text
review-2026-09-03-thunderbolts-doomsday-lead-in,work_relations.csv,work-relation-thunderbolts-new-avengers-2025-avengers-doomsday-2026-12-18-lead-in,legacy_seed,source_verified,verified_source,evidence-thunderbolts-doomsday-lead-in-marvel-jp-2025-05-14|evidence-thunderbolts-doomsday-key-turning-point-marvel-jp-2025-04-30,2026-09-03,"Promoted the existing broad story lead-in from two Marvel Japan pages; no release order, chronology, multiverse transition, or production milestone was added."
review-2026-09-03-nwh-brand-new-day-story-link,work_relations.csv,work-relation-spider-man-no-way-home-2021-spider-man-brand-new-day-2026-07-31-story-link,legacy_seed,source_verified,verified_source,evidence-nwh-brand-new-day-story-link-sony-2026,2026-09-03,"Promoted the existing Sony story-link relation; the four-year continuation statement does not add release/status, identity, or continuity facts."
```

- [ ] **Step 4: Run focused GREEN tests and strict CSV shape checks**

Run:

```powershell
& $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave001 tests.library_v5.test_content_audit tests.library_v5.test_db_compile -v
```

Every CSV row must have exactly the header column count; notes containing commas must remain quoted.

- [ ] **Step 5: Write the review report**

Record the two source URLs, paraphrased support, exact IDs, unchanged graph shape (`355` edges / `562` reasons), and explicit non-claims in `docs/superpowers/reviews/2026-09-03-marvel-relation-evidence-promotion-wave001.md`.

### Task 3: Full verification and integration gate

**Files:**
- Modify: generated `data/derived/flowchart.json`, `data/derived/work_edges_all.csv`, or `data/derived/work_pair_reasons.csv` only if deterministic regeneration changes them; otherwise keep them byte-identical.

**Interfaces:**
- Consumes: the canonical evidence/review promotion from Task 2.
- Produces: a verified branch ready for PR review with no graph fan-out or pair drift.

- [ ] **Step 1: Run full bundled-Python verification**

```powershell
& $MarvelPython -B -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
git diff --check
```

Expected: all tests pass, audit/content-audit issues are `0`, SQLite foreign keys are `0`, `integrity_check=ok`, and graph shape remains `131` nodes / `355` edges / `562` reasons.

- [ ] **Step 2: Run real browser audits when the branch is ready**

Run the existing selection, interaction, chronology, and publication-order browser contracts with their corresponding environment variables. All exact-set, interaction-state, chronology, and publication-order failures must be `0`.

- [ ] **Step 3: Review the full diff and open the PR**

Confirm no release/status, entity, appearance, event, transition, chronology, or source-registry rows changed. Push the branch, wait for all required CI jobs, and merge only after the normal PR gate; then verify `main`, Pages HTTP `200`, and the generated artifact.

