# AGENTS.md — marvel-flowchart-jp

This file defines persistent working rules for Codex and other coding agents operating in this repository.

## Repository and branch discipline

- Repository: `kamochama/marvel-flowchart-jp`.
- Production branch: `main`.
- Latest semantic production baseline after PR #47 is `28941193ec2b5c3fb18a57b02ac3fbc2b2e376c9`.
- PR #10 (Events & Multiverse), PR #11 (release/status normalization), PR #12 (HTML DB export), PR #13 (Pages artifact fix), PR #21 (mobile touch-target contract), PR #22 (X-Men '97 release/status evidence promotion batch005), PR #26 (VisionQuest production-status evidence promotion batch006), PR #28 (Avengers: Doomsday release/status evidence promotion batch007), PR #30 (full release/status evidence audit), PR #32 (HTML design/operation debugging), PR #38 (all-work browser selection audit), PR #40 (browser interaction state audit), PR #45 (Deadpool & Wolverine variant fan-out audit), and PR #47 (direct relation evidence promotion wave001) are merged into `main`.
- PR #30 promoted 27 release/status facts with exact evidence and review transitions; 240 facts remain deferred and 2 remain in explicit conflict.
- There is no currently approved semantic forward branch. Create a new `codex/` branch only after selecting a bounded plan for the next work.
- During development, **do not commit directly to `main`, publish production changes, rebase the forward history, force-push, or rewrite canonical history unless the user explicitly authorizes it.**
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

## Windows command execution and Python runtime

- In Codex Desktop on this repository, do **not** assume that `python` resolves to a runnable interpreter. The system command may be missing, and a user-installed Python can fail with `Access is denied` in the sandbox.
- Use the bundled Codex runtime explicitly from PowerShell. Set a task-specific variable and invoke it with the call operator (`&`):

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

実ブラウザの131作品×2 tier選択監査を行う場合は、Chrome / Chromiumを用意したうえで次を実行する。監査ランナーが一時HTTPサーバーを起動し、独立Pythonオラクルと実SVG点灯を比較する。Chromeを自動検出できない場合は `MARVEL_CHROME_BIN` に絶対パスを設定する。

```powershell
$env:MARVEL_BROWSER_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_selection_audit.BrowserSelectionAuditTests.test_headless_dom_matches_python_oracle_for_both_public_tiers -v
```

PC版の操作状態を代表ケースで監査する場合は、同じChrome/CDP方式で次を実行する。再クリック解除、背景クリック解除、ドラッグ後の選択維持、公開順・世界線／時系列・右パネル切替後の再点灯を、内部関数を直接呼ばず実操作とDOM状態で確認する。

```powershell
$env:MARVEL_BROWSER_INTERACTION_AUDIT = '1'
& $MarvelPython -m unittest tests.library_v5.test_browser_interaction_audit.BrowserInteractionAuditTests.test_headless_interactions_preserve_selection_contract -v
```

- Keep the `&` before a quoted executable path; without it PowerShell treats the path as text rather than launching it. Prefer repository modules (`-m ...`) over ad-hoc inline scripts. If the bundled path changes, resolve the current workspace runtime before substituting a new path; do not silently fall back to a different Python.
- For final verification, run the exact commands above from the repository root. The build may create transient audit/DB outputs under `data/content_audit/` and `data/derived/`; inspect the result first, then remove only the known generated paths when the workflow requires a clean working tree. Never delete canonical CSVs or `data/content_audit/reviews.csv`.
- Run strict CSV shape checks when editing CSV notes that contain commas. `csv.DictReader` can hide an extra field, so every row must have exactly the header column count; quote the complete notes field when it contains commas.
- `git fetch origin` is the safe freshness check before editing. If `.git/FETCH_HEAD` or `.git/index.lock` returns `Permission denied`, do not reset or overwrite the checkout; use GitHub Desktop/elevated local Git controls and then re-check `git rev-parse HEAD` against the relevant `origin/*` ref.

## Subagent collaboration

- Use subagents for bounded, independent work such as source/evidence audits, RED-test design, schema/CSV shape review, or read-only diff review. Do not have multiple agents edit the same canonical CSVs concurrently.
- Route each requested high-quality subagent explicitly with the current allowlisted model and effort. For the current Phase 2 workflow, the preferred invocation is `model: gpt-5.6-luna`, `reasoning_effort: xhigh`, and `fork_turns: none` for a clean context. Set both model and effort on every spawn; never copy stale model names from an old handoff.
- Give reviewers a read-only scope when possible. After a subagent reports, the primary agent must independently inspect the working-tree diff and rerun the relevant tests/build; a subagent report is evidence to investigate, not proof of completion.
- For a fix round, send a follow-up to the existing agent with `followup_task` instead of spawning a duplicate implementer. While local work remains, continue local execution without busy-polling; wait on outstanding agents only when otherwise idle.

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

