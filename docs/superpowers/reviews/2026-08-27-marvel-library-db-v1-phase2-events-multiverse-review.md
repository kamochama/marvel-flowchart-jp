# Marvel Library DB v1 Phase 2 Events & Multiverse 完了監査

日付: 2026-08-28

対象リポジトリ: `kamochama/marvel-flowchart-jp`

対象ブランチ: `library-v5-phase2-db6`

> **Historical review notice (updated 2026-08-30):** This review is the Task 8 snapshot from 2026-08-28. Its `main`/PR #10 statements and counts are historical. The current production baseline is `main` at `19134e187d40e808f926fd32607b0a2deebac8f1`; later PR #11, #12, #13, #21, and #22 integrations are recorded in `NEXT_CODEX_HANDOFF_MARVEL_LIBRARY_PHASE2_2026-08-28.md` and the roadmap.

実装前の基準 HEAD: `abe9bdbb29cd3a55869a153a8e2713091a09b5be`

`main` / `origin/main`: `3af097b72c174077c83d7091f79222a72fc7134f`（不変）

## 結論

Events & Multiverse Task 7 の bounded batch と Task 8 のローカル完了監査は **PASS** と判定する。既存の transition semantics、監査履歴、SQLite query layer、互換グラフを維持したまま、America Chavez の Earth-838 同伴者と Wade Wilson の Earth-10005 -> TVA 移送を evidence-backed に追加した。

これは `main` への merge、PR #10 の完成、または Phase 2 後続の releases / credits / memberships / possessions / HTML 作業の承認を意味しない。PR #10 は未マージであり、公開変更は行っていない。

## Fresh verification evidence

### Unit tests

実行コマンド:

```text
python -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
```

結果:

```text
Ran 165 tests in 11.142s
OK
```

追加した主要回帰テスト:

- `test_phase2_mom_america_participant.py`
- `test_phase2_deadpool_wade_tva_transfer.py`

### Build / audit / database

```text
audit_ok: true
audit_issue_count: 0
content_audit.issue_count: 0
SQLite foreign_key_check: 0 rows
SQLite integrity_check: ok
protected_inputs_unchanged: True
```

Build observations（件数は正しさの固定目標ではない）:

| 項目 | 件数 |
|---|---:|
| entities | 44 |
| appearances | 169 |
| continuities | 11 |
| events | 9 |
| event_occurrences | 9 |
| multiverse_transitions | 9 |
| transition_participants | 10 |
| evidence | 103 |
| reviews | 78 |
| work_edges_all | 361 |
| work_pair_reasons | 569 |
| prewatch_edges | 199 |
| story paths reproduced | 83 / 83 |

厳密な `csv.reader` 列数監査は `data/**/*.csv` 全体で `0` bad rows。全 applied JSON のキー存在・一意性、および update の最終 notes 値一致も `OK`。

### Remote / branch boundary

`git fetch origin` 後に次を確認した:

- `HEAD == origin/library-v5-phase2-db6`（今回の監査済み変更を push 済み）;
- `main == origin/main == 3af097b72c174077c83d7091f79222a72fc7134f`;
- `main` は変更していない。

PR #10 の head には今回の America Chavez / Wade Wilson 追加分と監査修正を push 済みで、GitHub Actions の fresh `test` job が success となった。これにより、今回の変更に対するリモート CI も確認済みである。

## Migrated cases

Task 5–7 の evidence-backed first-class facts:

1. Earth-828 の Fantastic Four `Excelsior` 到着;
2. No Way Home の Raimi / Webb Peter Parker 到着;
3. Eddie Brock / Venom の SSU -> Earth-616 -> SSU round trip;
4. Adrian Toomes / Vulture の Earth-616 -> SSU transfer;
5. Monica Rambeau の Earth-616 -> 記述的 alternate universe arrival;
6. Doctor Strange と America Chavez の Earth-616 -> Earth-838 traversal（同一 event の二名の traveler）;
7. Wade Wilson の Earth-10005 -> TVA / outside-timeline `tva_transfer`。

既存の純粋な crossing proxy は、既に parity と review history を確認済みのものだけ supersede し、独立した causal / story relation は保持した。今回の二つの追加 batch は work relation を退役させず、単一作品内の移送から新しい work-pair reason を作っていない。

## Deferred / explicit no-go cases

- `Multiverse of Madness` の無名・未特定の視覚的 dimension jump は、安定した source/destination と traveler が揃わないため未モデル化。
- `Deadpool & Wolverine` の TVA 後の TempPad による各 Wolverine variant 訪問は、単一の安定した destination continuity を特定できないため未モデル化。
- `Deadpool & Wolverine` の Logan (2017) と co-lead Wolverine の exact individual identity は variant 境界を越えて同一視していない。
- Blade / Elektra / Human Torch の legacy return は、既存の uncertain-return relation を exact old-film continuity に昇格していない。
- `Earth-838` は FOX X-MEN、Inhumans-series Black Bolt、または他の legacy grouping と同一視していない。

## Semantic safety checks

回帰テストと build audit により、次を確認した:

- transition の semantic home は `events.csv` / `event_occurrences.csv` / `multiverse_transitions.csv` / participant facts のまま;
- shared continuity や actor reuse だけで transition / identity / work pair を作っていない;
- `identity_of` と `variant_of` の境界を維持し、America Chavez と既存 entity、Wolverine variants を不当に collapse していない;
- `v_event_history` / `v_multiverse_crossings`、DB logical fingerprint、graph exporter は既存 determinism テスト群で GREEN;
- superseded proxy relation は replacement semantic reason と review history を持つ;
- ordinary build は canonical library と persistent `reviews.csv` を変更していない。

## Full-PR audit follow-up

リモート PR ref の read-only 監査で、旧 `library-v5-canonical-freeze` branch を参照する review-patch workflow を確認したため、現行 forward branch `library-v5-phase2-db6` を checkout・push 先とする回帰テストと修正を追加し、今回のローカルコミットに含めた。リモート snapshot に残っていた Earth-838 transition の notes 未引用も、現在のローカル canonical CSV では完全引用済みで、厳密な列数監査は `0` bad rows である。

同じ欠陥の再発防止として、`audit.py` に `DictReader` の余剰列を見逃さない CSV shape 検査を追加し、malformed row 回帰テストを通過させた。

## Next boundary

この監査で現行 Events & Multiverse plan の Task 7/8 はローカルおよび PR CI 上 PASS とした。次は PR 全体を確認したうえで、ユーザーから `main` への最終 merge / publish の明示承認を得る段階である。承認がない限り production は変更しない。
