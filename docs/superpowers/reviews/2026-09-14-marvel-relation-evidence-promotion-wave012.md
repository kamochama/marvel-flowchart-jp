# Marvel Library v5 relation evidence promotion wave012 review

## Scope

This wave promotes only three existing direct-sequel relation facts from
`legacy_seed` to `source_verified`. Relation tuples, directions, graph edges,
reason IDs, and all non-relation semantic domains remain unchanged.

## Promoted relations

| relation | source | bounded support |
| --- | --- | --- |
| Captain America: The Winter Soldier → Captain America: Civil War | [Disney announcement](https://thewaltdisneycompany.com/news/brand-new-trailer-and-posters-released-for-marvels-captain-america-civil-war/) | Calls *Civil War* the third Captain America installment; supports the existing direct sequel relation only. |
| Thor: The Dark World → Thor: Ragnarok | [Disney 2017 shareholder transcript](https://thewaltdisneycompany.com/app/uploads/2017-asm-transcript.pdf) | Calls *Thor: Ragnarok* the third Thor installment; supports the existing direct sequel relation only. |
| Thor: Ragnarok → Thor: Love and Thunder | [Marvel / Kevin Feige](https://www.marvel.com/watch/trailers-and-extras/kevin-feige-says-thor-love-and-thunder-is-more-than-just-ragnarok-2) | Calls *Love and Thunder* the fourth Thor installment and frames it as more than “Ragnarok 2”; supports the existing direct sequel relation only. |

Each relation has one relation-specific source, one `primary` evidence row with
`fact_table=work_relations.csv`, and one `legacy_seed -> source_verified`
review transition. No source is used to infer release dates, production
status, chronology, Avengers/Guardians participation, or continuity changes.

## Deferred boundary

Iron Man 2 → Iron Man 3 remains `legacy_seed`: the inspected Iron Man 3
material was a related-title/production-note reference rather than a sufficiently
direct relation statement for this strict wave. Spider-Man 2 → Spider-Man 3,
Blade, old X-Men, and Fantastic Four remain deferred for the same source-boundary
reason. No relation was deleted or rewritten.

## Verification

- build audit issues: 0
- content-audit issues: 0
- graph topology: 131 works / 355 edges / 562 reasons
- story paths: 83 / 83 reproduced
- focused Wave012 + explicit inventory + connection inventory: 18 / 18 passed
- releases/status/events/transitions/appearance/identity canonical facts: unchanged by this wave

## Independent review

通常ChatGPTへ根拠URL、対象relation、provenance ID、status遷移、検証結果、
保留境界を提示した。判定は `LGTM`（Important / Majorなし）。同一シリーズの
公式「第3作／第4作」記述を、既知の第2作／第3作との隣接続編検証に使う境界は
妥当だが、reboot・分岐・単なる次作には拡張しないこと、evidence noteは
「ordinal evidenceが既存隣接関係を支持」に限定することを再確認した。
実CSVの最終文字列とrelease/status/events/transitions非変更は、以下のローカル
diff・CIで引き続き確認する。

The full bundled test suite and the normal CI/browser review gate remain the
completion checks before merge.
