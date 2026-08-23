# GitHub Pages Direct Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace bot-commit-dependent Pages publishing with a single-run GitHub Actions build, verification, packaging, and direct Pages deployment.

**Architecture:** `build-public.yml` becomes the sole CI/publish workflow. Pull requests build and test only; `main` pushes additionally stage the six public files, upload both Pages and downloadable artifacts, then deploy through the `github-pages` environment. No workflow-generated Git commit is used.

**Tech Stack:** GitHub Actions, Python 3.13, Graphviz, GitHub Pages Actions.

**Spec:** `docs/superpowers/specs/2026-08-24-pages-direct-deploy.md`

## Global Constraints

- Public distribution consists of exactly `index.html`, `README.md`, `AUDIT.md`, `AUDIT.json`, `preview.png`, `.nojekyll`.
- Existing v5.15.0 source/release tests must remain green.
- Pull requests must never deploy Pages.
- Workflow publication must not use `git push` or `contents: write`.

---

### Task 1: Add the Pages workflow contract test

**Files:**
- Create: `tests/test_pages_workflow.py`
- Test: `tests/test_pages_workflow.py`

**Interfaces:**
- Consumes: `.github/workflows/build-public.yml` as UTF-8 text.
- Produces: a zero-exit contract check for direct Pages deployment and exact public-file staging.

- [ ] **Step 1: Write the contract assertions** for PR/workflow-dispatch triggers, Pages permissions/actions, main-only deployment, six-file staging, hidden `.nojekyll`, and absence of bot push.
- [ ] **Step 2: Run `python tests/test_pages_workflow.py` against the old workflow** and confirm it fails because direct Pages deployment is absent.
- [ ] **Step 3: Keep the failing test in the feature branch while implementing Task 2.**

### Task 2: Replace bot-commit publishing with direct Pages deployment

**Files:**
- Modify: `.github/workflows/build-public.yml`
- Test: `tests/test_pages_workflow.py`

**Interfaces:**
- Consumes: existing `scripts/build_public.py` and the v5.15 release tests.
- Produces: `_site/` containing exactly the six public files, a `github-pages` artifact, a downloadable `marvel-flowchart-jp-public` artifact, and a Pages deployment on `main`.

- [ ] **Step 1: Add `pull_request` and `workflow_dispatch` triggers** while keeping `main` push publication.
- [ ] **Step 2: Use `contents: read`, `pages: write`, and `id-token: write`; remove all workflow Git commit/push logic.**
- [ ] **Step 3: Build `index.html` and run all existing v5.15 tests plus `test_pages_workflow.py`.**
- [ ] **Step 4: Stage only the six public files into `_site/`.**
- [ ] **Step 5: On `main` only, configure Pages, upload the Pages artifact and downloadable artifact, then deploy with `actions/deploy-pages@v4`.**
- [ ] **Step 6: Open a PR and confirm the build job is green and the deploy job is skipped.**
- [ ] **Step 7: Merge with expected-head SHA protection, then confirm the `main` run builds successfully and reaches the deploy job.**

### Task 3: Verify the new operational path

**Files:**
- No additional code files required.

**Interfaces:**
- Consumes: the merged workflow run.
- Produces: evidence that future assistant changes need one repository push only.

- [ ] **Step 1: Confirm the `main` run's build and release-contract steps succeeded.**
- [ ] **Step 2: Confirm `marvel-flowchart-jp-public` contains the exact six public files.**
- [ ] **Step 3: Confirm Pages deployment succeeds; if repository Pages Source is still branch-based, record the one-time UI switch to `GitHub Actions` as the only manual prerequisite.**
