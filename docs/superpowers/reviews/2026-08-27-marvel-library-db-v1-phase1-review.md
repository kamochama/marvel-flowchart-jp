# Marvel Library DB v1 Phase 1 完了レビュー

日付: 2026-08-27

対象リポジトリ: `kamochama/marvel-flowchart-jp`

対象ブランチ: `library-v5-canonical-freeze`

実装検証対象 HEAD: `b30fd4b2eb4dd67faf5294edc96ee7ea1c6bcd41`

production `main` baseline: `3af097b72c174077c83d7091f79222a72fc7134f` (`v5.20.5`)

PR: #9 (`library-v5-canonical-freeze` -> `main`, draft)

> **Historical review notice (updated 2026-08-30):** This is the Phase 1 snapshot from 2026-08-27. The PR #9/draft and `main` baseline statements below are historical; the current production baseline is `main` at `19134e187d40e808f926fd32607b0a2deebac8f1`. Consult `AGENTS.md` and the current Codex handoff for present integration state and verification counts.

## 結論

Marvel Library DB v1 Phase 1 の実装境界は **PASS** と判定する。

Phase 1 で行ったのは、既存の人間可読な Marvel Library v5 正本を SQLite query layer へ決定的にコンパイルし、現在の work graph を SQLite の public view から同一意味・同一互換形式で再生成できるようにすることまでである。

これは **Marvel 内容監査全体の完了を意味しない**。既存 `legacy_seed` の外部ソース監査は継続中であり、Phase 2 の normalized semantic tables もまだ導入していない。

`main` への merge はこのレビューでは承認しない。Phase 2 もこの Phase 1 plan の範囲では開始しない。

## 正本と DB の役割

- `data/library/**` は引き続き authoritative canonical input である。
- `data/content_audit/reviews.csv` は persistent human review history であり、通常 build が書き換えてはいけない protected input である。
- `data/derived/db/marvel.sqlite` は生成物であり、正本ではない。
- SQLite の物理バイト列は correctness / reproducibility target ではない。
- DB の同一性は schema、canonical input hashes、table/view の logical contents からなる `library_db_manifest.json` の logical fingerprint で判定する。
- `index.html` は DB / graph 正本生成の入力ではない。

## Fresh verification evidence

最終修正後の fresh CI:

