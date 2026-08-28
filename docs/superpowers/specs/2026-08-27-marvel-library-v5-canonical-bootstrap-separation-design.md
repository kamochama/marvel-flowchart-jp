# Marvel Library v5 Canonical Bootstrap Separation Design

## Status

- Date: 2026-08-27
- Base implementation branch: `library-v5-migration`
- Production baseline: `main` at `3af097b72c174077c83d7091f79222a72fc7134f` (`v5.20.5`)
- Depends on:
  - `docs/superpowers/specs/2026-08-27-marvel-library-v5-design.md`
  - `docs/superpowers/specs/2026-08-27-marvel-library-v5-audit-status-clarification.md`
- Decision: adopt **A — frozen canonical library + separate one-time bootstrap migration**.
- Production `main` remains unchanged until explicit integration approval.

## 1. Problem

The migration implementation successfully produced a normalized v5 library, but the current `scripts.library_v5.build` still treats `data/library/*.csv` as generated migration output. A clean build deletes and recreates those files from legacy v5.20.5 inputs.

That behavior is correct for bootstrap migration, but incorrect once content auditing begins. If a reviewer upgrades a fact from `legacy_seed` to `source_verified`, adds evidence, records a conflict, or supersedes an old assertion, a later clean migration build must never erase that human-audited canonical state.

Therefore bootstrap reconstruction and ordinary library build/audit must become separate operations with different write permissions.

## 2. Core invariant

After bootstrap freeze:

> **`data/library/` is canonical input, not build output.**

Ordinary build, audit, derivation, CI, and view generation may read `data/library/`, but they must not create, delete, rewrite, normalize, reorder, or otherwise modify canonical library files.

The only accepted ways to modify canonical facts are explicit content-audit edits or an explicitly invoked bootstrap/install operation intended for migration recovery. Ordinary CI never performs such writes.

## 3. Repository layers after separation

### 3.1 Canonical facts — `data/library/`

Human-audited source of truth.

Includes the current canonical tables defined by schema 5.0:

- `works.csv`
- `entities.csv`
- `entity_relations.csv`
- `appearances.csv`
- `people.csv`
- `portrayals.csv`
- `continuities.csv`
- `work_continuities.csv`
- `chronology_assertions.csv`
- `work_relations.csv`
- `sources.csv`
- `evidence.csv`
- `schema.json`

These files survive every ordinary clean build byte-for-byte.

`manifest.json` is no longer stored here because it is generated state.

### 3.2 Bootstrap migration artifacts — `data/migration/bootstrap/`

Reproducible reconstruction of the initial v5 canonical seed from v5.20.5 legacy inputs.

Bootstrap outputs include candidate copies of canonical tables plus the legacy extraction/disposition ledgers. They exist to answer “how did the first v5 seed come from v5.20.5?” and to permit deterministic recovery/testing.

Bootstrap output is never silently installed over `data/library/`.

### 3.3 Frozen migration review — `data/migration/`

Migration ledgers and review reports remain historical evidence of the v4/v5.20.5-to-v5 transition. Ordinary build may validate them but does not regenerate or reinterpret them unless bootstrap mode is explicitly invoked.

### 3.4 Derived graph products — `data/derived/`

Generated from current canonical facts only. Safe to delete and regenerate.

Includes:

- `work_pair_reasons.csv`
- `work_edges_all.csv`
- `prewatch_edges.csv`
- `story_paths.csv`
- generated manifest/hash reports

No derived file is canonical.

### 3.5 Content-audit records — `data/content_audit/`

Human-review history and review queues. These are not graph facts, but they are persistent audit records and therefore are not deleted by ordinary build.

Initial files:

- `reviews.csv` — append-oriented record of fact review decisions;
- `queue.csv` — generated/reviewable queue of facts still requiring verification;
- `CONTENT_AUDIT.md` — generated summary of verification progress and unresolved conflicts.

`reviews.csv` is persistent input. `queue.csv` and `CONTENT_AUDIT.md` are generated views of canonical status plus review history.

### 3.6 Flowchart view — `views/flowchart/`

