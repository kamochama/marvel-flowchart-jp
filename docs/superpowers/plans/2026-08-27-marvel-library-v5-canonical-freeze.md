# Marvel Library v5 Canonical Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the migration prototype into a frozen canonical Marvel library whose ordinary build is read-only, while keeping bootstrap reconstruction reproducible and adding persistent content-audit history.

**Architecture:** `data/library/` becomes persistent canonical input. `scripts.library_v5.build` reads canonical facts, validates them, and regenerates only downstream products; the old migration writers move behind `scripts.library_v5.bootstrap` and stage candidate canonical snapshots under `data/migration/bootstrap/`. Persistent review decisions live in `data/content_audit/reviews.csv`, while queue/report files are generated from current canonical status.

**Tech Stack:** Python 3.12 standard library (`csv`, `json`, `hashlib`, `pathlib`, `shutil`, `tempfile`, `unittest`), CSV/JSON, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-v5-canonical-bootstrap-separation-design.md`

## Global Constraints

- Production `main` remains unchanged until explicit integration approval.
- `data/library/` is canonical input and ordinary build/CI must not modify it.
- Bootstrap reconstruction is explicit and stages under `data/migration/bootstrap/` by default.
- Installing bootstrap data over canonical facts is never implicit.
- Generated manifest lives under `data/derived/`, not `data/library/`.
- Persistent human review history is never deleted by ordinary clean build.
- `source_verified` requires qualifying evidence; legacy evidence alone cannot promote a fact.
- Derived edge counts are observations, not correctness targets.
- Internal IDs may remain English; user-facing flowchart labels remain Japanese.
- Implementation remains dependency-free and deterministic.

---

### Task 1: Freeze canonical inputs and make ordinary build read-only

**Files:**
- Create: `scripts/library_v5/canonical_guard.py`
- Modify: `scripts/library_v5/build.py`
- Modify: `scripts/library_v5/audit.py`
- Create: `tests/library_v5/test_canonical_freeze.py`

**Interfaces:**
- Produces: `canonical_hashes(repo_root: Path) -> dict[str, str]`
- Produces: `assert_canonical_unchanged(before: dict[str,str], after: dict[str,str]) -> None`
- Ordinary `build(repo_root, clean=True)` regenerates only `data/derived/`, generated audit reports, generated content-audit queue/report, and view outputs.

- [ ] **Step 1: Write failing tests** asserting ordinary build preserves every byte under `data/library/`, does not call legacy migration writers, and moves the generated manifest to `data/derived/library_manifest.json`.
- [ ] **Step 2: Run** `python -m unittest tests.library_v5.test_canonical_freeze -v` and verify RED for the current destructive build behavior.
- [ ] **Step 3: Implement** canonical SHA helpers and refactor build cleanup so it removes only safe generated paths/files. Refactor manifest generation to hash canonical inputs separately from generated outputs and write only under `data/derived/`.
- [ ] **Step 4: Run** the focused tests and the full `tests/library_v5` suite; verify GREEN.
- [ ] **Step 5: Commit** `refactor: freeze library v5 canonical inputs`.

### Task 2: Separate deterministic bootstrap reconstruction

**Files:**
- Create: `scripts/library_v5/bootstrap.py`
- Modify: migration writers only as needed to support a staging root rather than hard-coded `data/library/` writes.
- Create: `tests/library_v5/test_bootstrap.py`
- Generate: `data/migration/bootstrap/` snapshot and bootstrap manifest/report.

**Interfaces:**
- Produces: `bootstrap(repo_root: Path, install_canonical: bool=False, force_destructive: bool=False) -> dict[str, object]`
- Default writes candidate canonical tables only under `data/migration/bootstrap/library/`.
- `--install-canonical` refuses if current canonical hashes differ from the frozen initial-seed baseline unless `--force-destructive` is also supplied.

- [ ] **Step 1: Write failing tests** asserting default bootstrap leaves `data/library/` byte-identical, stages a complete candidate snapshot, and deterministic repeated bootstrap produces identical hashes.
- [ ] **Step 2: Add failing install-safety tests**: installation succeeds only when current canonical state equals the frozen seed baseline; audited changes cause a refusal with an explicit error unless destructive override is supplied.
- [ ] **Step 3: Run** `python -m unittest tests.library_v5.test_bootstrap -v` and verify RED.
- [ ] **Step 4: Implement** staged bootstrap using the existing extraction/migration pipeline against an isolated staging root; emit the replacement-file list before any explicit installation.
- [ ] **Step 5: Run** focused and full tests plus two bootstrap passes; verify byte-identical bootstrap manifests.
- [ ] **Step 6: Commit** `feat: separate library v5 bootstrap migration`.

### Task 3: Persistent content-audit history and generated queue

**Files:**
- Create: `scripts/library_v5/content_audit.py`
- Create: `tests/library_v5/test_content_audit.py`
- Create: `data/content_audit/reviews.csv`
- Generate: `data/content_audit/queue.csv`
- Generate: `data/content_audit/CONTENT_AUDIT.md`
- Modify: `scripts/library_v5/build.py`
- Modify: `scripts/library_v5/audit.py`

**Interfaces:**
- Produces: `validate_reviews(tables, evidence_rows, review_rows) -> list[dict[str,str]]`
- Produces: `build_review_queue(tables, migration_review) -> list[dict[str,str]]`
- Produces: `write_content_audit_outputs(repo_root: Path) -> dict[str, object]`

- [ ] **Step 1: Write failing tests** for nonexistent fact/evidence references, mismatched claimed current status, duplicate review IDs, invalid transitions, and deterministic queue ordering.
- [ ] **Step 2: Write failing priority tests** so current/future status-sensitive facts and high-degree convergence targets sort ahead of ordinary legacy seeds, while no fixed edge count is assumed.
- [ ] **Step 3: Run** the focused tests and verify RED.
- [ ] **Step 4: Implement** persistent review validation and generated queue/report. Ordinary clean build may rewrite `queue.csv` and `CONTENT_AUDIT.md` but never `reviews.csv`.
- [ ] **Step 5: Integrate** content-audit validation into repository audit and ordinary build.
- [ ] **Step 6: Run** full tests and two ordinary builds; verify canonical SHA equality and byte-identical generated outputs.
- [ ] **Step 7: Commit** `feat: add persistent library content audit workflow`.

### Task 4: CI safety boundary and migration freeze verification

**Files:**
- Modify: `.github/workflows/library-v5-ci.yml`
- Update: `data/migration/MIGRATION_AUDIT.md` / generated review outputs through commands only.
- Test: existing `tests/library_v5/*` plus command-level CI checks.

**Interfaces:**
- CI proves ordinary build never changes canonical files and bootstrap is deterministic without installing it.

- [ ] **Step 1: Change CI checkout/ref** to `library-v5-canonical-freeze` while this implementation is isolated.
- [ ] **Step 2: Add canonical pre/post SHA capture** around ordinary build; compare hashes and fail on mutation.
- [ ] **Step 3: Run ordinary build twice** and compare `data/derived/library_manifest.json` byte-for-byte.
- [ ] **Step 4: Run bootstrap twice in staging** and compare bootstrap manifests; never pass `--install-canonical` in CI.
- [ ] **Step 5: Restrict auto-commit paths** to generated downstream files; explicitly exclude `data/library/**` and `data/content_audit/reviews.csv`.
- [ ] **Step 6: Run the fresh workflow** and inspect every job/step result before claiming completion.
- [ ] **Step 7: Commit** `ci: enforce frozen library v5 canonical data`.

### Task 5: First source-backed high-impact content-audit batch

**Files:**
- Modify canonical fact tables under `data/library/` only through explicit audited edits.
- Modify: `data/library/sources.csv`, `data/library/evidence.csv` as required.
- Append: `data/content_audit/reviews.csv`.
- Regenerate: `data/content_audit/queue.csv`, `CONTENT_AUDIT.md`, and `data/derived/*`.
- Create: `data/content_audit/BATCH_001_HIGH_IMPACT_2026-08-27.md`.

**Interfaces:**
- Audits fact rows, not visual edges.
- Candidate work cluster: Doomsday, Brand New Day, The Fantastic Four: First Steps, VisionQuest, Wonder Man, Secret Wars, Thunderbolts*, plus immediate source/target facts selected by the generated queue.

- [ ] **Step 1: Generate the queue** and record the exact high-priority fact IDs selected for Batch 001; do not hard-code a target edge count.
- [ ] **Step 2: Research each selected fact** using source priority: Marvel/Marvel Studios, Disney/Disney+, Sony Pictures, official studio/distributor, then reputable trades only where first-party evidence is unavailable.
- [ ] **Step 3: For each fact**, either add qualifying evidence and promote to `source_verified`, mark `conflicted`, mark `superseded`, or retain `legacy_seed` with an explicit review note explaining why verification was insufficient.
- [ ] **Step 4: Add newly discovered facts** only when evidence supports them; preserve performer/character/variant distinctions and never infer identity from actor reuse.
- [ ] **Step 5: Append review history** for every decision and regenerate derived graphs from canonical facts.
- [ ] **Step 6: Run** full tests, ordinary build twice, canonical pre/post guard, and inspect Doomsday/high-degree relation deltas as observations.
- [ ] **Step 7: Write** Batch 001 report with sources, promotions/conflicts/supersessions/new facts, unresolved items, and derived-graph deltas.
- [ ] **Step 8: Stop before merging to `main`** and present the audited branch for approval.

## Self-review

- Spec coverage: ordinary build immutability, bootstrap staging/install safety, manifest relocation, persistent review history, generated queue, CI boundaries, and first content-audit batch are each assigned to a task.
- Placeholder scan: no TBD/TODO/"implement later" placeholders remain.
- Type consistency: canonical hash, bootstrap, review validation/queue, and ordinary build interfaces are named once and reused consistently.
- Scope: UI redesign and Phase 3 opacity/glow tuning remain explicitly outside this plan; only provenance fields needed by those future views are preserved.
