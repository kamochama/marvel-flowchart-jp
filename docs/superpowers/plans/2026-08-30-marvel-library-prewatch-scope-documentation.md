# Marvel Library prewatch scope documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the public README and audit record with the implemented two-scope chart viewer and the official/site-proposal prewatch terminology.

**Architecture:** Keep the existing static HTML and DB-derived artifact unchanged. Update only user-facing documentation and add a review record that distinguishes the current public choices from legacy internal compatibility values.

**Tech Stack:** Markdown documentation, existing static HTML contract tests, bundled Codex Python runtime, and the repository build command.

**Spec:** `docs/superpowers/plans/2026-08-30-marvel-library-html-design-operation-debug.md` plus the approved UI contract in `tests/library_v5/test_watch_scroll_navigation.py`.

## Global Constraints

- The public chart scope choices are exactly `関連全体` and `1つ前のみ`.
- The public prewatch choices are exactly `おすすめ` and `完全版`; legacy `minimum` remains only as an internal compatibility value.
- `公式予習ルート` must remain distinct from the site's `サイト提案ルート` fallback.
- Documentation changes must not modify canonical CSVs, persistent review history, or graph semantics.
- Final verification uses the bundled Python runtime and removes only known generated outputs.

---

### Task 1: Synchronize README terminology

**Files:**
- Modify: `README.md:1-8,66-74`
- Test: `tests/library_v5/test_watch_scroll_navigation.py`

**Interfaces:**
- Consumes: current `index.html` labels and the static UI contract tests.
- Produces: a current changelog and usage text that no longer advertises removed public choices.

- [ ] **Step 1: Update the current changelog**

  Replace the v5.20.7 top section with a v5.20.8 section describing `関連全体／1つ前のみ`, `おすすめ／完全版`, and `サイト提案ルート` fallback wording.

- [ ] **Step 2: Update the usage bullets**

  State that official routes are shown with source metadata and that unregistered works are explicitly labeled as site proposals, without changing historical changelog entries below.

- [ ] **Step 3: Run the focused contract**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_watch_scroll_navigation -v
  ```

  Expected: every test passes.

### Task 2: Record the scope redesign review

**Files:**
- Create: `docs/superpowers/reviews/2026-08-30-marvel-library-prewatch-scope-documentation.md`

**Interfaces:**
- Consumes: commit `9dc56c0`, the current HTML contract, and the full verification output.
- Produces: an auditable note that the old three-tier review is historical and the current public contract has two scope choices and two prewatch choices.

- [ ] **Step 1: Write the review record**

  Include the branch/commit, changed labels, incoming-edge-only behavior for `1つ前のみ`, legacy normalization behavior, and the fact that no canonical data or graph edge semantics changed.

- [ ] **Step 2: Include verification evidence**

  Record the focused contract, full suite (322 tests), build audit count, compatibility counts, and clean-worktree check from the implementation checkpoint.

### Task 3: Final documentation verification

**Files:**
- Read: `README.md`
- Read: `docs/superpowers/reviews/2026-08-30-marvel-library-prewatch-scope-documentation.md`

**Interfaces:**
- Consumes: the documentation edits from Tasks 1–2.
- Produces: a clean, committed documentation-only follow-up on the feature branch.

- [ ] **Step 1: Check the public wording**

  ```powershell
  Get-Content README.md -TotalCount 75 | Select-String -Pattern "最低限|2段階|監査済み編集ルート|編集ルート"
  ```

  Expected: no matches in the current top changelog or usage section; historical entries may remain below the current release note.

- [ ] **Step 2: Run the full suite and build**

  ```powershell
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  git diff --check
  ```

  Expected: all tests pass, audit issue count is zero, and the build exits successfully.

- [ ] **Step 3: Remove generated outputs and verify the diff**

  Remove only `data/content_audit/CONTENT_AUDIT.md`, `data/content_audit/queue.csv`, `data/derived/LIBRARY_AUDIT.md`, `data/derived/audit.json`, `data/derived/db/`, `data/derived/library_manifest.json`, and generated `__pycache__/` directories. Confirm that README, this plan, and the new review are the only intended files for the documentation commit.

- [ ] **Step 4: Commit**

  ```powershell
  git add README.md docs/superpowers/plans/2026-08-30-marvel-library-prewatch-scope-documentation.md docs/superpowers/reviews/2026-08-30-marvel-library-prewatch-scope-documentation.md
  git diff --cached --check
  git commit -m "docs: record prewatch scope terminology"
  ```
