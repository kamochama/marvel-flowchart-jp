# Marvel Library DB v1 normalized release/status Task 6 完了監査

監査日: 2026-08-29
対象リポジトリ: `kamochama/marvel-flowchart-jp`

> **Historical review notice (updated 2026-08-30):** This review records the normalized release/status seed boundary before evidence promotions. Its `main` and all-`legacy_seed` statements are historical. The latest semantic production baseline is `main` at `641d16577c847ab5f917e3faea0900536dc0baab`; PR #22, PR #26, PR #28, and PR #30 subsequently promoted evidence-backed release/status facts, as recorded in the current Codex handoff and roadmap. The full-audit disposition is 27 promoted, 240 deferred, and 2 conflicted facts; later documentation-only commits do not alter code/data.

## 対象と実行境界

この監査は、別承認された `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md` の normalized release/status subproject（Task 6）だけを対象とする。

- 対象ブランチ: `codex/db-v1-releases-status`
- 最終検証 HEAD: `dd56f321eb58569be1b6f386f4421cd2f10235bf` (`test: normalize graph fixture newlines for compatibility`)
- fresh `origin/main`: `2410ea482d9fe6c9063a23b80b9b766e2bb9daac`
- `git merge-base HEAD origin/main`: `2410ea482d9fe6c9063a23b80b9b766e2bb9daac`
- `main` は変更していない。今回の作業で merge、publish、push は行っていない。

最終 HEAD の `dd56f321` は Task 5 の cross-platform test fix のみである。graph fixture の CRLF/LF checkout 差を比較前に LF へ正規化し、同じ回帰を検出する小さなテストを追加した。production implementation、canonical data、graph policy の意味は変更していない。

Events & Multiverse の Task 7/8 は既存の `2026-08-27-marvel-library-db-v1-phase2-events-multiverse-review.md` に記録済みの別実行境界である。この文書はその完了判定を変更せず、release/status の正規化だけを監査する。`index.html` と既存の graph policy も変更していない。

## 正規化された表と migration

新しい canonical table の header は次のとおりである。

```text
releases.csv
release_id,work_id,territory,release_kind,release_date,release_precision,status,certainty,verification_status,notes

production_status_assertions.csv
production_status_assertion_id,work_id,status,asserted_at,certainty,verification_status,notes
```

`data/migration/normalized-releases-status/` の deterministic candidate と canonical rows は次の件数で一致する。

| 項目 | 件数 |
|---|---:|
| `works.csv` source work rows | 131 |
| `releases.csv` | 138 |
| primary release rows | 131 |
| Japanese-date (`JP`) release rows | 7 |
| `production_status_assertions.csv` | 131 |
| review queue 全体 | 698 |
| release/status の review queue rows | 269 |
| persistent review ledger rows | 78 |

適用記録は `data/content_audit/applied/2026-08-28-normalized-releases-status-seed.json` であり、候補 SHA-256 は次のとおりである。

- `data/migration/normalized-releases-status/releases.csv`: `de2c3eebcdea1f84e40cbf24b819834b37fa837a89e58010047b1774d073b4cd`
- `data/migration/normalized-releases-status/production_status_assertions.csv`: `a3d9dba46daca8921a4374894a10fbad618a1c0b11ebca15d63f5c2ee3900905`

全 269 件の新規 release/status fact は `verification_status=legacy_seed` のままである。この seed は `evidence.csv` や `reviews.csv` を追加せず、既存の `works.csv` の日付・status・source note を決定的に写像しただけである。したがって、qualifying evidence を追加して `source_verified` に昇格する作業と auditable promotion transition は、後続の別承認 audit batch に延期する。`asserted_at=2026-08-28` は current status snapshot の監査日であり、歴史的な production milestone を主張しない。

## Follow-up after this historical boundary

Evidence-promotion batches are intentionally separate from this seed migration. PR #22 (batch005, 2026-08-30) added qualifying evidence and review transitions for exactly two existing facts: X-Men '97 Season 2's primary streaming release and its released-status snapshot. The Japanese row remains unverified with a blank date. The post-batch005 counts were 6 source-verified releases of 138 and 2 source-verified statuses of 131; batch006 adds one source-verified VisionQuest status (3 of 131), and batch007 adds one source-verified Avengers: Doomsday announced-status snapshot (4 of 131). Remaining seeds require their own bounded audit without graph inference.

## Full verification evidence

すべてのコマンドは repository root で、指定の bundled Python runtime を用いて実行した。

### Unit tests

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
```

exit code `0`; `Ran 195 tests in 11.974s`; `OK`。追加の 1 test は上記 CRLF/LF graph fixture comparison の cross-platform regression test である。

### Ordinary build / audit

```powershell
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

exit code `0`。build の観測値は次のとおりである。

- `audit_ok=true`, `audit_issue_count=0`
- content-audit `issue_count=0`, review integrity issues `0`
- `canonical_files=21`
- review queue `698`、persistent review rows `78`
- verification-status 集計: `legacy_seed=698`, `source_verified=61`, `superseded=4`
- DB schema version: `1.2-normalized-releases-status`

SQLite は `data/derived/db/marvel.sqlite` に生成された。`PRAGMA foreign_key_check` は `0` rows、`PRAGMA integrity_check` は `ok` である。

