# Codex master roadmap — Marvel Library DB v1 to production main (2026-08-28)

This file is the long-range execution roadmap for Codex and other coding agents. It complements, rather than replaces:

- `AGENTS.md` — persistent safety and development rules;
- `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md` — exact current execution boundary;
- `docs/superpowers/plans/2026-08-27-marvel-library-db-v1-phase2-events-multiverse.md` — approved current implementation plan;
- `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` — broader DB v1 architecture and later-phase design.

If this roadmap conflicts with a newer explicit user instruction, the newer user instruction wins. If a SHA becomes stale, reconcile against fresh remote HEAD; never reset implementation to an older documentation checkpoint.

> **Current semantic production note (2026-09-02):** The historical PR #10/PR #11 gate described below has completed. PR #10 (Events & Multiverse), PR #11 (releases/status normalization), PR #12 (HTML DB export), PR #13 (Pages artifact fix), PR #21 (mobile touch-target contract), PR #22 (X-Men '97 release/status evidence promotion batch005), PR #26 (VisionQuest production-status evidence promotion batch006), PR #28 (Avengers: Doomsday release/status evidence promotion batch007), PR #30 (full release/status evidence audit), PR #32 (HTML design/operation debugging), and PR #38 (all-work browser selection audit) are merged into `main`; the latest semantic baseline is `fb715e87d5290b73e0ff86139d2554df32fc4a2d`. Later documentation-only commits do not change code/data. The post-merge baseline and the next separately bounded work are recorded in §13.

> **Integrated audit note (2026-09-02):** PR #40 (browser interaction state audit) is also merged into `main` at `04ff92b633f4da5756f58c96de7b321dac4bb02c`; it adds representative PC interaction coverage without changing semantic code or canonical data.

---

## 1. End goal

The intended final architecture is:

```text
Git-auditable canonical facts
        ↓
validate / compile
        ↓
Marvel SQLite database
        ↓
versioned SQL views + deterministic derivation
        ↓
static JSON / graph products / reports
        ↓
static GitHub Pages HTML viewer
```

`data/library/` remains the human-auditable canonical source of truth. SQLite is generated query state, not an editable source of truth. The public flowchart is ultimately a downstream view of the library rather than a separate place where Marvel facts live.

Production `main` is therefore **not permanently frozen**. It is the eventual integration target for completed, reviewed work. During development, however, do not modify or merge `main` without explicit user authorization.

---

## 2. Important terminology: two different phase vocabularies exist

Historical documents use overlapping phase names. Do not reinterpret or rename them silently.

### Current execution-plan vocabulary

`docs/superpowers/plans/2026-08-27-marvel-library-db-v1-phase2-events-multiverse.md` calls the current branch work **Phase 2 — Events & Multiverse**. Its Tasks 1–8 cover:

1. event/transition canonical schema;
2. SQLite compilation;
3. public event/multiverse views;
4. conservative transition-derived work reasons;
5. Thunderbolts* / Fantastic Four ship pilot;
6. No Way Home Raimi/Webb transitions;
7. high-confidence multiverse migration batches;
8. Phase 2 completion audit.

### Broader DB-v1 design vocabulary

`docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` uses a broader multi-phase roadmap:

- Design Phase 1 — DB compiler without semantic rewrite;
- Design Phase 2 — normalized canonical domain tables;
- Design Phase 3 — multiverse audit decomposition;
- Design Phase 4 — HTML switches to DB exports;
- Design Phase 5 — broader 131-work content audit.

The current Events & Multiverse execution work spans part of the broader normalized-table and multiverse-decomposition roadmap. When reporting status, name the plan/task explicitly rather than saying only “Phase 2”.

---

## 3. Historical branch and integration policy

Repository:

- `kamochama/marvel-flowchart-jp`

Current forward development branch:

- `library-v5-phase2-db6`

Draft integration PR:

- PR #10
- base: `main`
- head: `library-v5-phase2-db6`
- intentionally draft while development continues.

Historical PR #9 / `library-v5-canonical-freeze` was already reconciled into this forward history. Do not merge it again.

The branch and PR #10 labels in this section describe the pre-integration gate and are retained for historical traceability; the current production baseline and later integrations are summarized in §13.

### Main policy (historical PR #10 gate)

During development:

- do not commit directly to `main`;
- do not merge PR #10;
- do not rebase/force-push the forward history;
- do not publish production changes merely because a subtask is GREEN.

