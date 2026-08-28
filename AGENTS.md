# AGENTS.md — marvel-flowchart-jp

This file defines persistent working rules for Codex and other coding agents operating in this repository.

## Repository and branch discipline

- Repository: `kamochama/marvel-flowchart-jp`.
- Production branch: `main`.
- Current forward development branch for Marvel Library DB v1 Phase 2: `library-v5-phase2-db6`.
- Draft PR: #10, base `main`, head `library-v5-phase2-db6`.
- During development, **do not merge PR #10, commit directly to `main`, publish production changes, rebase the forward history, force-push, or rewrite canonical history unless the user explicitly authorizes it.**
- `main` is **not permanently frozen**. It is the intended final integration target after the current work is complete, fully audited, and the user explicitly approves the final merge.
- At the start of every session, run/fetch a fresh HEAD check. If local HEAD differs from origin, reconcile before editing; never overwrite a newer remote state blindly.
- The former PR #9 / `library-v5-canonical-freeze` history was already reconciled into the forward line. Do not merge it again.

## Required reading before Phase 2 work

Read these files before changing Phase 2 semantics:

1. `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md` — exact current execution boundary.
2. `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md` — long-range roadmap through the current PR integration gate and later DB-v1 milestones.
3. `NEXT_CHAT_HANDOFF_MARVEL_DB_PHASE2_RECONCILED_2026-08-28.md` — historical reconciliation context.
4. `docs/superpowers/plans/2026-08-27-marvel-library-db-v1-phase2-events-multiverse.md` — approved current Phase 2 execution plan.
5. `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` — broader DB-v1 architecture and later phases.

If any handoff SHA is stale, trust the repository's fresh HEAD and reconcile the documentation rather than resetting code to an older checkpoint.

Historical documents use overlapping phase names. When reporting status, identify the specific plan/task rather than saying only “Phase 2”. The current Events & Multiverse execution plan and the broader DB-v1 design phase vocabulary are not identical.

## Development method

- Use TDD for behavioral or semantic changes: **RED test -> minimal implementation/data change -> GREEN -> full verification**.
- Do not weaken/delete a failing regression test merely to make CI green. First determine whether the implementation or an obsolete historical assumption is wrong.
- For bugs or unexpected fan-out, isolate the root cause before patching. Add a regression test that reproduces the failure.
- Do not claim completion without fresh verification output.
- Prefer small, auditable commits. For large CSVs, verify the per-file diff after every write and immediately revert unrelated line changes.

## Canonical data rules

Canonical data lives under `data/library/`; persistent audit history lives under `data/content_audit/`.

- Ordinary builds must be read-only with respect to canonical CSVs and persistent review ledgers.
- `source_verified` facts require qualifying evidence in `data/library/evidence.csv`.
- New verified facts require explicit review history in `data/content_audit/reviews.csv`, normally `created_verified`.
- Status/meaning changes to an existing verified fact require an auditable review transition; do not silently edit semantics.
- Record completed migration batches in `data/content_audit/applied/` when the surrounding Phase 2 workflow uses an applied-patch record.
- Treat row counts as observations, not correctness targets.
- Preserve existing primary keys and IDs unless there is an explicit migration reason to replace them.

## Multiverse semantic boundaries

These are safety invariants, not suggestions:

- A work-to-work edge is a **derived view**, not the semantic home of a crossing.
- The semantic home of a crossing is `events.csv` + `event_occurrences.csv` + `multiverse_transitions.csv` + participant facts.
- `event_occurrence` means "this work depicts/contains the event"; it does **not** assert chronology between source-world films.
- Shared continuity alone must never manufacture a new work pair.
- A transition may enrich only an already independently supported pair under the conservative derivation rules.
- Same performer does not imply same character identity.
- `identity_of` may collapse aliases; variants remain distinct unless explicitly audited.
- Do not invent Earth numbers, universe identities, or exact variant continuity that the evidence does not support.
- Keep `continuity-earth-616` distinct from the legacy grouping `continuity-mcu`.
- Keep descriptive/uncertain alternate-universe contexts separate from legacy FOX X-MEN or Doomsday return contexts unless a source proves equivalence.
- Do not infer that a traveler seen arriving was aboard a vehicle unless evidence confirms that participant.
- Do not infer a transport mechanism; use `unknown` when the available source does not establish one.

## Proxy relation retirement

- Do not retire an existing `work_relation` simply because a first-class transition now exists.
- First prove with a fixture/test that the intended work pair survives independently after the proxy is temporarily superseded.
- Retire only a **pure crossing proxy** whose semantic job is fully replaced.
- Keep a relation active when it still expresses an independent causal, editorial, sequel, lead-in, or story assertion.
- Record proxy retirement with review history and supporting transition evidence.

