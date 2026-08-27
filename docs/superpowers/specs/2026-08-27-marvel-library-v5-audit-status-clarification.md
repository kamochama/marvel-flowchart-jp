# Marvel Library v5 Audit-Status Clarification

## Status

- Date: 2026-08-27
- Applies to: `docs/superpowers/specs/2026-08-27-marvel-library-v5-design.md`
- Scope: implementation clarification discovered during the Task 8 migration review
- Production `main` remains unchanged.

## Clarification 1: canonical audit vocabulary

Section 5 of the base design is normative for audit vocabulary.

`certainty` is exactly:

- `confirmed`
- `probable`
- `uncertain`
- `unknown`

`verification_status` is exactly:

- `legacy_seed`
- `source_verified`
- `conflicted`
- `superseded`

Earlier implementation-only spellings such as `strong`, `verified`, `candidate`, or `rejected` are not canonical v5 values.

## Clarification 2: which fact tables carry `verification_status`

Every source-auditable canonical fact table carries `verification_status`, including:

- `entity_relations.csv`
- `appearances.csv`
- `portrayals.csv`
- `continuities.csv`
- `work_continuities.csv`
- `chronology_assertions.csv`
- `work_relations.csv`

The field lists in sections 4.3, 4.7, 4.8, 4.9, and 4.10 of the base design should therefore be read as also including `verification_status`.

`entities.csv`, `people.csv`, and `works.csv` remain identity/catalog tables rather than relation/assertion audit rows under this initial v5 schema.

## Clarification 3: promotion to `source_verified`

A migrated row starts as `legacy_seed` even when the old file mentioned a URL or confidence level. It may become `source_verified` only when the v5 canonical fact has at least one non-legacy `evidence.csv` row that satisfies the source policy.

A legacy confidence label may seed `certainty`, but confidence and verification are separate dimensions. In the current migration mapping:

- legacy `high` -> `confirmed`
- legacy `medium` -> `probable`
- legacy `low` -> `uncertain`
- missing/other -> `unknown`

None of those mappings upgrades `verification_status` by itself.

## Clarification 4: derived reasons preserve provenance

`data/derived/work_pair_reasons.csv` must preserve enough provenance to explain why a work pair exists without reopening generated HTML. For each reason it records, as applicable:

- supporting canonical fact IDs;
- appearance kinds;
- supporting verification statuses;
- supporting certainty values;
- entity or explicit work-relation identifiers.

A view may use those fields for opacity, glow, filtering, or explanation. It must not rewrite canonical facts to achieve a display effect.

## Clarification 5: superseded facts

`superseded` is a retained audit/history state. Current all-relations derivation excludes superseded appearances, entity relations, and work relations, while migration ledgers keep their provenance visible. A later official status change requires a new source audit rather than silently reviving the old row.