At the **final integration gate** for the current PR:

1. finish the approved execution plan;
2. complete the Phase 2 review document and all full-CI checks;
3. audit PR #10 as a whole;
4. present the final integration state to the user;
5. obtain explicit user authorization to merge;
6. merge PR #10 into `main` through the normal PR path rather than rewriting history;
7. verify the resulting `main` HEAD, CI, generated products, and GitHub Pages/public-site behavior;
8. only then treat `main` as the new production baseline.

If authorization has not been given, stop at the integration gate. “Do not touch main” means **do not touch it during development without authorization**, not “main must never be updated”.

---

## 4. Historical execution boundary

The detailed current state is in `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`.

Latest implementation checkpoint before Codex documentation commits (historical):

- `ad9796b3a1833d49e044a4eef220ca9d49c3553d`
- GitHub Actions run #251: SUCCESS
- 161 / 161 unit tests PASS
- audit issues: 0
- review integrity issues: 0
- FK rows: 0
- SQLite integrity: `ok`
- `work_edges_all`: 361
- `work_pair_reasons`: 569
- events / occurrences / multiverse transitions / transition participants: 8 / 8 / 8 / 8
- prewatch edges: 199
- story paths: 83 / 83

Documentation-only Codex setup commits followed. Always use fresh remote HEAD rather than resetting to the implementation SHA.

### First action (historical)

The Doctor Strange / Earth-838 first-class transition is implemented, evidenced, reviewed, tested, and GREEN. The original transition record and the follow-up America Chavez participant audit now both have applied-patch bookkeeping records.

Confirm these paths exist at fresh HEAD:

- `data/content_audit/applied/2026-08-28-mom-earth838-transition-phase2.json`
- `data/content_audit/applied/2026-08-28-mom-america-earth838-participant-phase2.json`

If either path is absent, restore the corresponding bookkeeping-only applied patch record following the Monica/Vulture/Venom examples. Do not alter canonical semantic rows merely to create a record. Then rerun full CI.

---

## 5. Finish current Events & Multiverse Task 7

Task 7 must proceed one bounded, evidence-backed migration at a time. Do not batch-create multiverse facts.

Already completed:

1. Eddie Brock / Venom round trip;
2. Adrian Toomes / Vulture transfer;
3. Monica Rambeau / The Marvels alternate-universe arrival;
4. Doctor Strange Earth-616 -> Earth-838 traversal and America Chavez participant audit.

### 5.1 Multiverse of Madness residual audit

After the Earth-838 and America Chavez audit, verify whether any additional `Doctor Strange in the Multiverse of Madness` traversal deserves a separately modeled first-class transition.

Requirements for each additional candidate:

- source and destination context are supported without invented IDs/Earth numbers;
- traveler identity is supported;
- depiction work is clear;
- mechanism is not guessed;
- RED test first;
- qualifying evidence;
- created/changed review history;
- conservative work-reason behavior;
- full CI before moving to the next candidate.

Do **not** mechanically model every visual dimension jump.

The current residual audit found no additional named traversal that clears the evidence/utility threshold; preserve this no-go boundary unless new qualifying evidence is found, and proceed rather than inventing facts.

### 5.2 Deadpool & Wolverine TVA / multiverse transfers

After MoM residual audit, proceed to high-confidence `Deadpool & Wolverine` transfers. The initial bounded transfer is now implemented: Wade Wilson's explicitly labeled Earth-10005 home setting to the TVA/outside-timeline context.

Existing evidence to inspect first includes:

- `d23-deadpool-wolverine-tva-2024`;
- `deadpool-wolverine-screenplay-2024`.

Preserve established distinctions:

- TVA institutional connection is not automatically a sequel relation;
- Wade's home timeline is not casually collapsed into Earth-616;
- Logan's death is a story premise, not proof that the film's Wolverine is the same individual as Logan (2017);
- Blade / Elektra / Human Torch legacy returns currently have uncertain exact old-film continuity and must not be upgraded without stronger evidence.

Model only specific transfers whose direction, traveler identity, depiction, and continuity context are source-supported.

The current Deadpool & Wolverine batch intentionally stops before the later TempPad jumps to individually distinct Wolverine variants: the available screenplay does not provide one stable destination continuity suitable for a conservative first-class row. Its applied record is `data/content_audit/applied/2026-08-28-deadpool-wade-tva-transfer-phase2.json`; no work relation or work-pair reason is added.

