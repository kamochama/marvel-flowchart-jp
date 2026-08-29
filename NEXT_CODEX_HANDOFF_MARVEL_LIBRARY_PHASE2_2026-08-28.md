# Codex handoff — Marvel Library DB v1 Phase 2 (2026-08-28)

This is the current execution handoff for Codex. Read `AGENTS.md` first; its rules are persistent and mandatory.

## 0. Start here

Repository:

- `kamochama/marvel-flowchart-jp`

Current production branch:

- `main`
- current HEAD: `8234cfa04edf5fb6dd851d335107d606b9011731`

The previous forward line and its follow-up PRs are now integrated:

- PR #10 Events & Multiverse: merged as `2410ea482d9fe6c9063a23b80b9b766e2bb9daac`
- PR #11 releases/status normalization: merged as `d5c878d5763b2bd91940c31052db6e35a3e69d0a`
- PR #12 HTML DB export: merged as `00a7e703616821eec0e4b081cfc656d7fd0ec167`
- PR #13 Pages artifact fix: merged as `8234cfa04edf5fb6dd851d335107d606b9011731`

There is no currently approved semantic implementation branch. Create a new `codex/` branch only after the next bounded execution plan is selected. Do not commit directly to production `main`.

The last pre-integration implementation checkpoint was:

- `ad9796b3a1833d49e044a4eef220ca9d49c3553d`
- message: `audit: record Earth-838 transition reviews`
- GitHub Actions run #251: SUCCESS

Then documentation-only Codex setup began:

- `e2977fec4924cd241f16513add96d71b93fc58dd`
- message: `docs: add Codex project instructions`
- adds `AGENTS.md`

This handoff is historical context, not a checkout target. **Always check the fresh remote HEAD before doing anything** and reconcile documentation if it is stale; never reset code back to an older checkpoint.

Suggested local startup:

```bash
git status
git branch --show-current
git fetch origin
git checkout main
git pull --ff-only origin main
git log -5 --oneline
```

If the working tree is not clean or remote HEAD differs unexpectedly, reconcile first; do not discard user/local changes blindly.

## 0.1 Production baseline after the 2026-08-29 integration

The static viewer now consumes the committed DB-derived artifact `data/derived/flowchart.json`; the browser does not open SQLite. The artifact contains 131 nodes, 361 directed edges, 569 traceable reasons, and 42 character groups, with all eligible edges visible by default and selection limited to presentation styling.

