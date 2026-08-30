# Marvel Library DB v1 HTML DB-export Design

**Date:** 2026-08-29
**Status:** Proposed design for a separately reviewed implementation boundary
**Base:** `origin/main` at `d5c878d5763b2bd91940c31052db6e35a3e69d0a`

## Goal

Make the static flowchart consume a deterministic export of the compiled Marvel SQLite database instead of owning independent canonical Marvel fact arrays. The initial public view should show every evidence-supported derived work edge by default; selection, goals, filters, and path mode should control which existing edges and nodes receive emphasis (glow, opacity, or dimming).

The count `199` is retained only as the current HTML/prewatch compatibility observation. It is not a database limit or a correctness target.

## User-facing behavior

The default chart contains all eligible physical work-pair edges emitted by the database-facing flowchart view. The UI does not manufacture edges when a user selects a work. Selection computes a highlight state over the already exported graph:

- selected work and its configured neighborhood are emphasized;
- backward, forward, context, and PATH states apply styling to existing edge IDs;
- filters may hide or dim edges without deleting the underlying fact;
- the reason panel can explain every highlighted edge through its reason IDs;
- minimum/recommended/complete remain display-policy choices for watch planning, not separate canonical graphs.

The initial cutover preserves the existing layout, Japanese labels, controls, mobile interaction, and visual language. A later UI iteration may improve layout or default styling, but it must not silently change semantic edge derivation.

## Data flow

```text
data/library + data/content_audit
              ↓
validate and compile
              ↓
SQLite database
              ↓
v_flowchart_nodes
v_flowchart_edge_candidates
v_work_connection_reasons
              ↓
deterministic static flowchart JSON
              ↓
static GitHub Pages HTML
```

The browser does not open SQLite and no live database server is introduced. The export is a build product generated from versioned SQL views. The generated artifact must be reproducible from the same canonical inputs and must be suitable for the existing static Pages packaging.

## Export contract

The first export contract is a versioned JSON object with stable ordering:

```json
{
  "schema_version": "1",
  "generated_from": {
    "db_schema_version": "1.2-normalized-releases-status",
    "logical_fingerprint": "..."
  },
  "nodes": [],
  "edges": [],
  "reasons": [],
  "view_policy": {}
}
```

### Nodes

Each node is sourced from `v_flowchart_nodes` and keeps the stable `work_id`, Japanese and English titles, official title, format, status, classification, and release display metadata needed by the current search, filtering, watch planning, and accessibility text. Layout coordinates and lane geometry remain view data; they are not added to canonical `works` facts.

### Edges

Each edge is sourced from `v_flowchart_edge_candidates` and has one stable edge key per `(source_work_id, target_work_id)`. It includes the ordered reason IDs and the aggregated reason count. Presentation fields such as Japanese type labels, strength, line class, default opacity, glow, and bundling are derived by `views/flowchart/` policy from semantic reason metadata; they are never used to create or remove canonical facts.

### Reasons

Each exported reason retains its source fact IDs, reason kind, verification statuses, certainty values, and explanatory notes. A user-facing explanation must be traceable from an edge to a reason and then to canonical fact/evidence IDs. Release/status rows do not enter graph derivation merely because they are present in the database.

## Artifact and deployment boundary

The first cutover writes a deterministic generated artifact at `data/derived/flowchart.json` and commits that artifact alongside the existing compatibility CSVs. This keeps the current root-based GitHub Pages deployment static and requires no live build step in the browser. The build and CI checks must:

1. leave `data/library/` and persistent review ledgers untouched during ordinary builds;
2. make the deployed artifact available without SQLite or a server;
3. allow CI to compare two exports for semantic and byte determinism;
4. preserve the established ZIP root structure when a release package is produced.

## Semantic safety rules

- Only independently supported work pairs are exported as edges.
- Shared continuity alone, shared actor identity, or a traveler merely appearing in one work never creates an unsupported pair.
- A multiverse transition remains semantically housed in event/occurrence/transition facts; a derived work edge is only a supported projection.
- Same-character identity and variant identity remain distinct unless the canonical evidence supports the relation.
- Unknown continuity, transport mechanism, or exact Earth number remains unknown rather than guessed.
- A pure crossing proxy may be retired only after an independent replacement edge and review history are proven.
- Adding a canonical metadata row cannot silently fan out the graph.

## Migration stages

This design is intentionally split into independently reviewable stages.

### Stage A — Export contract and compatibility fixture

Add the exporter and JSON contract while leaving the production HTML behavior unchanged. Verify deterministic ordering, stable IDs, reason traceability, and parity of the current DB graph outputs. The 199-row prewatch artifact remains the compatibility fixture for the existing policy.

### Stage B — Data-source cutover

Change `index.html` so its node, edge, and reason data are loaded from the generated static JSON (or an assembled equivalent) rather than independently maintained `NODES`, `EDGES`, `CHAR_LINKS`, release metadata, and chronology arrays. Keep the current layout and interaction behavior while proving that all exported eligible edges are present in the graph model.

### Stage C — All-edge default and highlight policy

Make the default graph visibility include every eligible exported edge. Reuse the current selection/neighborhood/PATH state machine to assign visual emphasis to edge IDs. Add explicit tests for all-edge visibility, highlight isolation, reason-panel lookup, filters, and no edge creation during selection.

### Stage D — Production verification

Run the full bundled-Python test suite, ordinary build, deterministic export checks, desktop and Pixel-6-oriented browser smoke checks, and GitHub Pages verification. Compare selected paths and prewatch behavior with the pre-cutover baseline. Treat any intentional count change as a reviewed policy/data change, not as an incidental build result.

## Non-goals for this boundary

- No automatic promotion of the 269 `legacy_seed` release/status facts to `source_verified`.
- No implementation of credits, aliases, memberships, or possessions.
- No broad new multiverse facts without their own evidence-backed audit batch.
- No SQLite-in-browser/WASM runtime.
- No redesign of the entire chart layout in the first cutover.
- No fixed requirement that the final public count equal either 199 or 361.

## Acceptance criteria

The boundary is complete only when:

1. the same canonical inputs produce the same logical fingerprint and byte-stable flowchart export;
2. the export contains all database-supported candidate edges and their traceable reasons;
3. the default UI renders all eligible exported edges without selection;
4. selection and filters change styling/visibility only through view policy and never mutate canonical facts;
5. no independent canonical fact arrays remain in `index.html`;
6. existing selected-path, prewatch, and mobile behavior is covered by regression tests;
7. ordinary builds leave canonical data and persistent review history unchanged;
8. GitHub Pages serves the generated static artifact successfully.