---

## 6. Finish current execution plan — Task 8 completion audit

After Task 7 candidates are either migrated or explicitly deferred, execute **Task 8 — Phase 2 completion audit** from the approved plan.

Create/update:

- `docs/superpowers/reviews/2026-08-27-marvel-library-db-v1-phase2-events-multiverse-review.md`

Required final audit includes:

- all tests PASS;
- audit issue count 0;
- review integrity issues 0;
- ordinary build does not mutate canonical/review inputs;
- SQLite FK check empty;
- SQLite integrity `ok`;
- logical DB fingerprint deterministic;
- event and crossing views deterministic;
- graph exporter deterministic;
- every retired proxy has replacement semantics and review history;
- no transition inferred from actor reuse alone;
- no variant treated as the original individual without evidence;
- migrated and deferred multiverse cases explicitly listed;
- PR/main state clearly recorded.

The approved current plan says to stop before releases/credits/memberships/possessions/final-HTML work unless separately approved. Therefore **do not silently start the next architecture phase after Task 8**.

---

## 7. PR #10 final review and production integration gate (historical)

After Task 8 is GREEN:

1. fresh-fetch `main` and PR #10 heads;
2. reconcile if `main` advanced externally;
3. inspect the full PR diff, not only recent commits;
4. ensure no accidental generated/binary/canonical churn;
5. verify branch CI from fresh HEAD;
6. summarize semantic changes, deferred cases, graph compatibility, audit status, and deployment implications;
7. ask the user for **explicit final merge authorization**.

The full-PR audit also found that the review-patch workflow still targeted the former `library-v5-canonical-freeze` branch. The current local follow-up commit retargets checkout and push to `library-v5-phase2-db6`, adds a regression test, and adds strict CSV-shape rejection so pending audited patches can run safely on the forward line.

### If user authorizes merge

- merge PR #10 into `main` through the normal PR path;
- do not force-update `main`;
- verify fresh `main` HEAD;
- run/confirm `main` CI;
- verify public GitHub Pages still loads and existing viewer behavior is not broken;
- verify generated/public artifacts expected at this stage;
- record the new production baseline in a handoff/review document.

### If user does not authorize merge

Leave PR #10 draft/open or otherwise in the user-requested state and stop. Do not substitute your own release decision.

This conditional describes the historical gate. It has been superseded by the completed production integration recorded in §13.

---

## 8. Broader DB-v1 roadmap after current PR

The DB-v1 design contains later work that is **architecturally intended but not automatically authorized by completion of current Task 8**. Each later stage should get its own explicit plan/review boundary before implementation.

### 8.1 Complete normalized canonical domains

The broader design calls for normalized tables beyond the event/multiverse subset. Releases and production-status assertions are now implemented; remaining domains include:

- `credits`;
- `entity_aliases`;
- `entity_memberships`;
- `entity_possessions`.

Some event/transition tables from the broader design are already implemented by the current branch. Do not recreate them under a second schema.

Purpose:

- separate Japanese/US/streaming/re-release dates;
- retain historical production status assertions rather than overwriting them;
- store general real-world credits without inventing character identity;
- separate aliases from identity entities;
- represent organization memberships without manufacturing work edges;
- represent artifact possession/transfer in its proper semantic domain.

Before implementing these domains, produce/obtain a separately approved execution plan.

### 8.2 Broader multiverse decomposition

Continue decomposing legacy multiverse work-relations into first-class primitive facts where the evidence warrants it.

Rules remain:

- work relations are retained when they express independent sequel/lead-in/editorial/story semantics;
- pure crossing proxies may be retired only after independent replacement parity;
- no actor reuse -> identity inference;
- no invented Earth numbers;
- uncertain legacy return identity stays uncertain.

### 8.3 HTML switches to DB exports

This is a major later milestone from the DB-v1 design.

Required direction:

- generate node payload from `v_flowchart_nodes`;
- generate edge/reason payload from `v_flowchart_edge_candidates` plus view policy;
- remove independent/manual Marvel fact arrays from `index.html`;
- keep layout/UI policy under `views/flowchart/` rather than canonical data;
- preserve deterministic JSON generation;
- compare selected-path and prewatch behavior with the existing implementation;
- keep static GitHub Pages deployment; do not introduce a live production DB server merely for DB v1.

Performance requirement:

