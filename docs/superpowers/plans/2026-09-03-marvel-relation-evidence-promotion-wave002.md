# Marvel Library relation evidence promotion wave002 Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

Goal: Promote four existing sequel/spinoff work-relation seeds whose official Marvel, Disney, or Disney+ sources directly state the relation, without changing graph topology or inventing chronology.

Architecture: Keep work_relations.csv canonical and attach exact relation-level evidence plus auditable legacy_seed to source_verified reviews. Register one missing official Disney source for the Agatha spinoff wording; reuse the existing VisionQuest and X-Men '97 Season 2 source registrations for the remaining facts. Regenerate only deterministic verification metadata in derived outputs.

Tech Stack: CSV, SQLite compiler/build, bundled Python unittest, GitHub Actions.

Spec: AGENTS.md, docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md, and docs/superpowers/plans/2026-09-03-marvel-relation-evidence-promotion-wave001.md.

## Global Constraints

- Every promoted relation must have exact work_relations.csv evidence and a matching review transition.
- Preserve relation IDs, source/target direction, relation kind, certainty, and existing notes.
- Do not infer release/status, chronology assertions, continuity, events, transitions, identity, or additional appearances.
- Canonical CSVs are edited sequentially by the primary agent; subagents remain read-only.
- The batch contains exactly four facts: the three Vision/Agatha/VisionQuest relations and X-Men '97 S1 -> S2. Across -> Beyond remains deferred.

---

### Task 1: Add the RED promotion contract

Files:
- Create: tests/library_v5/test_relation_evidence_promotion_wave002.py
- Create: this plan document

Interfaces:
- Consumes canonical relation/source/evidence/review rows and derived graph rows.
- Produces exact-ID assertions for four promotions, the new source registration, and graph-preservation checks.

- [ ] Step 1: Write the failing test

Define these constants in the test:

    WANDAVISION_AGATHA = "work-relation-wandavision-2021-agatha-all-along-2024-spinoff"
    AGATHA_VISIONQUEST = "work-relation-agatha-all-along-2024-visionquest-2026-10-14-sequel"
    WANDAVISION_VISIONQUEST = "work-relation-wandavision-2021-visionquest-2026-10-14-sequel"
    XMEN97_S1_S2 = "work-relation-x-men-97-s1-2024-x-men-97-s2-2026-07-01-sequel"

Assert all four relation rows are source_verified, the source registry contains disney-agatha-all-along-2024, each fact has the exact primary evidence below, and each review records legacy_seed -> source_verified. Assert the existing directed reason IDs and the graph shape of 131 nodes / 355 edges / 562 reasons.

- [ ] Step 2: Run the RED test

    $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    & $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave002 -v

Expected: failure because the four relations are still legacy_seed, the Disney source row is absent, and evidence/review rows do not exist.

- [ ] Step 3: Commit the RED test

    git add tests/library_v5/test_relation_evidence_promotion_wave002.py docs/superpowers/plans/2026-09-03-marvel-relation-evidence-promotion-wave002.md
    git commit -m "test: define relation evidence promotion wave002 contract"

### Task 2: Register sources and promote the four relations

Files:
- Modify: data/library/sources.csv
- Modify: data/library/work_relations.csv
- Modify: data/library/evidence.csv
- Modify: data/content_audit/reviews.csv
- Create: docs/superpowers/reviews/2026-09-03-marvel-relation-evidence-promotion-wave002.md

Interfaces:
- Consumes exact official source URLs and fact IDs from the read-only audit.
- Produces one new source row, four source_verified relation rows, four primary evidence rows, and four auditable reviews.

- [ ] Step 1: Register the missing Disney source

Add this exact source row to data/library/sources.csv:

    disney-agatha-all-along-2024,Agatha All Along relation,The Walt Disney Company,2024-09-17 article states WandaVision spinoff and creative segue,https://thewaltdisneycompany.com/news/a-magical-look-at-the-making-of-agatha-all-along-with-kathryn-hahn-and-jac-schaeffer/

- [ ] Step 2: Promote only the four relation statuses

Change only verification_status to source_verified for the four exact relation IDs from Task 1. Keep the non-adjacent WandaVision -> VisionQuest relation as its existing sequel kind, and explain in the review that this denotes the official trilogy link, not a new chronology assertion.

- [ ] Step 3: Add exact relation evidence

