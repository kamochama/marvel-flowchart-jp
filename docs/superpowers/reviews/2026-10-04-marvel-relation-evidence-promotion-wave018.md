# Wave018 execution ledger and review

Plan: `docs/superpowers/plans/2026-10-04-marvel-relation-evidence-promotion-wave018.md`.
Base: `3506aeeb07ada4bae52d951ae69c5112a3cf6b85` (PR #104, Pages 37174090086 success, merged-main 622 tests OK / 6 gated skips, HTTPS HTTP 200).

## Decisions and evidence

- Sony's [collection description](https://www.sonypictures.com/movies/venom3moviecollection) explicitly names Venom and Let There Be Carnage as Eddie and Venom's earlier adventures relative to The Last Dance, the final trilogy film. This supports story continuation, not collection membership alone. The [Last Dance page](https://www.sonypictures.com/movies/venomthelastdance) corroborates the trilogy conclusion but is not a second registered source.
- Promote only existing `work-relation-venom-let-there-be-carnage-2021-venom-the-last-dance-2024-story-link`; retain all tuple fields, probable certainty and Japanese notes. No shortcut Venom 1 -> 3, sequel reclassification, event chronology, identity, numbered Earth, release/status or transition is added.
- Ordinary non-Work ChatGPT read the Sony sources and approved this bounded status-only plan: https://chatgpt.com/c/6ac1bb97-6934-83ee-acee-9aedada32826 . Its caution against claiming new directness or certainty is reflected in the evidence notes.
- Independent Fox F4 audit: official [2007 page](https://www.20thcenturystudios.jp/movies/f4-2) describes the team reuniting but does not identify the 2005 endpoint as a direct sequel. Series listing includes the 2015 reboot. Defer; do not substitute a nonofficial press-kit mirror or shared cast for exact evidence. Canonical row unchanged.
- Iron Man auditor found a candidate [official production-notes PDF](https://i.annihil.us/u/prod/avengersmovie/ironman3/fullsite1/pdf/Iron_Man_3_Notes.pdf). Ruling: keep the relation unchanged and queue main-agent PDF verification for a separate wave, since historical Wave012/013 deferred related-title/production-note material and this claim needs reconciliation. Cost if delayed: one seed remains, not a lost line.

## Execution and verification

- Pre-flight: Task 2 consumes Task 1 provenance; build precedes inventory regeneration to avoid stale reasons. No conflicting interfaces.
- Runtime ruling: skill shell bookkeeping scripts are not native PowerShell commands; use this tracked ledger and repository modules without installing a shell or alternate implementation helpers.
- Baseline 622 tests OK / 6 gated skips. Task 1 complete: exact provenance regression observed RED on legacy_seed, then GREEN after minimal status/source/evidence/review edits.
- Task 2 local verification: 623 tests OK / 6 gated skips, audit/content issues 0. Rebuild leaves canonical CSV/review hashes and all three graph export hashes unchanged.
- Strict CSV shapes valid, FK 0, SQLite integrity ok, inventory coverage all empty/zero.
- Relations 164 total / 161 active / 68 verified / 93 seeds / 3 superseded; sources 105 / evidence 195 / reviews 169.
- Topology 131 nodes / 355 edges / 562 reasons, prewatch 199, story paths 83/83. Recursive JSON comparison finds six scalar changes: one edge reference/weak -> recommended/strong with Japanese label/note, reason status and fingerprint. No viewer/export-policy implementation changes.
- CRLF-aware whitespace check passes; preexisting report CRLF conventions retained.

## Remaining gates

Independent full-diff review, ordinary ChatGPT final review, seven-job CI, normal PR merge and merged-main/Pages publication verification remain pending. Neither this wave nor the whole-work audit is called published/complete yet.