View policy remains downstream of facts. It may consume verification/certainty/provenance fields to choose opacity, glow, filtering, labels, and explanations, but cannot modify or suppress canonical fact existence.

## 4. Commands and write boundaries

### 4.1 Ordinary build

Canonical command remains:

```bash
python -m scripts.library_v5.build --repo-root .
```

It must:

1. treat `data/library/` as read-only input;
2. validate schema, FKs, verification/evidence invariants, and content-review references;
3. regenerate only safe generated products (`data/derived/`, generated audit summaries, generated queue/report files);
4. compare deterministic manifests across repeated runs;
5. fail if canonical files changed during the command.

It must not invoke legacy extraction or migration writers.

### 4.2 Bootstrap reconstruction

A separate explicit command performs the old migration role:

```bash
python -m scripts.library_v5.bootstrap --repo-root .
```

Default behavior writes only under `data/migration/bootstrap/` and never touches canonical files.

It deterministically reconstructs the initial v5 seed and migration ledgers from the pinned legacy inputs. CI may run this command and compare the bootstrap snapshot with the recorded initial seed baseline, but it may not install it.

### 4.3 Bootstrap installation

Installing a bootstrap snapshot over canonical facts is exceptional and intentionally noisy:

```bash
python -m scripts.library_v5.bootstrap --repo-root . --install-canonical
```

Requirements:

- must be explicit; no default or CI path uses it;
- refuses to run when `data/library/` contains facts whose verification state or evidence differs from the frozen initial bootstrap baseline, unless an additional destructive override is supplied;
- prints every canonical file to be replaced;
- intended only for migration recovery before content-audit work, not routine maintenance.

The implementation plan may choose an even safer staging-and-copy mechanism, but it must preserve this semantic boundary.

## 5. Canonical immutability guard

Ordinary build and CI record SHA-256 hashes of all canonical input files before derivation and compare them after all build/audit steps.

Any change produces a hard failure such as `canonical_input_mutated`.

This guard protects against accidental writes by:

- cleanup code;
- migration helpers accidentally imported by ordinary build;
- audit normalization;
- CSV sorting/reformatting;
- GitHub Actions persistence steps.

CI persistence may commit generated derived/audit products, but its `git add` paths must exclude `data/library/` and persistent human review input.

## 6. Generated manifest location

`data/library/manifest.json` was useful during migration but violates the frozen-canonical rule because it is generated.

The ordinary build moves generated hash metadata to:

- `data/derived/library_manifest.json`

The manifest records hashes of canonical inputs and generated outputs separately so a reviewer can distinguish “what facts were read” from “what graph was produced.” The manifest excludes itself and generated audit summaries from its own digest set.

A compatibility copy in `data/library/` is not maintained.

## 7. Content audit workflow

### 7.1 Audit unit

The audit unit is a canonical fact row, not a visual line and not an entire work.

A work-focused review batch may inspect all relevant facts for one or more works, but each fact receives its own evidence and verification state.

### 7.2 Allowed verification transitions

Normative vocabulary remains:

- `legacy_seed`
- `source_verified`
- `conflicted`
- `superseded`

Typical transitions:

- `legacy_seed -> source_verified` when qualifying non-legacy evidence is added;
- `legacy_seed -> conflicted` when credible evidence disagrees or identity/continuity cannot be resolved;
- `legacy_seed -> superseded` when a migrated assertion is no longer current;
- `conflicted -> source_verified` only after the conflict is actually resolved and evidence history is retained.

No transition is inferred solely from legacy confidence.

### 7.3 Evidence rule

Promotion to `source_verified` requires at least one qualifying `evidence.csv` row with `evidence_role=primary` or `supporting` and a source meeting the source policy.

`legacy_seed` evidence never promotes a fact.

Conflicting sources are retained rather than overwritten.

### 7.4 Review log

`data/content_audit/reviews.csv` records review history with stable rows such as:

- `review_id`
- `fact_table`
- `fact_id`
- `previous_verification_status`
- `new_verification_status`
- `review_action`
- `evidence_ids`
- `reviewed_at`
- `notes`

