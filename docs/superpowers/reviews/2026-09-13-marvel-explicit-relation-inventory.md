# Marvel explicit relation inventory review

## Scope

This audit covers only the canonical `data/library/work_relations.csv` facts on
main `c0f2b35d5190c27e572ee856d7e4cd0037cd7ec9`. It does not promote, rewrite,
or infer any relation, release/status fact, chronology, identity, or multiverse
transition. Evidence and review joins use the exact key
`(fact_table, fact_id)`.

## Result

The inventory contains 164 relation rows: 161 active rows, 54
`source_verified`, 107 `legacy_seed`, and 3 `superseded`. Every relation ID is
represented exactly once. All 54 source-verified rows have exact relation-table
evidence, exact relation-table review history, and registered source IDs.

The independent graph projection remains 131 works, 355 edge pairs, and 562
reason rows. Projection mismatches and reason orphans are both zero.

Every active relation has exactly one explicit-relation reason with matching
direction, support fact ID, verification status, certainty, notes tuple, and
stable reason ID, and that reason ID occurs exactly once on the corresponding
exported edge. The reverse direction is also checked: every explicit reason
resolves to one active relation, so active relations and explicit reasons form
a 161-to-161 bijection. Superseded rows have no orphan explicit reason.

Evidence is split into exact same-fact evidence (the relation's own
`work_relations.csv:<relation_id>` rows) and external evidence referenced by a
review. Only same-fact primary/supporting evidence can satisfy a
`source_verified` disposition. Reviews may intentionally cite evidence from
another fact table when recording a cross-domain recheck (for example,
transition or continuity support); the inventory records those external
evidence IDs and only fails when a referenced evidence ID does not exist
globally.

The 107 active `legacy_seed` rows are reported as `needs-source`; they are not
treated as verified merely because they already project into the viewer. The
three superseded rows remain visible in the audit with a separate `superseded`
disposition. No explicit conflict marker is present in the current relation
rows.

## Artifacts

- `scripts/library_v5/explicit_relation_inventory.py` — deterministic,
  read-only auditor and JSON/Markdown CLI.
- `tests/library_v5/test_explicit_relation_inventory.py` — coverage,
  provenance-isolation, graph-topology, and report-rendering contract.
- `data/content_audit/reports/explicit_relation_inventory.json` — complete
  machine-readable snapshot.
- `data/content_audit/reports/explicit_relation_inventory.md` — complete
  human-readable table and `needs-source` list.

## Review boundary

This is an audit-only baseline. The next semantic PR should select a small
3–6-relation wave from the `needs-source` list, register relation-specific
official sources, add one exact evidence row and one auditable review transition
per relation, then rerun the full graph and browser verification. Generic
catalogue membership is not sufficient relation evidence.

## Verification

Focused inventory tests passed (7 tests). Report generation passed after a
single formatting-path regression was covered and fixed. Canonical and derived
CSV inputs were not edited by the auditor.
