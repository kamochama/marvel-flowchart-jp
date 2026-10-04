# Relation evidence promotion wave022

> Required execution method: superpowers:executing-plans; read-only independent source/diff review, exact-fact RED/GREEN, ordinary ChatGPT review, all seven CI jobs, normal PR integration and deployed-main verification.

## Approved scope

Promote only verification_status from legacy_seed to source_verified on these existing relations. Preserve IDs, endpoints, kind, scope, directness, continuity, certainty and full notes.

1. `work-relation-captain-america-the-first-avenger-2011-agent-carter-one-shot-2013-story-link`: story_link/story/indirect/same_or_intended/probable; `Peggy Carter continuation.` Disney+ Japanese work details explicitly place Peggy's SSR story after The First Avenger. Source: https://www.disneyplus.com/ja-jp/browse/entity-5e7f5aa1-b3ea-4cd3-983f-c5cda970fb0a . Do not add SHIELD membership, Zodiac events or exact chronology.
2. `work-relation-captain-america-civil-war-2016-black-widow-2021-aftermath`: aftermath/story/direct/same_or_intended/probable; `『ブラック・ウィドウ』本編は『シビル・ウォー』直後のナターシャを描く。` Marvel Studios Black Widow advance production brief, printed p.2, explicitly places Natasha on the heels of Civil War. Source: https://lumiere-a.akamaihd.net/v1/documents/black_widow_advance_updated_final_04-29-21_e1222ad3.pdf . Do not create Accords/Ross events or chronology facts.
3. `work-relation-avengers-endgame-2019-hawkeye-2021-aftermath`: aftermath/story/indirect/same_or_intended/probable; `ローニン期とナターシャ喪失を抱えるクリントの後日談。` Hawkeye production brief, printed p.2, explicitly identifies Endgame/Ronin history and Natasha's loss as Clint's emotional starting point. Source: https://lumiere-a.akamaihd.net/v1/documents/hawkeye_production_brief_final_11-04-21_b8718e9c.pdf . Do not create Ronin/death events or identity/chronology facts.

Add three official source registrations, three exact primary evidence rows and three legacy_seed -> source_verified review transitions. No viewer implementation or export-policy changes. Existing export policy may change recommendation metadata on these three supported pairs; explicitly inspect and report that effect rather than claiming byte-identical export. Preserve all graph endpoints and reason IDs.

## Execution

- [ ] Wait for Wave021 reviewed exact head to pass seven CI jobs and merge normally; fresh-check the resulting main and Pages. Start a new codex/ feature branch from that remote main, not from an unmerged forward head.
- [ ] Write an exact tuple/full-notes/source/evidence/review regression. Observe three failing legacy statuses before canonical writes.
- [ ] Apply the minimal four-table change, verify strict CSV shapes and per-file diff. Do not edit other semantic domains.
- [ ] Rebuild before full tests so committed derived provenance matches canonical statuses; regenerate connection/explicit inventories without pretending the structural index proves semantic completeness.
- [ ] Run full tests, two deterministic builds, canonical isolation, audit/content/review integrity, SQLite FK/integrity and diff checks.
- [ ] Independently compare the complete export, not just graph counts; explain any metadata difference and forbid unrelated node/edge/meaning changes.
- [ ] Obtain independent Luna full-diff review and ordinary ChatGPT review with base/head/full diff/results. Push/create/attach normal PR and require all seven CI jobs.
- [ ] Merge normally under standing authorization, verify main SHA/CI/Pages/HTTP 200 and deployed graph payload. Record integration without claiming whole-work audit complete.

## Research exclusions

Netflix Defenders showrunner announcements do not prove a Season 2 narrative endpoint. AoU -> WandaVision notes describing both characters' MCU origin need narrowing because Wanda debuted in Winter Soldier's post-credit scene. Neither enters this status-only batch. Unfinished source investigation remains open, not formal DEFER.

## Plan review

2026-10-04: Main agent read all three primary passages. Ordinary ChatGPT independently read the Disney+ details and both PDF texts and approved all three exact tuples/full notes as status-only promotions (12-second response). PDF text extraction succeeded; reviewer PDF screenshots failed, so no independent visual-layout claim is made. Implementation review remains a separate required gate.
