# Marvel Library DB v1 HTML DB-export review

## Review boundary

This review covers the HTML DB-export cutover through Task 7 on branch
`codex/html-db-export`. Production `main` and the public site were not merged or
published. The implementation range is `1e9023b..HEAD` and includes the JSON
bootstrap, all-edge materialization, selection styling contract, and the mobile
edge-key normalization fix.

## Verification evidence

- Bundled-Python full suite: `Ran 231 tests ... OK` after the Task 7
  index-independent regression was added.
- Ordinary build: `audit_ok: true`, `audit_issue_count: 0`, foreign-key and
  SQLite integrity checks remain clean; compatibility observations are
  `prewatch_edges=199`, `story_paths_reproduced=83`, `work_edges_all=361`, and
  `work_pair_reasons=569`.
- Flowchart export: schema `1`, `131` nodes, `361` directed edges, `569`
  traceable reasons, and `42` character groups; policy defaults are
  `default_edge_visibility=all` and `default_importance_mode=reference`.
- Export/build determinism: repeated ordinary builds produced byte-identical
  DB manifest, graph CSVs, and `data/derived/flowchart.json`.
- Index-independent build: the working-copy `index.html` was moved aside,
  rebuilt, and restored; DB manifest, graph CSVs, and flowchart JSON SHA-256
  hashes were unchanged (`index_independent_build=ok`).
- JSON schema checks confirmed the required top-level keys, stable counts,
  reason-ID resolution, and the all/reference policy.
- CI now repeats the static-artifact contract check (schema/default policy,
  endpoint membership, and reason endpoint agreement) after the index-independent
  build step.
- GitHub Pages root packaging inputs are present exactly as
  `index.html`, `README.md`, `AUDIT.md`, `AUDIT.json`, `preview.png`, and
  `.nojekyll`; no version-named duplicate HTML was added.
- `git diff --check` is clean for the committed changes. Canonical
  `data/library/` inputs and `data/content_audit/reviews.csv` were not edited by
  the ordinary build or export.

## Semantic decisions

The browser consumes only the generated static JSON artifact. The default
overview keeps every exported eligible pair visible by materializing missing
SVG groups once, while selection, goals, PATH, and character filters only apply
classes/opacity and reason-panel content. Stable exported `edge_id` values are
retained on SVG groups; mobile Canvas primitives normalize them back to the
existing directed pair keys so highlighting remains directional. The existing
importance tier controls still allow users to narrow the display after the
all-edge default.

The compatibility values 199/361/569 are reported as observations, not fixed
targets. No new semantic work pair is derived by the HTML layer, and no
SQLite/WASM runtime is introduced.

## Browser and deployment boundary

The required desktop and 412x915 browser smoke could not be completed in this
managed Windows run: a temporary localhost static server failed to bind with
`WinError 10013`. Consequently this review makes no browser-render or timing
claim. The source/runtime contracts and mobile Canvas key-normalization test
cover the no-edge-rebuild path; a connected environment should repeat the
desktop/mobile smoke before publication. GitHub Pages/public behavior and
remote CI remain pending until the user authorizes final integration.

## Deferred work

- Repeat static-server desktop/mobile smoke and capture first-ready, selection,
  and deselection timings on a 412x915 Pixel-6-oriented run.
- Complete the broader DB-v1 roadmap phases (credits, aliases, memberships,
  possessions, and additional audited multiverse batches) under their own
  approved boundaries.
