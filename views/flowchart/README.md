# Flowchart view configuration

This directory contains presentation policy only. Canonical Marvel facts live under `data/library/`.

`node_view.json` and `details.json` are tracked presentation inputs keyed by
stable `work_id`. They preserve branch filters, priority, chronology lane/order
metadata, and Japanese synopsis/map-role descriptions from the pre-cutover
HTML. They do not define titles, release dates, production status, edges, or
any other canonical fact. The DB export remains authoritative for those
fields.

`scripts.library_v5.extract_view_metadata` is a one-shot migration utility that
may read the checked-in `index.html` to regenerate these files. Ordinary builds
load only these JSON inputs, and therefore continue to export when
`index.html` is absent. Do not add canonical facts or promote `legacy_seed`
rows through this directory.

The ordinary build writes the browser-facing artifact to
`data/derived/flowchart.json`. Its `view_policy` defaults to
`default_edge_visibility: "all"` and `default_importance_mode: "reference"`;
the HTML materializes those exported edges once and lets selection/PATH/filter
state change only their visual classes or opacity. The artifact is static JSON;
the browser never opens the SQLite database.

- User-facing lane and region labels are Japanese.
- Edge visibility, opacity, glow, dimming, bundling, crossings, and geometry are view concerns.
- Hiding or dimming an edge never deletes the underlying canonical fact.
