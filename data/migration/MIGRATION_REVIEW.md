# Marvel Library v5 Migration Review

This review inventories migration dispositions. Counts are observations, not correctness targets.

## Dataset coverage

- connections: 199
- entity_seeds: 163
- story_paths: 83
- chronology: 103

## connections dispositions

- appearance_derived_pending_audit: 36
- migrated_explicit_relation: 159
- migrated_promotion_fact: 3
- rejected_superseded: 1

## entity_seeds dispositions

- decomposed_entity_return_seed: 8
- migrated_appearance_seed: 155

## story_paths dispositions

- reproduced_from_v5_graph: 83

## chronology dispositions

- legacy_display_placement_seed: 103

## Content-audit backlog

- appearance_derived_pending_audit: 36
- decomposed_entity_return_seed: 8
- legacy_display_placement_seed: 103
- migrated_appearance_seed: 155
- migrated_explicit_relation: 159
- migrated_promotion_fact: 3
- rejected_superseded: 1

## Interpretation

- `migrated_*` and `*_seed` rows are preserved legacy knowledge and still require independent source review before promotion to `source_verified`.
- `appearance_derived_pending_audit` rows must be explained by canonical appearances/portrayals/entity relations rather than copied back as work-to-work facts.
- `legacy_display_placement_seed` rows are display history only and must not become chronology facts without evidence.
- `rejected_superseded` remains visible as a watch item so a later official status change cannot be silently missed.
- reproduced story-path rows are compatibility observations, not canonical source facts.
