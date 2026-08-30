# Marvel Library DB v1 HTML DB-export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the static flowchart consume a deterministic export of the compiled SQLite database, render every database-supported work edge by default, and reserve selection/PATH/filter state for visual emphasis rather than edge creation.

**Architecture:** The build will query versioned SQLite views and write one byte-stable `data/derived/flowchart.json` artifact containing DB-backed nodes, edges, traceable reasons, character memberships, and presentation policy. The existing static SVG/layout and interaction state machine will be retained initially; its data arrays will be replaced by an asynchronous JSON bootstrap, and its existing master/dynamic overlay layers will style already-exported edges without rebuilding the graph on selection.

**Tech Stack:** Python 3 bundled Codex runtime, `sqlite3`, deterministic JSON/CSV writers, existing `unittest` suite, static HTML/CSS/SVG/JavaScript, GitHub Pages root deployment.

**Spec:** `docs/superpowers/specs/2026-08-29-marvel-library-db-v1-html-db-export-design.md`

## Global Constraints

- The browser never opens SQLite and no SQLite/WASM runtime or live server is introduced.
- `data/derived/flowchart.json` is a generated build product; canonical facts remain under `data/library/` and persistent review history remains under `data/content_audit/`.
- The default graph contains every eligible pair from `v_flowchart_edge_candidates`; `199` remains a compatibility observation, not a limit or acceptance target.
- A selection, goal, filter, or PATH operation may style, dim, or hide an exported edge but may not create a new semantic pair or mutate canonical data.
- Multiverse transitions remain housed in event/occurrence/transition facts; shared continuity, actor identity, or a traveler appearance alone must not manufacture an edge.
- Preserve stable IDs, Japanese labels, current layout, current controls, and mobile behavior during the first cutover.
- Do not promote `legacy_seed` facts or implement credits, aliases, memberships, possessions, or unrelated multiverse batches in this boundary.
- Every behavioral change follows RED test -> minimal implementation -> GREEN test -> full verification and a small auditable commit.
- Use the bundled PowerShell runtime for verification:
  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

---

### Task 1: Extend the flowchart SQL view contract

**Files:**
- Modify: `scripts/library_v5/db_views.py:620-655`
- Modify: `scripts/library_v5/db_fingerprint.py` view ordering metadata
- Test: `tests/library_v5/test_db_views.py`
- Test: `tests/library_v5/test_db_export_parity.py`

**Interfaces:**
- Consumes: the existing `works`, `_v_resolved_appearances`, and `v_work_connection_reasons` tables/views.
- Produces: `v_flowchart_nodes` rows with all DB-backed node display fields (`work_id`, title/release/status fields, `ja_status`, Japan release fields, aliases, and audit metadata) and `v_flowchart_edge_candidates` rows with stable pair summaries. The view remains presentation-facing and does not derive new facts.

- [ ] **Step 1: Write failing contract tests.** Add assertions that `v_flowchart_nodes` exposes the named columns in a deterministic `work_id` order, that every edge candidate has one row per `(source_work_id,target_work_id)`, and that graph-view SQL does not reference `v_work_releases` or `v_work_production_status`.