### DB table/view counts and logical fingerprint

生成 manifest の logical equivalence fingerprint は次である。

```text
80f345416dd37ea81dcc9a89b128020132440a9538506820764382d6b20c6825
```

| table | rows | table | rows |
|---|---:|---|---:|
| `_entity_identity_map` | 44 | `appearances` | 169 |
| `chronology_assertions` | 0 | `continuities` | 11 |
| `entities` | 44 | `entity_relations` | 1 |
| `event_occurrences` | 9 | `event_participants` | 0 |
| `event_relations` | 0 | `events` | 9 |
| `evidence` | 103 | `multiverse_transitions` | 9 |
| `people` | 7 | `portrayals` | 8 |
| `production_status_assertions` | 131 | `releases` | 138 |
| `reviews` | 78 | `sources` | 43 |
| `transition_participants` | 10 | `work_continuities` | 104 |
| `work_relations` | 164 | `works` | 131 |

公開 view の row counts は `v_work_releases=138`、`v_work_production_status=131`、`v_flowchart_nodes=131`、`v_flowchart_edge_candidates=361`、`v_work_connection_reasons=569`、`v_work_connections_all=361`、`v_continuity_works=103`、`v_entity_work_history=169`、`v_event_history=9`、`v_multiverse_crossings=10` である。

同一生成物に対して build を再実行し、manifest と `work_pair_reasons.csv`、`work_edges_all.csv`、`prewatch_edges.csv`、`story_paths.csv` の SHA-256 を比較した結果は `deterministic=true` であった。

| output | SHA-256 |
|---|---|
| `library_db_manifest.json` | `a81525cf44a8c40cac5788202d6c0097de46bae272c6fdb612264403acbcf612` |
| `work_pair_reasons.csv` | `9a26aabc720151e67f95cd4daf683f9f619e79098a10f29432524733ed386897` |
| `work_edges_all.csv` | `26da871dc424c469331e186b208e710acf1751e580484206b5e9b3fb5ae08f77` |
| `prewatch_edges.csv` | `bf8831bec41d92920e9e4afe4b75435a8d318e529bc3bdb80bda316cef91f4d8` |
| `story_paths.csv` | `5190f81fdb503e0df643277114e50f80e84f85ec25127a9f53307361f0d6f4e2` |

### Graph compatibility and protected inputs

legacy graph の row counts は `work_edges_all=361`、`work_pair_reasons=569`、`prewatch_edges=199`、`story paths reproduced=83/83` である。生成した 4 つの graph CSV は fresh `origin/main` (`2410ea482d9fe6c9063a23b80b9b766e2bb9daac`) にある既存 output と byte-identical であり、上表の SHA-256 も一致した。

`index.html` を一時的に退避して build した追加確認も `build_audit_ok=true`、`graph_equal_without_index=true` となった。release/status table と public views は既存の graph derivation に接続していない。

build 前後の protected input hash 比較は `protected_inputs_unchanged=true`、変更キー `[]` であった（canonical library 21 files + persistent `reviews.csv` 1 file）。`reviews.csv` は 78 rows、SHA-256 `1e380546f108d6afe7d2b7059a86f200d4e3ae20263c0b81dd7b5bae9e8bbf6b` である。

`data/**/*.csv` の strict `csv.reader` shape scan は 46 files、`bad_rows=0`。`git diff --check` は exit code `0` で、canonical CSV の notes field に余分な列はない。検証後、build が生成した `data/derived/` と `data/content_audit/{queue.csv,CONTENT_AUDIT.md}`、テストの `__pycache__/` だけを cleanup し、追跡済みの graph CSV と `views/flowchart/{README.md,policy.json}` は保持した。

## Deferred scope と integration gate

この subproject は次を実施していない。

- legacy seed rows の evidence-backed `source_verified` promotion と review transition;
- credits、entity aliases、memberships、possessions の追加;
- 新たな multiverse decomposition;
- `index.html` の DB-derived node/edge JSON への切替（HTML DB-export milestone は未着手）。

PR は primary agent が全体差分と fresh remote CI を最終確認する準備ができているが、この Task では push、PR merge、production publish を行っていない。`main` への統合には、上記の全体監査後にユーザーの明示的な merge authorization が必要である。release/status の evidence promotion と HTML DB-export は、それぞれ別の実行計画・承認境界として扱う。

## Full release/status evidence audit — PR #30

The later full-fact audit is recorded in `docs/superpowers/reviews/2026-08-30-marvel-library-full-release-status-audit.md` and was merged as PR #30 at `641d16577c847ab5f917e3faea0900536dc0baab`. It promotes only exact source/evidence/review matches: 27 facts promoted, 240 deferred, and 2 conflicts retained as `legacy_seed`. GitHub Actions run #285 passed 305 tests; build/audit/review/FK checks are zero and graph compatibility remains 361 edges, 569 reasons, prewatch 199, and story paths 83/83. The normalized rows now contain 14 verified releases and 13 verified status snapshots (sources/evidence/reviews 49/130/105). The next boundary is a separately planned HTML design/operation debugging pass; this historical review does not claim that UI debugging has started.