Examples already established:

- Raimi Peter -> No Way Home and Webb Peter -> No Way Home pure crossing proxies were superseded after parity proof.
- Venom: Let There Be Carnage -> No Way Home pure crossing proxy was superseded after Eddie Brock appearance + two directional transition facts independently preserved the pair.
- No Way Home -> Morbius remains active because it carries an independent causal assertion about Adrian Toomes' transfer.
- Thunderbolts* -> First Steps remains active until independent replacement support is proven.

## Transition-reason derivation guardrails

- `scripts/library_v5/db_transition_support.py` contains the current post-install transition reason support logic.
- Verified traveler appearances are stronger anchors than generic continuity fallback.
- If a transition participant has a source-verified appearance in the opposite endpoint work, use that precise anchor and do not fan the transition reason across other continuity-neighbor pairs.
- The representative-source logic for Raimi/Webb Peter must remain stable.
- New multiverse facts such as Monica Rambeau's alternate-universe arrival or Doctor Strange's Earth-838 traversal may legitimately produce **no new work reason** when there is no independently supported second-work pair.

## Current compatibility invariants

The latest implementation checkpoint before the Codex documentation commits is:

- `ad9796b3a1833d49e044a4eef220ca9d49c3553d`
- GitHub Actions run #251: GREEN
- 161 / 161 unit tests PASS
- audit issues: 0
- review integrity issues: 0
- FK check rows: 0
- SQLite integrity: `ok`
- `work_edges_all`: 361
- `work_pair_reasons`: 569
- prewatch edges: 199
- story paths reproduced: 83 / 83
- events / occurrences / transitions / transition participants: 8 / 8 / 8 / 8

These numbers document the checkpoint. They are not frozen targets except where a test explicitly encodes semantic compatibility. Future legitimate first-class facts can increase row counts while preserving protected graph compatibility.

## Current-plan completion and production integration gate

The current approved Events & Multiverse execution plan ends with Task 8, the Phase 2 completion audit.

After Task 8 is GREEN:

1. fresh-fetch `main` and PR #10;
2. audit the full PR, not only recent commits;
3. verify all branch CI and content-audit invariants;
4. summarize migrated/deferred cases and production impact to the user;
5. **stop and obtain explicit user authorization for final merge**.

If the user explicitly authorizes final integration:

- merge PR #10 into `main` through the normal PR path;
- do not force-update or rewrite `main`;
- verify fresh `main` HEAD and CI;
- verify GitHub Pages/public behavior and expected generated artifacts;
- document the new production baseline.

If authorization is not given, leave production unchanged. Do not interpret “finish the branch” as permission to publish.

Later DB-v1 phases are architecturally intended but require their own approved execution boundary. See `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`.

## Verification commands

At minimum, before claiming a Phase 2 batch complete, run:

```bash
python -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
python -m scripts.library_v5.build --repo-root .
```

The GitHub Actions workflow `.github/workflows/library-v5-ci.yml` is the authoritative full verification surface. It additionally checks:

- canonical inputs unchanged by ordinary build;
- logical DB determinism;
- graph regeneration without `index.html`;
- ordinary build determinism;
- SQLite foreign keys and integrity;
- bootstrap determinism and canonical isolation;
- content-audit review integrity.

If local environment/network behavior is unreliable, use CI as the final execution surface rather than weakening verification.

## Broader DB-v1 direction

The approved DB-v1 architecture ultimately intends to:

- complete normalized semantic domains such as releases, production-status assertions, credits, aliases, memberships, and possessions;
- continue evidence-backed multiverse decomposition;
- switch `index.html` to DB-derived node/edge JSON rather than independent Marvel fact arrays;
- preserve static GitHub Pages deployment;
- preserve Pixel-6/mobile performance while the HTML data source changes;
- continue the broader 131-work content audit using the richer semantic model.

Do not start these later phases automatically after the current Task 8. They require a separately approved plan/boundary.

## Public site packaging constraint

When later producing the public GitHub Pages ZIP, keep the established root structure exactly:

- `index.html`
- `README.md`
- `AUDIT.md`
- `AUDIT.json`
- `preview.png`
- `.nojekyll`

Do not add version-named duplicate HTML files inside the distribution ZIP.

## Communication / working style

- Explain progress and decisions in Japanese unless asked otherwise.
- Continue autonomously when the user says `進めて`; do not stop for routine choices that are already governed by these rules.
- Surface semantic uncertainty rather than guessing.
- Never merge/publish production without explicit user authorization, but remember that approved final integration into `main` is an intended project milestone rather than a prohibited outcome.