- [ ] **Step 2: Run the focused tests and verify they fail** because the current node view omits the additional columns.

  Run:
  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_db_views tests.library_v5.test_db_export_parity -v
  ```

- [ ] **Step 3: Implement the minimal view change.** Select the complete `works` display/audit column set in the established order, retain the existing pair projection for `v_flowchart_edge_candidates`, and add matching order keys to `_VIEW_ORDER_KEYS` so fingerprints remain deterministic.

- [ ] **Step 4: Run the focused tests and verify they pass.** Confirm no release/status view enters graph SQL and that legacy semantic/pair parity is unchanged.

- [ ] **Step 5: Commit.**

  ```powershell
  git add scripts/library_v5/db_views.py scripts/library_v5/db_fingerprint.py tests/library_v5/test_db_views.py tests/library_v5/test_db_export_parity.py
  git commit -m "feat: expose complete flowchart node view"
  ```

### Task 2: Add the deterministic JSON exporter and presentation policy

**Files:**
- Create: `scripts/library_v5/flowchart_export.py`
- Modify: `scripts/library_v5/db_export.py` (share the reason-row query through a public helper without changing CSV output)
- Modify: `scripts/library_v5/derive_compat.py` (extend generated policy with schema/default-edge/presentation rules)
- Create: `tests/library_v5/test_flowchart_export.py`
- Modify: `tests/library_v5/test_db_export_parity.py`

**Interfaces:**
- Consumes: `compile_database` output, `v_flowchart_nodes`, `v_flowchart_edge_candidates`, `v_work_connection_reasons`, `v_entity_work_history`, `entities`, `views/flowchart/policy.json`, and the DB manifest equivalence hash.
- Produces:
  - `export_flowchart(repo_root: Path, db_path: Path, output_path: Path, *, db_manifest: dict[str, object]) -> dict[str, int]`.
  - JSON object `{schema_version, generated_from, nodes, edges, reasons, characters, view_policy}`.
  - Node IDs sorted by `work_id`; edge IDs are `slug_id("edge", source, target)`; reason IDs are the existing stable reason IDs; `reason_ids` are sorted and refer only to entries in `reasons`.
  - Edge presentation fields (`type`, `type_en`, `strength`, `render_class`, `importance`, `importance_ja`, `importance_note`) computed solely by deterministic policy from reason kinds, verification statuses, certainty values, and reason notes.

- [ ] **Step 1: Write failing exporter tests.** Use a compiled temporary DB and assert:
  - exact top-level keys and schema version `"1"`;
  - node/edge/reason stable ordering and unique IDs;
  - every edge reason ID resolves to a reason with matching endpoints;
  - the export pair set equals `v_flowchart_edge_candidates` and the CSV exporter pair set;
  - `generated_from.db_schema_version` and `generated_from.logical_fingerprint` come from the manifest;
  - two exports from the same DB are byte-identical;
  - characters are grouped from canonical entity/appearance views and no release/status rows appear in reasons.

- [ ] **Step 2: Run the focused test and verify it fails** because no JSON exporter exists.

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_flowchart_export -v
  ```

- [ ] **Step 3: Implement the exporter.** Reuse the existing reason query and stable ID helper, query view rows with explicit `ORDER BY`, serialize with `ensure_ascii=False`, `sort_keys=True`, and compact separators, and write one trailing newline. Keep full evidence IDs/notes in `reasons` but do not embed source documents or layout geometry.

- [ ] **Step 4: Add the view policy.** Set `default_edge_visibility` to `"all"`, `default_importance_mode` to `"reference"`, and define Japanese/English labels and strength/importance thresholds for `explicit_relation`, `shared_entity`, and `multiverse_transition` (with a conservative fallback). Document that policy fields can dim/hide only exported edges.

- [ ] **Step 5: Run the focused tests and verify they pass**, including existing CSV parity tests.

- [ ] **Step 6: Commit.**

  ```powershell
  git add scripts/library_v5/flowchart_export.py scripts/library_v5/db_export.py scripts/library_v5/derive_compat.py tests/library_v5/test_flowchart_export.py tests/library_v5/test_db_export_parity.py
  git commit -m "feat: export deterministic flowchart JSON"
  ```

### Task 3: Integrate the export into ordinary builds and CI

**Files:**
- Modify: `scripts/library_v5/build.py:16-70`
- Modify: `tests/library_v5/test_db_build_integration.py`
- Modify: `.github/workflows/library-v5-ci.yml`
- Modify: `.gitignore` only if a generated temporary path is required

**Interfaces:**
- Consumes: `export_flowchart` and the manifest written by `write_db_manifest`.
- Produces: `data/derived/flowchart.json` on every ordinary build, a `flowchart_export` result summary, and CI assertions for semantic/byte determinism and canonical isolation.

- [ ] **Step 1: Write failing build tests.** Extend the temporary-repository integration test to assert that `flowchart.json` is emitted, is byte-identical across two builds, has the same logical fingerprint as the DB manifest, and remains unchanged when compatibility release/status rows are appended. Assert that `data/library/` and `reviews.csv` hashes remain unchanged.

- [ ] **Step 2: Run the focused build tests and verify they fail** because the build does not call an HTML exporter.

- [ ] **Step 3: Implement build wiring.** Call `export_flowchart` immediately after writing the DB manifest, pass the parsed manifest, include its counts in the result, and keep `clean_generated` limited to generated products so tracked view inputs survive. Do not stage or persist `marvel.sqlite` as a canonical input.

- [ ] **Step 4: Add CI checks.** Run the exporter twice from the same canonical checkout, compare JSON bytes and a normalized semantic projection, assert the artifact exists without `index.html`, and retain existing foreign-key, integrity, bootstrap, and audit checks.

