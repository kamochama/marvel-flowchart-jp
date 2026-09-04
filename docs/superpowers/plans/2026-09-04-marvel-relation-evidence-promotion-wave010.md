# Marvel Library v5 relation evidence promotion wave010 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote eleven existing work relations to `source_verified` using relation-specific official primary sources, without changing relation semantics or graph topology.

**Architecture:** Keep the existing relation rows and derived graph as the semantic contract. Register one official source, one primary evidence row, and one auditable `legacy_seed -> source_verified` review row per selected relation; regenerate deterministic exports only to carry verification metadata.

**Scope:** The independent Codex audit and ordinary-ChatGPT review agreed on eleven candidates. `work-relation-x-men-days-of-future-past-2014-x-men-apocalypse-2016-sequel` is explicitly deferred because the proposed official page is production/marketing succession wording, not direct story-relation evidence.

## Global Constraints

- Preserve existing relation IDs, directions, kinds, scopes, directness, continuity scopes, certainty, and notes.
- Use only relation-specific official primary sources; do not reuse generic catalogue/listing sources as relation evidence.
- Do not infer release/status, chronology, identity, Earth numbers, multiverse transitions, or new work pairs.
- Keep `uncertain_legacy_tv` unchanged for the Cloak & Dagger → Runaways crossover.
- Use `C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` with PowerShell's `&` call operator.
- Ordinary builds must leave canonical CSVs and persistent review history unchanged except for the intentional promotion rows.

## Selected relations and sources

1. `work-relation-avengers-age-of-ultron-2015-captain-america-civil-war-2016-aftermath` → `https://www.marvel.com/amp/articles/movies/the-essential-marvel-cinematic-universe-guide-phase-three`
2. `work-relation-thor-ragnarok-2017-avengers-infinity-war-2018-crossover` → `https://www.marvel.com/articles/tv-shows/tom-hiddleston-decade-god-of-mischief-loki-mcu`
3. `work-relation-captain-america-civil-war-2016-ant-man-and-the-wasp-2018-aftermath` → `https://www.marvel.com/movies/ant-man-and-the-wasp`
4. `work-relation-ms-marvel-2022-the-marvels-2023-story-link` → `https://thewaltdisneycompany.com/news/the-marvels-director-nia-dacosta-on-crafting-a-cosmic-team-up-of-epic-proportions/`
5. `work-relation-what-if-s2-2023-what-if-s3-2024-sequel` → `https://www.marvel.com/articles/tv-shows/sdcc-2022-marvel-studios-animation-panel`
6. `work-relation-iron-man-3-2013-all-hail-the-king-2014-sequel` → `https://www.disneyplus.com/browse/entity-14988369-345c-4984-9c16-59428bd70609`
7. `work-relation-the-avengers-2012-item-47-2012-sequel` → `https://www.disneyplus.com/browse/entity-2cd46937-17fe-4ada-8de4-0972f2763f1c`
8. `work-relation-jessica-jones-s1-2015-jessica-jones-s2-2018-sequel` → `https://www.marvel.com/amp/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-critically-acclaimed-marvel-s-jessica-jones`
9. `work-relation-jessica-jones-s2-2018-jessica-jones-s3-2019-sequel` → `https://www.marvel.com/articles/tv-shows/marvel-s-jessica-jones-renewed-for-season-3`
10. `work-relation-iron-fist-s1-2017-iron-fist-s2-2018-sequel` → `https://www.marvel.com/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-marvel-s-iron-fist?EML=072018_SDCC_Season2&cid=SDCC18&mi_u=2417338`
11. `work-relation-cloak-dagger-20182019-runaways-20172019-crossover` → `https://www.marvel.com/articles/tv-shows/first-look-runaways-meet-cloak-and-dagger?linkId=78522422`

## Task 1: Add the wave010 regression contract

**Files:**
- Create: `tests/library_v5/test_relation_evidence_promotion_wave010.py`
- Read: `data/library/work_relations.csv`, `data/library/sources.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, `data/derived/work_pair_reasons.csv`

Require each selected ID to be `source_verified` with exact source/evidence/review records while preserving all semantic fields. Require the deferred X-Men Apocalypse relation to remain `legacy_seed`. Assert the graph node/edge/reason counts and selected relation reason statuses remain compatible.

### RED check

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $MarvelPython -m unittest tests.library_v5.test_relation_evidence_promotion_wave010 -v
```

Expected: FAIL before canonical source/evidence/review additions. This RED check was observed before the canonical edits.

## Task 2: Add source, evidence, and review records

**Files:**
- Modify: `data/library/work_relations.csv`
- Modify: `data/library/sources.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`

Change only the eleven selected `verification_status` fields. Append one source, one primary evidence row, and one `verified_source` review transition dated `2026-09-04` per relation. Evidence notes must describe only the directly supported relation; no release, date, universe, variant, or chronology assertions.

## Task 3: Regenerate and verify deterministic outputs

Run the focused test, full bundled suite, deterministic build, `git diff --check`, independent connectivity checks, and real Chrome selection/interaction/chronology/publication-order audits when available. Expected graph topology remains unchanged; only verification metadata/reason support changes. These checks are complete and green for this branch.

```powershell
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

## Task 4: Review and integrate

**Files:**
- Create: `docs/superpowers/reviews/2026-09-04-marvel-relation-evidence-promotion-wave010.md`
- Update after semantic merge: `AGENTS.md`, `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md`, `CODEX_MASTER_ROADMAP_MARVEL_DB_V1_TO_MAIN_2026-08-28.md`

Inspect the complete diff, commit and push the feature branch, open a PR, wait for required CI, and merge through the normal PR path under the user's standing authorization. Then record the merged SHA, CI/Pages result, counts, deferred relation, and clean-worktree verification in a docs-only follow-up.
