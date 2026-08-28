# Codex handoff — Marvel Library DB v1 Phase 2 (2026-08-28)

This is the current execution handoff for Codex. Read `AGENTS.md` first; its rules are persistent and mandatory.

## 0. Start here

Repository:

- `kamochama/marvel-flowchart-jp`

Forward branch:

- `library-v5-phase2-db6`

Draft PR:

- PR #10: `WIP: Marvel Library DB v1 Phase 2 events & multiverse`
- base: `main`
- head: `library-v5-phase2-db6`
- draft: true
- merged: false

Production `main` checkpoint:

- `3af097b72c174077c83d7091f79222a72fc7134f`

**Do not merge PR #10 or change/publish `main` without explicit user approval.**

At handoff preparation time, the last implementation checkpoint was:

- `ad9796b3a1833d49e044a4eef220ca9d49c3553d`
- message: `audit: record Earth-838 transition reviews`
- GitHub Actions run #251: SUCCESS

Then documentation-only Codex setup began:

- `e2977fec4924cd241f16513add96d71b93fc58dd`
- message: `docs: add Codex project instructions`
- adds `AGENTS.md`

This handoff itself is a later documentation-only commit, so **always fetch the fresh remote HEAD before doing anything**. Do not reset the branch back to the implementation checkpoint merely because the SHA in this file is older than fresh HEAD.

Suggested local startup:

```bash
git status
git branch --show-current
git fetch origin
git checkout library-v5-phase2-db6
git pull --ff-only origin library-v5-phase2-db6
git log -5 --oneline
```

If the working tree is not clean or remote HEAD differs unexpectedly, reconcile first; do not discard user/local changes blindly.

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

## 3. Current verified baseline

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

America Chavez is explicitly acknowledged in notes/source as a co-traveler, but **no America Chavez canonical entity/participant was created in this batch**. Audit her separately if needed; do not invent/merge identity casually.

### Important negative contract

This Earth-838 transition must **not**:

- turn the existing NWH -> MoM fallout relation into a physical crossing relation;
- manufacture a new work-pair reason from a single-work traversal;
- equate Earth-838 with `continuity-fox-x-men`;
- equate Earth-838 Black Bolt with the Inhumans-series individual.

All five Earth-838 tests are GREEN at run #251.

### Remaining bookkeeping — DO THIS FIRST

The canonical facts, evidence, and five `created_verified` reviews exist and are GREEN, but the corresponding applied-patch file was still absent when this handoff was prepared.

Confirmed missing path:

- `data/content_audit/applied/2026-08-28-mom-earth838-transition-phase2.json`

First Codex action after fresh-HEAD reconciliation:

1. Confirm that this file is still absent at fresh HEAD.
2. If absent, add a bookkeeping-only applied patch record for the five created verified facts:
   - `continuity-earth-838`
   - `event-mom-doctor-strange-earth838-arrival`
   - `event-occurrence-mom-doctor-strange-earth838-arrival`
   - transition `event-mom-doctor-strange-earth838-arrival`
   - `transition-participant-mom-doctor-strange-earth838`
3. Reference the five already-existing review IDs:
   - `review-2026-08-28-mom-earth838-continuity`
   - `review-2026-08-28-mom-strange-earth838-event`
   - `review-2026-08-28-mom-strange-earth838-occurrence`
   - `review-2026-08-28-mom-strange-earth838-transition`
   - `review-2026-08-28-mom-strange-earth838-participant`
4. Do **not** alter canonical CSV rows as part of this bookkeeping commit.
5. Run full tests / CI and verify the semantic baseline remains unchanged.

Suggested patch-record shape: follow nearby files in `data/content_audit/applied/`, especially the Monica/Vulture/Venom Phase 2 records. Record that no work relation is retired and no work reason is expected from this single-work traversal.

## 7. After Earth-838 bookkeeping

The approved Task 7 order from the reconciled handoff was:

1. Venom round trip — done;
2. Vulture transfer — done;
3. Monica transfer — done;
4. Multiverse of Madness traversals — Earth-838 sub-batch done; inspect whether any additional traversal deserves a separately bounded migration;
5. Deadpool & Wolverine TVA / multiverse transfers — not started as first-class transitions.

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