- [ ] **Step 5: Run focused tests and the full bundled suite.**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_db_build_integration tests.library_v5.test_flowchart_export -v
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  ```

- [ ] **Step 6: Commit.**

  ```powershell
  git add scripts/library_v5/build.py tests/library_v5/test_db_build_integration.py .github/workflows/library-v5-ci.yml
  git commit -m "build: emit flowchart JSON artifact"
  ```

### Task 4: Move non-canonical view metadata out of `index.html`

**Files:**
- Create: `views/flowchart/node_view.json` (branch/priority and chronology metadata keyed by stable work ID)
- Create: `views/flowchart/details.json` (descriptive synopsis/map-role text only)
- Create: `scripts/library_v5/extract_view_metadata.py` (one-shot strict extractor from the current HTML)
- Create: `tests/library_v5/test_flowchart_view_metadata.py`
- Modify: `scripts/library_v5/flowchart_export.py`
- Modify: `scripts/library_v5/build.py`

**Interfaces:**
- Consumes: the existing checked-in `index.html` only for the one-time migration command; thereafter consumes tracked view metadata and DB node IDs.
- Produces: `view_policy.node_metadata`, `view_policy.details`, and chronology lane definitions in the JSON artifact. These files contain layout/descriptive policy, never canonical edge/fact assertions.

- [ ] **Step 1: Write failing metadata tests.** Require strict JSON shapes, no unknown work IDs, no duplicate lane/order entries, and exact ID coverage against the DB node set. Assert that the extractor rejects malformed or missing markers rather than guessing.

- [ ] **Step 2: Run the focused metadata test and verify it fails** because the view metadata files and extractor do not exist.

- [ ] **Step 3: Implement the one-shot extractor and checked-in inputs.** Preserve current Japanese labels, branch filters, chronology lanes/orders, and descriptive details; reject duplicate IDs and write sorted UTF-8 JSON. Mark the inputs as presentation-only in `views/flowchart/README.md`.

- [ ] **Step 4: Merge view metadata during export.** Validate that every metadata work ID exists in `v_flowchart_nodes`; use DB titles/release/status as authoritative values and never let view metadata override them.

- [ ] **Step 5: Run focused tests and verify they pass.** Confirm the exporter still succeeds when `index.html` is temporarily absent after the one-time extraction.

- [ ] **Step 6: Commit.**

  ```powershell
  git add views/flowchart/node_view.json views/flowchart/details.json views/flowchart/README.md scripts/library_v5/extract_view_metadata.py scripts/library_v5/flowchart_export.py scripts/library_v5/build.py tests/library_v5/test_flowchart_view_metadata.py
  git commit -m "refactor: separate flowchart presentation metadata"
  ```

### Task 5: Replace HTML-owned fact arrays with the JSON bootstrap

**Files:**
- Modify: `index.html` around the current `NODES`, `EDGES`, `CHAR_LINKS`, `RELEASE_META`, `CHRONOLOGY_LANES`, and `CHRONOLOGY_META` declarations and initialization blocks
- Create: `tests/library_v5/test_index_db_export_contract.py`
- Modify: `README.md` with the static artifact/loading boundary

**Interfaces:**
- Consumes: `data/derived/flowchart.json` loaded by a relative static URL.
- Produces: an asynchronous `loadFlowchartData()`/`initializeFlowchartData(payload)` bootstrap that populates runtime state (`NODES`, `EDGES`, `reasonsById`, `charWorks`, release/chronology metadata) only after schema and endpoint validation, then runs the existing UI initialization.

- [ ] **Step 1: Write failing HTML contract tests.** Read `index.html` as text and assert that it references `data/derived/flowchart.json`, has an explicit loading/error path, and no longer contains literal `const NODES=`, `const EDGES=`, `const CHAR_LINKS=`, `const RELEASE_META=`, `const CHRONOLOGY_LANES=`, or `const CHRONOLOGY_META=` data arrays. Assert that the loader validates `schema_version` and that runtime code does not fetch SQLite.

- [ ] **Step 2: Run the focused contract test and verify it fails** against the current embedded arrays.

- [ ] **Step 3: Implement the loader and initialization guard.** Replace embedded data with empty runtime declarations, move data-dependent option population/adjacency construction/initial render behind `initializeFlowchartData`, use `fetch(new URL('data/derived/flowchart.json', document.baseURI))`, show a Japanese loading/error message, and preserve the current relative URL behavior on GitHub Pages.

- [ ] **Step 4: Wire reasons and characters.** Build `reasonsById` and character work sets from the exported payload; keep release/status display sourced from node fields and chronology/details sourced from `view_policy`.

- [ ] **Step 5: Run the focused contract tests and a local static-server smoke check.** Start a read-only local HTTP server, load the page, and verify that the loader reaches the ready state and the existing controls can select a work.

- [ ] **Step 6: Commit.**

  ```powershell
  git add index.html README.md tests/library_v5/test_index_db_export_contract.py
  git commit -m "feat: load flowchart data from static DB export"
  ```

### Task 6: Render all exported edges by default and keep selection styling-only

**Files:**
- Modify: `index.html` in the existing SVG overlay/materialization and selection/PATH functions
- Create: `tests/library_v5/test_flowchart_selection_contract.py`
- Modify: `README.md` performance notes

**Interfaces:**
- Consumes: runtime `EDGES`, `reasonsById`, `view_policy.default_edge_visibility`, and existing node geometry.
- Produces: one-time materialization of every eligible edge as a neutral `master-edge-overlay`, default `importanceMode='reference'`, and selection state that only toggles classes/opacity and reads reason IDs for explanation. `render()` and `refreshSelection()` must not append a new semantic edge.

- [ ] **Step 1: Write failing selection tests.** Add source-level/runtime assertions that no-selection materializes every eligible edge present in the JSON, the default policy does not mark any eligible edge `importance-hidden`, selecting/deselecting changes only classes/opacity, and the reason panel resolves all highlighted edge reason IDs. Include a multi-select/PATH case and a filter case that hides visually without changing `EDGES.length`.

- [ ] **Step 2: Run the focused test and verify it fails** because the current default policy and runtime still use the embedded compatibility array and hide lower-importance edges by default.

- [ ] **Step 3: Implement the minimal runtime change.** Feed `materializeMissingMasterEdges()` from JSON edges, use stable `edge_id`/`data-edge-key` values, set the all-edge default, preserve existing directed traversal rules, and update highlight classes in place. Add a compact reason explanation block keyed by `reason_ids` without embedding evidence documents.

- [ ] **Step 4: Run focused tests and browser smoke checks.** Verify overview/release/chronology tabs, selection, clear, multi-goal, PATH, character filter, and reason lookup with no full SVG/layout rebuild on selection.

- [ ] **Step 5: Measure the mobile gate.** On a 412x915 headless Chromium/Pixel-6-oriented run, record first ready paint, selection, and deselection times; keep the existing `refreshSelection=0 / rebuildMobileCanvas=0` criterion and report any intentional threshold change before altering it.

- [ ] **Step 6: Commit.**

  ```powershell
  git add index.html README.md tests/library_v5/test_flowchart_selection_contract.py
  git commit -m "feat: show all exported edges and style selections"
  ```

### Task 7: Full verification, packaging, and production review

**Files:**
- Modify: `tests/library_v5/test_db_build_integration.py` for index-independent export/build checks
- Modify: `.github/workflows/library-v5-ci.yml` for final artifact checks
- Modify: `README.md` and `views/flowchart/README.md` with the generated artifact and performance contract
- Create: `docs/superpowers/reviews/2026-08-29-marvel-library-db-v1-html-db-export-review.md`

**Interfaces:**
- Consumes: all prior tasks, `data/derived/flowchart.json`, the generated DB manifest, and the existing Pages root package.
- Produces: an auditable review recording semantic parity, intentional count changes, canonical isolation, browser checks, and deployment verification. No merge/publication is implied by this task.

- [ ] **Step 1: Run the exact bundled-Python full suite and ordinary build** from the worktree root; capture fresh output and inspect generated paths.

- [ ] **Step 2: Run index-independent verification.** Temporarily move only the working copy of `index.html` out of the build input set, rebuild/export, restore it, and prove the JSON/DB graph outputs are unchanged. Remove only known generated transient paths after inspection.

- [ ] **Step 3: Run `git diff --check`, inspect every generated JSON/CSV diff, validate JSON parse/schema, and confirm canonical/review hashes are unchanged.** Treat counts such as 199, 361, and 569 as observations and explain any reviewed change.

- [ ] **Step 4: Run desktop and mobile static-server smoke checks and verify GitHub Pages serves `data/derived/flowchart.json` and the ready HTML.** Confirm the established ZIP root remains exactly `index.html`, `README.md`, `AUDIT.md`, `AUDIT.json`, `preview.png`, `.nojekyll` when packaging is tested.

- [ ] **Step 5: Write the review with test/build commands, outputs, semantic decisions, deferred work, and production impact.** Stop at the branch review gate; do not merge or publish without explicit user authorization.

- [ ] **Step 6: Commit the review/docs and leave the worktree clean.**

  ```powershell
  git add tests/library_v5/test_db_build_integration.py .github/workflows/library-v5-ci.yml README.md views/flowchart/README.md docs/superpowers/reviews/2026-08-29-marvel-library-db-v1-html-db-export-review.md
  git commit -m "docs: audit html db-export cutover"
  git status --short
  ```
