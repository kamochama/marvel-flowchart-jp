# Chronology Selection Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make chronology highlighting obey the same scope and combination semantics as graph selection while preserving explicit, auditable chronology metadata in desktop and mobile renderers.

**Architecture:** Keep chronology edges as a separate view layer. A pure shared helper will classify explicit chronology edge records from the current selection state; SVG and Canvas adapters will only map those classifications onto their own primitives. Structural branch lines will carry source/target metadata, while display-only sequences will be marked non-traversable.

**Tech Stack:** `index.html` inline JavaScript/SVG/Canvas, Python `unittest` contract tests, bundled Codex Python runtime.

**Spec:** Local read-only audit of `e42a3c0` and the Phase 2 chronology-selection requirements in `AGENTS.md`.

**Audit boundary:** Do not use ChatGPT Work for this batch; all review and verification stay in this checkout.

## Global Constraints

- Do not add chronology edges to `EDGES` or change the 199 prewatch graph-edge compatibility count.
- Preserve release-order charts as `data-relationship-edges="off"` and do not fabricate work arrows.
- Use TDD: each behavior gets a failing regression assertion before production changes.
- Keep `main` untouched; all changes stay on `codex/chronology-selection-audit-fixes` until explicitly approved.
- Run the bundled full unittest suite and deterministic build before claiming completion.

### Task 1: Add RED contract tests

**Files:**
- Modify: `tests/library_v5/test_flowchart_selection_contract.py`

- [x] Add assertions for state-aware shared chronology classification, `previous1` direct-incoming behavior, AND/PATH handling, branch metadata, and explicit traversability metadata.
- [x] Run the focused test file and confirm the new assertions fail against `e42a3c0`.

### Task 2: Implement shared chronology selection and metadata

**Files:**
- Modify: `index.html`

- [x] Add a pure chronology edge classifier that accepts edge records and selection state, respecting scope, combine mode, path mode, and `data-chronology-traversable`.
- [x] Add selection state fields needed by both renderers and route desktop/mobile through the shared classifier.
- [x] Add traversability metadata to chronology groups, wrap FOX branch connectors with source/target metadata, and mark the independent SSU sequence display-only.

### Task 3: Verify locally and re-audit

**Files:**
- Modify: `README.md` only if the user-visible version note is required.

- [x] Run focused tests, browser smoke checks, full tests, and build; inspect and clean only known generated outputs.
- [x] Perform a local read-only audit of the exact branch diff and resolve the stale public-version contract assertion.
- [x] Apply the concrete finding with another focused GREEN run; no external Work audit is part of this batch.