- preserve the user's Pixel 6/mobile responsiveness standard;
- one-finger chart movement and whole-chart zoom behavior must not regress;
- avoid payload/runtime changes that make the previously optimized mobile chart sluggish.

This HTML migration was later separately approved and completed through `docs/superpowers/plans/2026-08-29-marvel-library-db-v1-html-db-export.md`, then merged as PR #12 with the Pages artifact repair in PR #13. Any further viewer/data-source changes require their own bounded plan.

### 8.4 Broader 131-work content audit

After the richer semantic model and DB-export path are stable, continue the full audiovisual-work audit.

Bias toward:

- fewer, better-supported edges;
- evidence-backed identity/continuity;
- correct semantic homes;
- explicit uncertainty instead of guessed connectivity.

Newly audited facts should enter the correct domain table rather than creating ad-hoc flowchart edges.

---

## 9. Public-site / release requirements

The public site is static GitHub Pages. DB v1 does not require SQLite in the browser or a live database server.

For any eventual release that changes the viewer:

- verify desktop behavior;
- verify mobile behavior, with Pixel-6-level performance as an explicit regression concern;
- verify selected paths/prewatch plans;
- verify dimming/arrow behavior and relation explanations;
- verify Pages from the production `main` result.

When creating the public distribution ZIP, preserve the established root structure exactly:

```text
index.html
README.md
AUDIT.md
AUDIT.json
preview.png
.nojekyll
```

Do not add version-named duplicate HTML files inside the ZIP.

---

## 10. What must never be inferred merely to advance the roadmap

Do not trade correctness for roadmap completion.

Never invent or assume:

- an Earth number absent from evidence;
- same fictional identity from the same actor;
- exact old-film continuity for a legacy return without proof;
- chronology from the work containing a multiverse crossing;
- traveler presence aboard a vehicle without evidence;
- a transport mechanism when unknown;
- an edge merely because two works share a continuity;
- that every first-class event must create a work-to-work edge.

A documented defer/no-go is preferable to a false canonical fact.

---

## 11. Completion ladder

Use this ladder when deciding what “done” means:

### A. Batch complete

- RED contract existed;
- implementation/evidence/reviews applied;
- applied-patch record added when required;
- batch tests GREEN;
- full CI GREEN.

### B. Current Events & Multiverse execution plan complete (historical gate)

- all approved Task 7 candidates migrated or explicitly deferred;
- Task 8 final review written;
- full branch CI GREEN;
- PR #10 audited;
- **stop at integration gate**.

### C. Current work integrated to production

- user explicitly approved merge;
- PR #10 and its reviewed follow-up integrations merged to `main`;
- fresh main CI GREEN;
- Pages/public behavior verified;
- production baseline documented.

### D. DB v1 architecture complete

Only after later separately approved work also completes:

- normalized semantic domains implemented as needed;
- multiverse decomposition mature;
- HTML consumes DB-derived exports instead of independent Marvel facts;
- broader content audit progresses through the richer model;
- public viewer remains performant and deterministic.

Do not collapse B, C, and D into one milestone. Finishing the current Phase 2 PR does not automatically authorize later architecture phases, and finishing a feature branch does not automatically authorize production merge.

## 12. Separate normalized release/status boundary — Task 6 audit (historical, 2026-08-29)

The approved plan `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md` defines a separate normalized release/status subproject after the Events & Multiverse execution boundary. Its Task 6 review is recorded in `docs/superpowers/reviews/2026-08-28-marvel-library-db-v1-releases-production-status-review.md`.

Fresh verification was run on branch `codex/db-v1-releases-status` at final HEAD `dd56f321eb58569be1b6f386f4421cd2f10235bf` (`test: normalize graph fixture newlines for compatibility`), with fresh `origin/main=2410ea482d9fe6c9063a23b80b9b766e2bb9daac` as the integration base. The bundled-Python full suite ran `195` tests and exited `0`; the ordinary build exited `0`; audit issues, content-audit/review-integrity issues, and SQLite foreign-key issues were all `0`, while SQLite `integrity_check` was `ok`. The final test-only fix normalizes CRLF/LF graph fixture bytes before comparison and adds one cross-platform regression test; production implementation, canonical data, and graph policy are unchanged.