A review row explains the decision; the canonical table still stores the current state.

The audit validates that every referenced fact/evidence ID exists and that claimed status transitions agree with current canonical state.

## 8. Content-audit queue

The queue is generated deterministically from canonical facts and review status rather than manually maintained as a second source of truth.

Priority order for the first pass:

1. current/future and status-sensitive works or relations;
2. high-degree convergence targets where a bad fact creates many derived lines;
3. migrated `appearance_derived_pending_audit` relationships;
4. continuity membership and chronology claims;
5. remaining legacy appearance/portrayal seeds.

The first planned work-focused batch centers on the current high-impact cluster already present in the project: Doomsday, Brand New Day, The Fantastic Four: First Steps, VisionQuest, Wonder Man, Secret Wars, Thunderbolts*, and their immediate source/target relations. Exact facts are determined from the canonical queue at execution time; no fixed edge count is a success criterion.

## 9. Derived-edge behavior during partial audit

The library must remain usable while most rows are still `legacy_seed`.

Derived reasons retain supporting fact IDs, appearance kinds, verification statuses, and certainty values. Therefore an all-relations graph may continue to include seed-supported relations while the view later chooses how strongly to render them.

Current derivation excludes `superseded` facts. `conflicted` facts remain representable as conflicted provenance unless a specific derivation policy explicitly requests verified-only output.

No audit status change is allowed to silently merge distinct source works or fictional entities.

## 10. CI behavior

The migration branch CI is changed from “rebuild canonical migration outputs and commit them” to “validate frozen canonical inputs and regenerate downstream products.”

Required checks:

1. all unit tests;
2. canonical pre/post SHA equality;
3. ordinary build/audit;
4. canonical-only edge regeneration;
5. second clean ordinary build with byte-identical derived manifest;
6. bootstrap reconstruction in staging and deterministic comparison;
7. verification/evidence integrity;
8. content-review ledger integrity;
9. `main` remains unchanged during this work.

CI auto-commit, if retained, may stage only explicitly generated downstream paths. It must never stage `data/library/` or `data/content_audit/reviews.csv`.

## 11. Migration freeze point

The canonical CSV state produced at the end of migration Task 8 becomes the **initial v5 bootstrap baseline**.

Its purpose is historical reproducibility, not ongoing regeneration.

The existing observations remain observations rather than correctness targets, including the then-current counts of works, appearances, relations, and derived edges. Later content audit may legitimately change canonical and derived counts.

The frozen migration review keeps the known v5.20.5 disposition facts, including the one superseded Wonder Man Season 2 relation decision, without forcing later audits to preserve old counts.

## 12. Failure handling

The ordinary build fails rather than repairing canonical data when it sees:

- malformed canonical CSV;
- schema/header mismatch;
- broken FK;
- duplicate fact ID;
- invalid verification/certainty enum;
- `source_verified` fact without qualifying evidence;
- review ledger referencing nonexistent facts/evidence;
- canonical pre/post hash change;
- nondeterministic derived output.

Recovery instructions point either to an explicit canonical edit or to bootstrap staging. Ordinary build never “fixes” facts automatically.

## 13. Non-goals

This separation does not yet:

- finish external research for all 131 works;
- finalize flowchart line opacity/glow values;
- merge the migration branch to `main`;
- redesign the public HTML layout;
- treat fixed legacy or derived edge counts as correctness requirements.

## 14. Definition of done

The separation is complete when:

- normal build does not write any file under `data/library/`;
- clean build no longer invokes legacy extraction/migration writers;
- bootstrap migration has its own explicit staging command;
- bootstrap reconstruction is deterministic;
- canonical pre/post SHA guard is enforced by tests and CI;
- generated manifest lives outside `data/library/`;
- review history has a persistent non-generated home;
- audit queue/report can be generated from current canonical state;
- derived graph generation continues without `index.html`;
- repeated ordinary builds are byte-identical;
- production `main` remains unchanged pending explicit approval.

Once these conditions pass, source-backed content auditing can safely begin without later clean builds destroying reviewed facts.