The post-merge Pages deployment (run #37) succeeded, and the public page was smoke-tested at `https://kamochama.github.io/marvel-flowchart-jp/`: the status reached `データを読み込みました（131作品）。` with no browser console errors. The Pages 404 found immediately after PR #12 was fixed by PR #13, which versions the generated artifact and adds a regression test.

The current local verification baseline for the integrated HTML export is 232 library-v5 tests passing and an ordinary bundled-Python build with audit issue count 0. These counts are observations, not frozen correctness targets.

The next semantic work is not implicitly authorized by the completed export. Candidate boundaries are an evidence-backed promotion audit for a small subset of the 269 `legacy_seed` release/status facts, or a separately planned normalized domain (`credits`, `entity_aliases`, `entity_memberships`, or `entity_possessions`). Do not change canonical data until one bounded plan and its RED contract are selected.

## 1. Required context

Read in this order:

1. `AGENTS.md`
2. this file
3. `NEXT_CHAT_HANDOFF_MARVEL_DB_PHASE2_RECONCILED_2026-08-28.md`
4. `docs/superpowers/plans/2026-08-27-marvel-library-db-v1-phase2-events-multiverse.md`

Historical reconciliation is already complete:

- former PR #9 / branch `library-v5-canonical-freeze` is already an ancestor of the forward line via history-only merge `8fcdc53578c5d2f022572698eea1306d3945502f`.
- Do not merge PR #9 again.

## 2. Architecture already completed

DB v1 Phase 1 is complete and should be treated as established infrastructure:

- frozen canonical CSV model;
- SQLite schema/compiler;
- identity resolution;
- SQL public views;
- semantic parity with legacy Python graph reasoning;
- logical DB fingerprint;
- SQLite exporter;
- ordinary build routed through SQLite;
- deterministic CI and bootstrap isolation.

Phase 2 Tasks 1–4 are complete:

1. first-class event/transition schema;
2. compilation + semantic integrity;
3. public event/multiverse views;
4. conservative transition-derived work reasons.

Important implementation files include:

- `scripts/library_v5/db_compile.py`
- `scripts/library_v5/db_views.py`
- `scripts/library_v5/db_rollup.py`
- `scripts/library_v5/db_transition_support.py`

`db_transition_support.py` contains the newer verified-traveler anchor rule used to prevent transition-reason fan-out.

## 3. Historical Events & Multiverse verified baseline

Implementation checkpoint `ad9796b3...`, Actions run #251:

- 161 / 161 unit tests PASS
- audit issues: 0
- review integrity issues: 0
- FK check rows: 0
- SQLite integrity: `ok`
- DB schema: `1.1-phase2-events`
- prewatch edges: 199
- story paths reproduced: 83 / 83
- `work_edges_all`: 361
- `work_pair_reasons`: 569
- works: 131
- entities: 43
- appearances: 168
- continuities: 9
- events: 8
- event occurrences: 8
- multiverse transitions: 8
- transition participants: 8
- evidence: 93
- reviews: 66
- sources: 43

Full CI also passed:

- canonical read-only ordinary build;
- logical DB determinism;
- graph regeneration without `index.html`;
- ordinary-build determinism;
- SQLite FK/integrity;
- bootstrap determinism + canonical isolation.

These counts document this checkpoint. They are observations, not global correctness targets. Preserve them only where the tests/semantics require parity.

## 4. Completed Phase 2 semantic batches

### Task 5 — Thunderbolts* / First Steps ship crossing

First-class facts model the Fantastic Four spacecraft Excelsior / F4-marked spacecraft:

- Earth-828 -> Earth-616;
- depicted in the `Thunderbolts*` post-credit;
- confirmed participant is the ship only.

Do not infer Reed/Sue/Johnny/Ben aboard.

Legacy work relation remains active:

- `work-relation-thunderbolts-new-avengers-2025-the-fantastic-four-first-steps-2025-crossover`

It has **not** yet been proven safe to retire independently.

### Task 6 — No Way Home legacy Peter crossings

Complete including audited proxy retirement.

- `event-nwh-raimi-peter-arrival`
- `event-nwh-webb-peter-arrival`

Raimi / Webb / MCU Peters remain separate canonical entities.

Pure crossing proxies now superseded after parity proof:

- `work-relation-spider-man-3-2007-spider-man-no-way-home-2021-crossover`
- `work-relation-the-amazing-spider-man-2-2014-spider-man-no-way-home-2021-crossover`

A prior fan-out bug was fixed by representative participant/source-work selection.

## 5. Task 7 completed sub-batches

Task 7 is proceeding one high-confidence multiverse migration at a time with RED -> evidence -> canonical facts -> review history -> GREEN.

### 7.1 Eddie Brock / Venom round trip — COMPLETE

Canonical Eddie entity:

- `entity-eddie-brock-sony`

Eddie is intentionally modeled separately from the Venom symbiote.

Source-verified appearances:

- LTBC: `appearance-venom-let-there-be-carnage-2021-entity-eddie-brock-sony`
- NWH: `appearance-spider-man-no-way-home-2021-entity-eddie-brock-sony`

Directional transitions:

- `event-ltbc-eddie-brock-earth616-arrival`
  - `continuity-ssu` -> `continuity-earth-616`
  - mechanism `unknown`
  - depicted in LTBC credits

- `event-nwh-eddie-brock-ssu-return`
  - `continuity-earth-616` -> `continuity-ssu`
  - mechanism `unknown`
  - depicted in NWH mid-credit

No Sony-universe Earth number was invented.

Important derivation fix:

- verified participant appearance anchors outrank generic continuity fallback;
- without this rule the transition reason incorrectly spread to Venom (2018), The Last Dance, and Morbius neighboring pairs.

The old LTBC -> NWH pure crossing proxy was independently reproduced by Eddie shared-entity + transition facts and is now superseded:

- `work-relation-venom-let-there-be-carnage-2021-spider-man-no-way-home-2021-crossover`

Audit record:

- `data/content_audit/applied/2026-08-28-venom-round-trip-transition-phase2.json`

### 7.2 Adrian Toomes / Vulture — COMPLETE

First-class event:

- `event-morbius-adrian-toomes-ssu-arrival`
- Earth-616 -> `continuity-ssu`
- mechanism `unknown`
- occurrence is the `Morbius` post-credit
- traveler: existing canonical `entity-adrian-toomes-vulture`

Important semantic distinction:

- `Morbius` is the **depiction work** for the transition;
- `No Way Home` is retained separately as the **causal work** according to the director evidence.

Therefore this relation remains active and must not be retired as a pure proxy:

- `work-relation-spider-man-no-way-home-2021-morbius-2022-crossover`

The transition reason enriches the independently supported Homecoming -> Morbius same-Vulture pair only.

Audit record:

- `data/content_audit/applied/2026-08-28-vulture-transfer-transition-phase2.json`

### 7.3 Monica Rambeau / The Marvels alternate universe — COMPLETE

Destination continuity:

- `continuity-the-marvels-alternate-xmen-context`
- label is deliberately descriptive: alternate X-Men-linked universe
- no Earth number
- not equated with legacy `continuity-fox-x-men`
- not equated with Avengers: Doomsday returning-X-Men context

First-class event:

- `event-the-marvels-monica-alternate-universe-arrival`
- Earth-616 -> descriptive alternate universe
- mechanism `unknown`
- occurrence: The Marvels post-credit
- traveler: `entity-x-06c4fa169e` (Monica Rambeau)

Binary and Beast are destination encounters, not modeled as travelers.

This transition intentionally creates **no new work pair/reason** because there is no independently supported second-work endpoint for the crossing.

The existing The Marvels -> Doomsday relation remains conservative/uncertain and is not promoted by this transition.

Audit record:

- `data/content_audit/applied/2026-08-28-the-marvels-monica-transition-phase2.json`

## 6. Current boundary — Multiverse of Madness Earth-838 traversal

This is the most recent implementation batch.

### Facts now present and GREEN

Source:

- `d23-mom-earth838-travel-2024`
- D23/Disney source states Doctor Strange and America Chavez accidentally teleport to Earth-838 and identifies the source-side Strange as `616 Steven Strange`.

Continuity:

- `continuity-earth-838`
- `universe`
- `confirmed`
- `source_verified`
- kept separate from legacy X-Men world groups.

Event:

- `event-mom-doctor-strange-earth838-arrival`

Occurrence:

- `event-occurrence-mom-doctor-strange-earth838-arrival`
- work: `doctor-strange-in-the-multiverse-of-madness-2022`
- `occurrence_kind=depicted`

Transition:

- `continuity-earth-616` -> `continuity-earth-838`
- `transition_kind=unknown`
- direction confirmed

Participant:

- `transition-participant-mom-doctor-strange-earth838`
- entity `entity-x-c8ead423cc`
- role `traveler`

America Chavez is represented by the separate canonical entity `entity-x-0ba895cd8f`, a source-verified onscreen appearance, and the confirmed traveler participant `transition-participant-mom-america-chavez-earth838`. This is a co-traveler addition to the existing event, not a new transition or a new work pair; her unsupported origin and variant continuity remain unasserted.

### Important negative contract

This Earth-838 transition must **not**:

- turn the existing NWH -> MoM fallout relation into a physical crossing relation;
- manufacture a new work-pair reason from a single-work traversal;
- equate Earth-838 with `continuity-fox-x-men`;
- equate Earth-838 Black Bolt with the Inhumans-series individual.

The Earth-838 tests, including the America Chavez participant audit, are GREEN in the current local run (165 tests overall, including the review-patch workflow branch guard and malformed-CSV regression).

### Applied bookkeeping — complete

The canonical facts, evidence, and review history are present, and both bounded batches have applied-patch records:

- `data/content_audit/applied/2026-08-28-mom-earth838-transition-phase2.json`
- `data/content_audit/applied/2026-08-28-mom-america-earth838-participant-phase2.json`

The first record covers the five original Earth-838 facts and their existing reviews. The second records the America Chavez appearance/participant addition plus the rechecks that remove the obsolete deferred wording. Neither batch retires a work relation or creates a work-pair reason.

Suggested patch-record shape: follow nearby files in `data/content_audit/applied/`, especially the Monica/Vulture/Venom Phase 2 records. Record that no work relation is retired and no work reason is expected from this single-work traversal.

## 7. After Earth-838 and America Chavez audit

The approved Task 7 order from the reconciled handoff was:

1. Venom round trip — done;
2. Vulture transfer — done;
3. Monica transfer — done;
4. Multiverse of Madness traversals — Earth-838 and America Chavez participant audit done; no additional named traversal has yet met the separately bounded migration threshold;
5. Deadpool & Wolverine TVA / multiverse transfers — Wade's Earth-10005 -> TVA transfer is now modeled; later exact variant destinations remain unmodeled.

Do not mechanically create every dimension jump in MoM. For each candidate require:

- precise source/destination context supported by evidence;
- identified traveler participant;
- containing/depiction work clearly separated from causal/background works;
- no invented universe identity or Earth number;
- RED contract first;
- evidence + review history;
- conservative work-reason behavior.

If no additional MoM traversal meets that standard, document the no-go/boundary and proceed to Deadpool & Wolverine.

For Deadpool & Wolverine, existing registered evidence includes:

- `d23-deadpool-wolverine-tva-2024`
- `deadpool-wolverine-screenplay-2024`

Existing semantics already distinguish:

- TVA institutional connection from a sequel relation;
- Wade's home timeline from Earth-616/Sacred Timeline contexts where the source does so;
- the Logan-death story premise from exact identity of the film's Wolverine variant.

Do not promote old Blade/Elektra/Human Torch legacy relations to exact old-film timeline identity without stronger evidence; current audits deliberately keep those return continuities uncertain.

### Deadpool & Wolverine bounded batch — complete for the identified TVA transfer

The current bounded batch records:

- `continuity-earth-10005` as the explicitly labeled source universe;
- `continuity-tva-outside-timeline` as a descriptive TVA context, not a numbered universe;
- `event-dw-wade-tva-recruitment` and its depicted occurrence in `deadpool-wolverine-2024`;
- Wade Wilson (`entity-x-06b270750e`) as the confirmed traveler;
- `tva_transfer` direction from Earth-10005 to the TVA context.

Audit record:

- `data/content_audit/applied/2026-08-28-deadpool-wade-tva-transfer-phase2.json`

This batch creates no work relation or work-pair reason. The later TempPad jumps to individually distinct Wolverine variants are intentionally deferred because the available source does not provide a single stable destination continuity for a conservative first-class row.

## 8. Tests most relevant to current Phase 2 work

Read these before changing transition semantics:

- `tests/library_v5/test_phase2_transition_edge_reasons.py`
- `tests/library_v5/test_phase2_pr9_reconciliation.py`
- `tests/library_v5/test_phase2_thunderbolts_f4_transition.py`
- `tests/library_v5/test_phase2_nwh_legacy_spider_transitions.py`
- `tests/library_v5/test_phase2_venom_round_trip_transitions.py`
- `tests/library_v5/test_phase2_venom_proxy_retirement.py`
- `tests/library_v5/test_phase2_vulture_transfer_transition.py`
- `tests/library_v5/test_phase2_the_marvels_monica_transition.py`
- `tests/library_v5/test_phase2_mom_earth838_transition.py`
- `tests/library_v5/test_phase2_mom_america_participant.py`
- `tests/library_v5/test_phase2_deadpool_wade_tva_transfer.py`
- `tests/library_v5/test_apply_review_workflow.py`
- `tests/library_v5/test_audit.py` (strict CSV shape regression)
- `tests/library_v5/test_db_export_parity.py`

## 9. Verification before claiming completion

Run at least:

```bash
python -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
python -m scripts.library_v5.build --repo-root .
```

Then require the GitHub Actions workflow to pass before declaring a batch complete.

At the `ad9796b3...` checkpoint the expected observed summary was:

```text
161/161 tests PASS
audit issues = 0
review integrity issues = 0
FK rows = 0
integrity = ok
work_edges_all = 361
work_pair_reasons = 569
prewatch_edges = 199
story paths = 83/83
events = 8
transitions = 8
transition participants = 8
```

A documentation-only applied-patch addition should not change these semantic counts.

## 10. User intent / operating preference

The user wants the DB redesign to prevent bad arrows and accidental semantic fan-out in the public Marvel flowchart. The key real-world complaints that motivated the model include wrong Secret Wars/Doomsday arrows, appearance-only relations, duplicate/incorrect connections, and uncertain universe identity.

Bias toward **fewer, better-supported relations** rather than maximizing connectivity.

When the user says `進めて`, continue autonomously under `AGENTS.md` without asking routine questions. Report meaningful RED/GREEN findings and semantic boundaries in Japanese.

## 11. Separate normalized release/status subproject — Task 6 audit

The normalized `releases` / `production_status_assertions` work is a separately approved subproject recorded in:

- plan: `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md`;
- review: `docs/superpowers/reviews/2026-08-28-marvel-library-db-v1-releases-production-status-review.md`.

It was not a continuation of the already completed Events & Multiverse Task 7/8 audit. The subproject was subsequently merged as PR #11; it also does not imply evidence-backed promotion of the seed rows.

Task 6 was finally verified on `codex/db-v1-releases-status` at HEAD `dd56f321eb58569be1b6f386f4421cd2f10235bf` (`test: normalize graph fixture newlines for compatibility`), against fresh `origin/main=2410ea482d9fe6c9063a23b80b9b766e2bb9daac` (the merge base is the same). The exact bundled-Python full suite ran `195` tests with exit code `0`; the ordinary build exited `0` with `audit_issue_count=0`, content-audit/review-integrity issues `0`, SQLite foreign-key rows `0`, and `integrity_check=ok`. The final test-only fix normalizes CRLF/LF graph fixture bytes before comparison and adds one cross-platform regression test; it does not change production implementation, canonical data, or graph policy.

The normalized migration contains `131` primary release rows, `7` separate Japanese-date release rows, and `131` production-status snapshot rows for `131` works. All `269` release/status facts remain `legacy_seed`; no evidence or review rows were added. Evidence-backed promotion is a later separately approved audit batch. The DB schema version is `1.2-normalized-releases-status`, the logical fingerprint is `80f345416dd37ea81dcc9a89b128020132440a9538506820764382d6b20c6825`, and legacy graph compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, `prewatch_edges=199`, story paths `83/83`.

The release/status public views join only to `works` and do not feed graph derivation. The HTML DB-export milestone was later completed and merged as PR #12, with the committed `data/derived/flowchart.json` artifact repaired by PR #13 after the first public Pages check found a 404. The next boundary is (a) a separately planned evidence-promotion audit for a small subset of these legacy seeds or (b) one later normalized domain (`credits`, `entity_aliases`, `entity_memberships`, or `entity_possessions`); do not begin either without selecting a bounded plan and RED contract.