The normalized migration observes `131` works, `138` releases (`131` primary + `7` JP), and `131` production-status assertions. All `269` new release/status facts remain `legacy_seed`; no evidence-backed promotion is claimed. The DB schema is `1.2-normalized-releases-status` with logical fingerprint `80f345416dd37ea81dcc9a89b128020132440a9538506820764382d6b20c6825`. The legacy compatibility outputs remain unchanged: `work_edges_all=361`, `work_pair_reasons=569`, `prewatch_edges=199`, and `83/83` story paths reproduced. Strict CSV shape scan covered `46` files with `0` malformed rows, and protected canonical/review inputs were unchanged.

This boundary did not modify `index.html`, the existing graph policy, or the semantic status of the completed Events & Multiverse plan. It was merged as PR #11; evidence-backed promotion of the seed rows and the remaining normalized domains (credits, aliases, memberships, possessions) remain separately approved future work.

### 12.1 Evidence-promotion follow-up (batch005, 2026-08-30)

PR #22 promoted exactly two existing facts: the X-Men '97 Season 2 primary streaming release and its released-status snapshot. Each has a `primary` evidence row and an auditable `legacy_seed -> source_verified` review transition. The Japanese release row remains `legacy_seed` with a blank date, and no graph edge or work-pair reason is derived from these metadata facts. The applied record is `data/content_audit/applied/2026-08-30-release-status-evidence-promotion-batch005.json`.

After batch005, the normalized tables contain 138 releases (6 `source_verified`, 132 `legacy_seed`) and 131 production-status assertions (2 `source_verified`, 129 `legacy_seed`). Remaining seeds require separate evidence-backed batches; do not infer territory, Japanese dates, production milestones, or graph connectivity from the normalized metadata.

### 12.2 Evidence-promotion follow-up (batch006, 2026-08-30)

PR #26 promoted the existing VisionQuest announced-status snapshot with one primary Marvel Television evidence row and one auditable `legacy_seed -> source_verified` review transition. The announced status, `asserted_at=2026-08-28`, certainty, unknown territory boundary, and no-production-milestone rule remain unchanged. No Japanese date or graph fact was inferred. The applied record is `data/content_audit/applied/2026-08-30-release-status-evidence-promotion-batch006.json`.

After batch006, the normalized tables contain 138 releases (6 `source_verified`, 132 `legacy_seed`) and 131 production-status assertions (3 `source_verified`, 128 `legacy_seed`); sources/evidence/reviews are 44/112/87. Compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, prewatch edges `199`, and story paths `83/83`. Remaining seeds require separate evidence-backed batches.

### 12.3 Evidence-promotion follow-up (batch007, 2026-08-30)

PR #28 promoted the existing Avengers: Doomsday announced-status snapshot with one primary Marvel Japan evidence row and one auditable `legacy_seed -> source_verified` review transition. The announced status, `asserted_at=2026-08-28`, certainty, separate JP release row with blank date, and no-production-milestone rule remain unchanged. No territory, Japanese date, or graph fact was inferred. The applied record is `data/content_audit/applied/2026-08-30-production-status-evidence-promotion-batch007.json`.

After batch007, the normalized tables contain 138 releases (6 `source_verified`, 132 `legacy_seed`) and 131 production-status assertions (4 `source_verified`, 127 `legacy_seed`); sources/evidence/reviews are 44/113/88. Compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, prewatch edges `199`, and story paths `83/83`. Remaining seeds require separate evidence-backed batches.

## 13. Post-integration baseline and next execution boundary (2026-09-02)

PR #40 is integrated as the representative browser interaction-state audit. Its six real desktop cases cover same-work re-click clear, background clear, drag preservation, overview↔chronology repaint, overview↔release repaint, and right-panel works↔links preservation. The audit runs in a separate dependent CI job and observes real pointer events and DOM state without extending the overview selection oracle.

The latest semantic production baseline is `main` at `fb715e87d5290b73e0ff86139d2554df32fc4a2d`, the merge commit for PR #38. The static Pages viewer still loads the committed DB-derived `data/derived/flowchart.json`; release/status metadata remains outside graph derivation.

PR #30 completed the strict all-fact release/status evidence audit and merged promotion batches008–015. The normalized tables contain `138` releases (`14` `source_verified`, `124` `legacy_seed`) and `131` production-status assertions (`13` `source_verified`, `118` `legacy_seed`). The full disposition ledger covers all `269` facts: `27` promoted, `240` deferred, and `2` conflicts retained as seeds. Sources/evidence/reviews are `49/130/105`. Promoted facts preserve territory, precision, announced/released semantics, and snapshot dates; no graph edge, work-pair reason, production milestone, or Earth identity is inferred.