- implementation commit: `b30fd4b2eb4dd67faf5294edc96ee7ea1c6bcd41`
- workflow: `Library v5 canonical freeze CI`
- run: `33075335198` (run #135)
- job: `98527933516`
- conclusion: `success`

Unit tests:

- `Ran 101 tests in 3.602s`
- `OK`

Build / audit:

- `audit_ok: true`
- `audit_issue_count: 0`
- canonical library files observed: `13`
- content review integrity issues: `0`

SQLite integrity:

- `PRAGMA foreign_key_check`: `0` rows
- `PRAGMA integrity_check`: `ok`

DB schema:

- `db_schema_version`: `1.0-phase1`
- logical equivalence fingerprint: `e59e5f175bf043a2ce4788760125e6cbfb6b7116beccc4b960f3c31b2cefeb09`

## Loaded table observations

Counts are observations only; they are not correctness targets.

| table | rows |
|---|---:|
| works | 131 |
| entities | 41 |
| entity_relations | 1 |
| appearances | 166 |
| people | 7 |
| portrayals | 8 |
| continuities | 6 |
| work_continuities | 104 |
| chronology_assertions | 0 |
| work_relations | 164 |
| sources | 38 |
| evidence | 45 |
| reviews | 26 |
| `_entity_identity_map` (internal generated table) | 41 |

## Public view observations

| view | rows |
|---|---:|
| `v_entity_work_history` | 166 |
| `v_continuity_works` | 103 |
| `v_work_connection_reasons` | 565 |
| `v_work_connections_all` | 361 |
| `v_flowchart_nodes` | 131 |
| `v_flowchart_edge_candidates` | 361 |

Current graph observations:

- `work_pair_reasons.csv`: 565
- `work_edges_all.csv`: 361
- `prewatch_edges.csv`: 199
- reproduced story paths: 83

Again, 565 / 361 / 199 / 83 are observations, not desired fixed counts.

## Semantic parity result

Phase 1 SQL view semantics were compared against the existing tested Python derivation oracle over the actual current canonical dataset.

Verified:

1. `v_work_connection_reasons` and the Python `combined_all_pairs` oracle have the same semantic reason set.
2. Same-performer / different-fictional-entity does not produce a character relation.
3. `identity_of` aliases collapse for work-history/shared-entity derivation.
4. `variant_of` does not collapse automatically.
5. superseded identity / work relation facts do not participate in the corresponding live derivation.
6. DB exporter reproduces current `reason_id`, `edge_id`, fields, and row ordering.
7. repeated DB export is byte deterministic for the compatibility CSV products.

The ordinary production build path no longer calls the legacy `write_derived_edges` writer. It now follows:

`canonical text inputs -> SQLite compile -> SQL public views -> DB graph exporter -> compatibility outputs -> content/library audit`

The old Python derivation remains as a regression oracle/test implementation during this migration phase, not as the ordinary build graph source.

## Reproducibility and isolation result

Fresh CI verified all of the following:

- canonical `data/library/**` hashes are unchanged by ordinary build;
- persistent `data/content_audit/reviews.csv` is protected at the build boundary and mutation is rejected by regression test;
- two ordinary builds produce the same logical DB manifest;
- two ordinary builds produce byte-identical `work_pair_reasons.csv` and `work_edges_all.csv`;
- ordinary library manifest is deterministic;
- raw `marvel.sqlite` bytes are excluded from the ordinary library manifest;
- logical `library_db_manifest.json` is included as the DB reproducibility record;
- graph regeneration succeeds with `index.html` temporarily absent and reproduces the same graph outputs;
- bootstrap reconstruction remains deterministic and isolated;
- bootstrap does not install or overwrite audited canonical data.

## Atomic compiler boundary

The compiler:

- builds a sibling temporary SQLite file;
- enables foreign keys;
- validates CSV header contracts;
- loads inside a transaction;
- runs foreign-key and integrity checks;
- publishes the generated DB only after successful validation;
- removes the temporary candidate on compile failure.

A broken-FK regression test confirms that invalid canonical input cannot be accepted as a valid DB compile.

## Bugs / audit gaps found and fixed during Phase 1

### 1. First Steps -> Doomsday continuity scope

SQLite CHECK constraints exposed an existing canonical semantic-column error:

- previous `continuity_scope`: `crossover`
- corrected `continuity_scope`: `multiverse`

`crossover` belongs to relation classification vocabulary and was invalid as a continuity scope. Because `The Fantastic Four: First Steps` is explicitly audited as Earth-828 while the relation leads into `Avengers: Doomsday`, `multiverse` is the appropriate continuity-scope value.

The correction was not silently edited. It was applied through the persistent review-patch workflow with existing evidence and a new `verified_rechecked` audit action, leaving the fact `source_verified -> source_verified` while preserving the semantic correction history.

Applied audit commit:

`1d04879cbfa8866c76e19108b5496268e077304c`

### 2. Raw SQLite bytes in ordinary manifest

The first DB-backed build revealed that the old ordinary manifest would recursively hash `data/derived/**`, thereby treating the raw SQLite file bytes as a reproducibility requirement.

That contradicted the DB design. The manifest logic was corrected so:

- `data/derived/db/marvel.sqlite` is excluded;
- `data/derived/db/library_db_manifest.json` remains included.

A regression test fixes this contract.

### 3. Persistent review-ledger mutation guard

Final PR review found that ordinary build directly guarded `data/library/**`, but relied on implementation convention rather than a build-boundary hash guard for `data/content_audit/reviews.csv`.

A RED regression test injected a harmless byte mutation into `reviews.csv` during build and proved the previous build did not reject it. The build guard was then extended to protected inputs:

- canonical `data/library/**`;
- persistent `data/content_audit/reviews.csv`.

The final fresh CI run includes the now-GREEN regression test `test_ordinary_build_rejects_persistent_review_mutation`.

## Content-audit status after Phase 1

Structural/database Phase 1 PASS must not be read as content verification completion.

Current observed verification states:

- `legacy_seed`: 429
- `source_verified`: 19
- `superseded`: 1

Persistent review rows:

- 26

Current content-audit queue:

- 429

Content review integrity issues:

- 0

The 429 queued facts remain actual Marvel-content review work. They should be promoted, superseded, or marked conflicted only through source-backed review actions; no fixed final edge count is implied.

## Phase 2 deferred semantic model

The following normalized semantic tables are intentionally **not** introduced in Phase 1 and require a separate Phase 2 implementation plan:

- `releases`
- `production_status_assertions`
- `credits`
- `entity_aliases`
- `entity_memberships`
- `events`
- `event_occurrences`
- `event_participants`
- `event_relations`
- `multiverse_transitions`
- `transition_participants`
- `entity_possessions`

In particular, current multiverse-related `work_relations` have **not** been automatically decomposed into `multiverse_transitions` facts. Doing that is a semantic canonical-model change and must not be smuggled into the DB compiler migration.

## Merge / next-phase boundary

At this checkpoint:

- DB v1 Phase 1 implementation: PASS
- ordinary build cutover to DB graph path: PASS
- SQL/Python semantic parity: PASS
- logical reproducibility: PASS
- SQLite FK/integrity checks: PASS
- protected canonical/review inputs: PASS
- full Marvel content audit: NOT COMPLETE
- Phase 2 normalized semantic migration: NOT STARTED
- merge to `main`: NOT PERFORMED / NOT AUTHORIZED BY THIS REVIEW

Before any future merge, `main` HEAD and PR head must be checked again and the merge must be an explicit separate action.