The latest integrated production/audit baseline after PR #47 is:

- `main` `28941193ec2b5c3fb18a57b02ac3fbc2b2e376c9` (merge commit for PR #47)
- PR #47 required checks: GREEN (`test`, `browser-selection-audit`, `browser-interaction-audit`, `browser-chronology-audit`, and `browser-publication-order-audit`)
- 439 / 439 library-v5 unit tests PASS locally (4 browser tests are environment-gated skips in the ordinary suite)
- real Chrome/CDP audit: 131 works × 2 public tiers, exact-set mismatches `0`
- real Chrome/CDP interaction audit: 6 / 6 representative cases PASS
- real Chrome/CDP chronology audit: 7 cases, failures `0`
- real Chrome/CDP publication-order audit: 131 cards, 21 cases, failures `0`, synthetic edges `0`
- audit issues: 0
- review-integrity issues: 0
- FK check rows: 0
- SQLite integrity: `ok`
- releases: 138 rows (14 `source_verified`, 124 `legacy_seed`)
- production-status assertions: 131 rows (13 `source_verified`, 118 `legacy_seed`)
- work relations: 164 rows (9 `source_verified`, 152 `legacy_seed`, 3 `superseded`)
- sources: 49
- evidence: 133
- reviews: 108
- `work_edges_all`: 355
- `work_pair_reasons`: 562
- prewatch edges: 199
- story paths reproduced: 83 / 83
- events / occurrences / transitions / transition participants: 9 / 9 / 9 / 10

PR #30 also records the strict full-audit disposition for all 269 release/status facts: 27 promoted, 240 deferred, and 2 conflicts retained as seeds. PR #32 records the UI regression contract and desktop/mobile operation audit for the three watch-plan tiers and the official prewatch route highlight. PR #38 adds the independent all-work selection oracle, real DOM exact-set audit, and CI browser job; PR #40 adds representative PC interaction-state coverage and a dependent CI browser job; neither changes canonical data.

These numbers document the checkpoint. They are not frozen targets except where a test explicitly encodes semantic compatibility. Future legitimate first-class facts can increase row counts while preserving protected graph compatibility.

## Current-plan completion and production integration gate

The approved Events & Multiverse execution plan (Tasks 1–8), normalized release/status integration, HTML DB export, mobile touch-target fix, X-Men '97 batch005, VisionQuest batch006, Avengers: Doomsday batch007, the full release/status evidence audit (PR #30), the HTML design/operation debugging pass (PR #32), the all-work browser selection audit (PR #38), the representative browser interaction-state audit (PR #40), the Deadpool & Wolverine variant fan-out audit (PR #45), and direct relation evidence promotion wave001 (PR #47) are integrated into `main`. The next viewer or semantic change must use its own bounded plan, RED/UI regression contract, evidence/review audit where applicable, and full verification.

For every future branch:

1. fresh-check `main` and the relevant remote branch;
2. audit the full diff, not only recent commits;
3. verify branch CI and content-audit invariants;
4. summarize migrated/deferred cases and production impact;
5. obtain explicit user authorization before the final merge unless a standing authorization explicitly covers that exact batch.

If authorized, merge through the normal PR path, never force-update or rewrite `main`, then verify the resulting `main` HEAD, CI, GitHub Pages/public behavior, and generated artifacts. Record the new production baseline in the handoff/roadmap.

Later DB-v1 phases remain architecturally intended but require their own approved execution boundary. The current integrated HTML export is production baseline; see `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md` and `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md` for the next-boundary candidates.

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

- complete remaining normalized semantic domains such as credits, aliases, memberships, and possessions; releases and production-status assertions are present; batch007 verified the Avengers: Doomsday announced status and remaining seed rows require their own bounded audits;
- continue evidence-backed multiverse decomposition;
- switch `index.html` to DB-derived node/edge JSON rather than independent Marvel fact arrays;
- preserve static GitHub Pages deployment;
- preserve Pixel-6/mobile performance while the HTML data source changes;
- continue the broader 131-work content audit using the richer semantic model.

Do not start new semantic phases automatically after the integrated HTML export. They require a separately approved plan/boundary and a RED contract before canonical changes.

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