Fresh verification on PR #30 head (GitHub Actions run #285) passed `305` library-v5 tests. PR #32 then passed its required check (`1 / 1`) with the expanded `318`-test suite. The post-merge build and audit/review checks report zero issues, SQLite foreign-key rows are `0`, `integrity_check=ok`, and compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, prewatch edges `199`, story paths `83/83`. Applied records and the deterministic inventory are recorded under `data/content_audit/applied/` and `data/content_audit/release_status_inventory.csv`.

The data-audit boundary and the HTML design/interaction debugging pass are complete. PR #32 records the official/curated provenance boundary, three tier semantics, chart-return navigation, route highlighting, and desktop/mobile smoke results; PR #38 adds the independent all-work selection oracle and real Chrome/CDP DOM exact-set audit for both public tiers, including its required CI job and hosted-runner cleanup handling. The public Pages URL was rechecked after the merge and returned HTTP `200`. Any subsequent viewer change requires its own plan, RED/UI regression contract, full verification, and an explicit merge boundary.

## 14. Chronology display contract boundary (2026-09-03)

The separately approved chronology display plan `docs/superpowers/plans/2026-09-02-marvel-library-chronology-display-contract.md` is complete through its Task 4 implementation and Task 5 local documentation handoff on branch `codex/chronology-publication-order-contract`. The implementation range is `10726ac..e141d3d`, ending at `e141d3da7f26eccea49d3d81a0f51d564f95d06b` (`test: strengthen chronology mode and canvas audits`). The Task 5 commit is documentation-only and records the review, handoff, and this roadmap boundary.

The chronology viewer now materializes stable edge IDs for all `74` display lines, separates display-only lines from traversable adjacency, and classifies selections by edge ID across five public modes: `complete`, `site-proposal`, `or`, `and`, and `path`. `previous1` remains an internal unit-only contract without a public scope control. PATH pair/ID inputs are mapped only at the existing SVG/Canvas render boundary to traversable chronology IDs; no new chronology search or BFS is introduced. SVG `data-chronology-edge-id` and Canvas `overlayChronologyEdgeId` produce equal materialized ID sets, categories, and chronology metadata. A fixed independent fixture makes the OR/AND and site-proposal incoming-tier checks distinguishable. These lines remain a display layer, not canonical relation facts.

Local evidence:

- full bundled-Python suite: `398` tests, `OK (skipped=3)`;
- ordinary build: exit `0`, audit/review/FK issues `0`, SQLite `integrity_check=ok`;
- graph compatibility: `361/569`, prewatch `199`, story paths `83/83`;
- real Chrome/CDP chronology audit: `7` cases, `failures=0`, duplicate IDs `0`, display-only highlighted `0`, SVG/Canvas ID/category/metadata parity failures `0`, all five display-only endpoint checks, and both overview↔chronology round trips true;
- `previous1` is explicitly unavailable/skipped because the export has no public scope control; no internal scope state was invoked;
- `chronology_assertions=0`, and canonical `data/library/` plus persistent `data/content_audit/reviews.csv` are unchanged.

The local `git fetch origin` freshness check failed with `.git/FETCH_HEAD: Permission denied`; the checkout was not reset or overwritten. Remote CI, complete branch review, merge into `main`, and Pages publication remain pending explicit approval. The release-order/publication-order plan `docs/superpowers/plans/2026-09-02-marvel-library-publication-order-display.md` is intentionally unexecuted and remains a separate future boundary; no release-order semantics are introduced here.

## 15. Publication-order display contract boundary (2026-09-03)

The separately approved plan `docs/superpowers/plans/2026-09-02-marvel-library-publication-order-display.md` is complete through Task 5 implementation and Task 6 local verification on branch `codex/publication-order-display-contract`. The implementation range is `5e159c4236ee03ede4c5175519bff468ff6beb1e..c5e24393904aec6ae50511813b61a300c2a572f1`; the Task 6 docs-only handoff is recorded in `docs/superpowers/reviews/2026-09-02-marvel-library-publication-order-display-review.md`, this roadmap section, and the corresponding handoff section.