Add these primary evidence rows to data/library/evidence.csv:

    evidence-wandavision-agatha-spinoff-disney-2024,work_relations.csv,work-relation-wandavision-2021-agatha-all-along-2024-spinoff,disney-agatha-all-along-2024,primary,"The Walt Disney Company describes Agatha All Along as a WandaVision spinoff and a creative segue from WandaVision.",2026-09-03
    evidence-agatha-visionquest-trilogy-marvel-2026,work_relations.csv,work-relation-agatha-all-along-2024-visionquest-2026-10-14-sequel,visionquest,primary,"Marvel Television describes VisionQuest as the final installment in the trilogy begun with WandaVision and continued with Agatha All Along.",2026-09-03
    evidence-wandavision-visionquest-trilogy-marvel-2026,work_relations.csv,work-relation-wandavision-2021-visionquest-2026-10-14-sequel,visionquest,primary,"Marvel Television describes VisionQuest as the final installment in the trilogy begun with WandaVision; this supports the existing trilogy relation without asserting chronology.",2026-09-03
    evidence-xmen97-s1-s2-season-continuation-marvel-2026,work_relations.csv,work-relation-x-men-97-s1-2024-x-men-97-s2-2026-07-01-sequel,xmen97-s2,primary,"Marvel's official Season 2 article presents X-Men '97 as returning for and continuing into a second season.",2026-09-03

- [ ] Step 4: Add exact review transitions

Add these rows to data/content_audit/reviews.csv:

    review-2026-09-03-wandavision-agatha-spinoff,work_relations.csv,work-relation-wandavision-2021-agatha-all-along-2024-spinoff,legacy_seed,source_verified,verified_source,evidence-wandavision-agatha-spinoff-disney-2024,2026-09-03,"Promoted the existing WandaVision -> Agatha spinoff relation from the official Disney article; no character identity or chronology fact was added."
    review-2026-09-03-agatha-visionquest-trilogy,work_relations.csv,work-relation-agatha-all-along-2024-visionquest-2026-10-14-sequel,legacy_seed,source_verified,verified_source,evidence-agatha-visionquest-trilogy-marvel-2026,2026-09-03,"Promoted the existing Agatha -> VisionQuest trilogy relation; final-installment wording does not add a production milestone or release assertion."
    review-2026-09-03-wandavision-visionquest-trilogy,work_relations.csv,work-relation-wandavision-2021-visionquest-2026-10-14-sequel,legacy_seed,source_verified,verified_source,evidence-wandavision-visionquest-trilogy-marvel-2026,2026-09-03,"Promoted the existing non-adjacent trilogy link; the sequel kind is retained as a display relation and does not assert direct chronology."
    review-2026-09-03-xmen97-s1-s2-continuation,work_relations.csv,work-relation-x-men-97-s1-2024-x-men-97-s2-2026-07-01-sequel,legacy_seed,source_verified,verified_source,evidence-xmen97-s1-s2-season-continuation-marvel-2026,2026-09-03,"Promoted the existing Season 1 -> Season 2 continuation relation from Marvel's official Season 2 article; release metadata remains separate."

- [ ] Step 5: Run focused GREEN tests and strict CSV shape checks

    & $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave002 tests.library_v5.test_content_audit tests.library_v5.test_db_compile -v

Every CSV row must have exactly the header column count, with complete notes fields quoted when they contain commas.

### Task 3: Full verification and integration gate

Files:
- Modify: generated data/derived/flowchart.json and data/derived/work_pair_reasons.csv only for deterministic verification-status changes; do not alter pair counts.

Interfaces:
- Consumes Task 2 canonical source/evidence/review changes.
- Produces a PR-ready branch with no edge or reason fan-out.

- [ ] Step 1: Run full bundled-Python verification

    & $MarvelPython -B -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
    & $MarvelPython -m scripts.library_v5.build --repo-root .
    git diff --check

Expected: all tests pass, audit/content-audit issues 0, SQLite foreign keys 0, integrity_check=ok, and graph shape remains 131 nodes / 355 edges / 562 reasons.

- [ ] Step 2: Run the real browser contracts

Run selection, interaction, chronology, and publication-order audits with their corresponding environment variables. All exact-set, state, chronology, and publication-order failures must be 0.

- [ ] Step 3: Review, push, and integrate

Confirm no entity, appearance, release/status, event, transition, or chronology rows changed. Push the branch, wait for all required CI jobs, merge through the normal PR path, then verify main, Pages HTTP 200, and the public artifact.