Publication order is now a date-axis/card focus view. It renders all `131` works, preserves exact/month/year/undated-TBD precision without inventing a day, uses deterministic stable-sort-index then `work_id` tie-breaking, and puts TBD works in an explicit `Upcoming / date TBD` lane. The release SVG declares `data-relationship-edges="off"` and creates no `g.edge` or `g.chronology-edge`; relation/chronology lines are likewise prohibited from mobile synthetic Canvas overlays. Shared work selection and detail focus are preserved across overview, chronology, and release, but the release panel does not become a relation graph. The canonical export currently has `day=127 / month=2 / year=0 / none=2`, so the year-only browser case is a runtime fixture only.

Task 6 local evidence:

- bundled-Python full suite: `424` tests, `OK (skipped=4)`, exit `0`;
- ordinary build: exit `0`, audit issue `0`, content-audit issue `0`, SQLite FK rows `0`, `integrity_check=ok`, logical fingerprint/equivalence `39917ceee6af94e680acebdf7b570142f1a2995646aec1dd344ec3ed395b5b92`;
- graph/export compatibility: `131` nodes, `361` edges, `569` reasons, `42` character groups, prewatch `199`, story paths `83/83`;
- direct real Chrome/CDP runner: `cards=131`, `cases=21`, `failures=0`, `syntheticEdges=0`; SVG edges `0/0`, geometry failures `0`, mobile `390x844` nodeBoxes `131`, synthetic overlays `0`;
- wrapper: `cards=131, failures=0, syntheticEdges=0`; release↔overview and release↔chronology round trips all true;
- canonical `data/library/**`, persistent `data/content_audit/reviews.csv`, and derived SQLite/export inputs have no branch diff. Build-only outputs were inspected and removed as transient paths.

The normal-permission local `git fetch origin` freshness check first reported `.git/FETCH_HEAD: Permission denied`, but the authorized elevated retry succeeded. At this checkpoint `origin/main` was `5e159c4236ee03ede4c5175519bff468ff6beb1e` (containing the AGENTS.md `04ff92b...` baseline as an ancestor); no reset, overwrite, rebase, or force update was performed. This milestone is locally verified but not production-integrated. Remote CI, full branch review, public artifact/Pages checks, and explicit user approval remain the merge/publication gate. Do not merge, push, publish, or begin another semantic/viewer phase from this boundary without that approval.

## 16. Publication-order display — production baseline (2026-09-03)

PR #42 (`https://github.com/kamochama/marvel-flowchart-jp/pull/42`) integrated the publication-order display contract into `main` at merge commit `f4d4662383645eec714faf3b73d3fa2e0f2e2ded`. The required CI checks all passed, including the dedicated publication-order browser audit. Its real Chrome coverage reported `131` cards, `21` cases, `failures=0`, `syntheticEdges=0`; release/overview and release/chronology round trips were successful.

The GitHub Pages deployment for the merge commit completed with `status=built`, `public=true`, and `https_enforced=true`. The public URL is `https://kamochama.github.io/marvel-flowchart-jp/`, which returned HTTP `200`; the served HTML contains the release relationship-edge guard and release-card attributes. Canonical `data/library/**`, `data/content_audit/reviews.csv`, and derived SQLite/export inputs were unchanged by this milestone.

This is now the production viewer baseline. Any subsequent viewer or semantic change requires its own bounded plan, regression contract, full verification, and explicit merge boundary.

## 17. Variant fan-out audit — production baseline (2026-09-03)

PR #45 (`https://github.com/kamochama/marvel-flowchart-jp/pull/45`) integrated the bounded Deadpool & Wolverine variant fan-out audit into `main` at `040c2842a0bf4436ab43194be87cfaff03a283b9`. The source-backed model introduces `entity-x-dw-wolverine-variant-2024`, a confirmed `variant_of` relation to the original Logan/Wolverine entity, and a new source-verified Deadpool & Wolverine appearance. The pre-existing appearance is retained as `superseded` with an auditable review transition. The explicit Logan story relation remains; six unsupported shared-entity work-pair projections are removed, changing compatibility from `361/569` to `355/562`. Loki is intentionally not split because a qualifying identity/variant source is not yet registered.

Verification at this production boundary:

- bundled-Python full suite: `437` tests pass, `4` environment-gated skips;
- build/audit: audit issues `0`, content-audit issues `0`, SQLite FK rows `0`, `integrity_check=ok`;
- graph: `131` nodes, `355` edges, `562` reasons, prewatch `199`, story paths `83/83`;
- real Chrome/CDP: selection `131 × 2` with zero exact-set mismatches; interaction `6/6`; chronology `7` cases with zero failures; publication order `131` cards/`21` cases with zero failures and zero synthetic edges;
- GitHub Actions run `33734185633`: all five required jobs passed.

The implementation plan and review are `docs/superpowers/plans/2026-09-03-marvel-variant-fanout-audit.md` and `docs/superpowers/reviews/2026-09-03-marvel-variant-fanout-audit.md`. The official screenplay evidence distinguishes the recruited Wolverine from the exhumed Logan; no unsupported Earth, continuity, or TVA-transition semantics were added. Future source/relation batches require their own bounded plan, regression contract, evidence/review audit, and merge gate.

## 18. Relation evidence promotion wave001 — production baseline (2026-09-03)

PR #47 (`https://github.com/kamochama/marvel-flowchart-jp/pull/47`) integrated the first bounded relation-evidence promotion wave into `main` at `28941193ec2b5c3fb18a57b02ac3fbc2b2e376c9`. It promotes only the existing Thunderbolts* → Avengers: Doomsday lead-in and No Way Home → Brand New Day story-link relations. Existing relation IDs and directed pairs are preserved; each has exact work-relation evidence plus a `legacy_seed -> source_verified` review transition. No new source registry row, entity/appearance, release/status, event, transition, or chronology fact was added.

Verification at this boundary:

- bundled-Python full suite: `439` tests pass, `4` environment-gated skips;
- build/audit: audit and content-audit issues `0`, SQLite FK rows `0`, `integrity_check=ok`;
- relation table: `164` rows (`9` source_verified, `152` legacy_seed, `3` superseded); evidence `136`; reviews `110`;
- graph/export compatibility: `131` nodes, `355` edges, `562` reasons, prewatch `199`, story paths `83/83`;
- real Chrome/CDP selection, interaction, chronology, and publication-order audits all pass with zero failures/mismatches;
- GitHub Actions run `33743113994` passed all five required checks; Pages run `33743746234` succeeded and the public URL returned HTTP `200`.

The plan and review are `docs/superpowers/plans/2026-09-03-marvel-relation-evidence-promotion-wave001.md` and `docs/superpowers/reviews/2026-09-03-marvel-relation-evidence-promotion-wave001.md`. The next bounded source queue begins with the three VisionQuest-trilogy relations and X-Men '97 S1 → S2, subject to direct fact-level evidence and separate RED tests.

## 19. Relation evidence promotion wave002 — production baseline (2026-09-03)

PR #49 (`https://github.com/kamochama/marvel-flowchart-jp/pull/49`) integrated the second bounded relation-evidence promotion wave into `main` at `3e25c5b2671ccc29cf551aa51875ae8e48625e64`. It promotes four existing relations: `WandaVision -> Agatha All Along` (official spinoff/segue), the two existing `WandaVision/Agatha All Along -> VisionQuest` trilogy display links, and `X-Men '97 S1 -> S2` (official season continuation). The batch preserves relation IDs, directed pairs, relation kinds, and certainty values, adding only source registration where needed plus exact evidence and `legacy_seed -> source_verified` review transitions. No release/status, chronology, identity, multiverse-transition, or new work-pair fact was inferred. Across→Beyond remains deferred.

Verification at this boundary:

- bundled-Python full suite: `441` tests pass, `4` environment-gated skips;
- build/audit: audit and content-audit issues `0`, SQLite FK rows `0`, `integrity_check=ok`;
- relation table: `164` rows (`13` source_verified, `148` legacy_seed, `3` superseded); sources/evidence/reviews `50` / `140` / `114`;
- graph/export compatibility: `131` nodes, `355` edges, `562` reasons, prewatch `199`, story paths `83/83`;
- real Chrome/CDP selection `131 × 2`, interaction `6/6`, chronology `7` cases, and publication order `131` cards/`21` cases all pass with zero failures/mismatches and zero synthetic edges;
- GitHub Actions run `33745660110` passed all five required jobs after a transient hosted selection timeout was rerun; Pages run `33746647857` succeeded and the public URL returned HTTP `200`.

The plan and review are `docs/superpowers/plans/2026-09-03-marvel-relation-evidence-promotion-wave002.md` and `docs/superpowers/reviews/2026-09-03-marvel-relation-evidence-promotion-wave002.md`. Remaining legacy relation rows require their own source-specific evidence/review batches; this wave is not a claim that the entire relation queue is complete.
