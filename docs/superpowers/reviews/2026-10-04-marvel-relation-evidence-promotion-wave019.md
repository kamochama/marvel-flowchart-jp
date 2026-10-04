# Wave019 execution ledger and review

Plan: `docs/superpowers/plans/2026-10-04-marvel-relation-evidence-promotion-wave019.md`.
Base `e21a2606a22ad30473b16f53cd03ad187c1dbf05`: PR #105 integrated, CI seven jobs green, Pages 37175026829 succeeded, merged-main 623 tests OK / 6 skips, HTTPS HTTP 200.

## Evidence and rulings

- Main-agent and independent source audit read [Marvel's official production notes](https://i.annihil.us/u/prod/avengersmovie/ironman3/fullsite1/pdf/Iron_Man_3_Notes.pdf), page 2. Named Iron Man / Iron Man 2 context precedes THE STORY; Feige's combined culmination/sequel explanation distinguishes The Avengers as another follow-up context. Supports the existing Iron Man 2 -> 3 sequel, not related-title membership or culmination alone.
- Ordinary non-Work ChatGPT independently read the PDF and historical Wave012 review, approving this bounded promotion: https://chatgpt.com/c/6ac1bb97-6934-83ee-acee-9aedada32826 . Caution: do not pretend the PDF contains a literal sentence naming Iron Man 2 as the sequel endpoint; notes accurately paraphrase combined wording and context.
- Promote only `work-relation-iron-man-2-2010-iron-man-3-2013-sequel` status; preserve endpoints, sequel/story/direct/same_or_intended/confirmed and notes. The Avengers -> Iron Man 3 remains a separate unaudited seed. No shortcut pair or chronology/identity/release/status/events/transitions changes.
- Ruling: historical Wave012/013 defer records remain unchanged. This re-audit identifies a specific story statement, not a blanket reversal of the old evidence standard. Cost if interpretation is wrong: one relation would be oververified; exact provenance, independent review and source notes expose this decision for correction.
- Runtime ruling: keep the persistent execution ledger here and use repository modules rather than non-native shell bookkeeping scripts; no tooling installation.

## TDD and verification

- Pre-flight: provenance is Task 1 output; Task 2 build precedes inventory regeneration. No conflicting interfaces.
- Baseline 623 tests OK / 6 gated skips. New exact tuple/source/evidence/review regression observed RED on legacy_seed before promotion, GREEN afterward.
- Initial full suite: 624 tests, two failures in historical Wave012/013 current-state defer assertions for this fact. Root cause traced to changed verification status, not broken provenance/graph behavior. Ruling: update only this relation's current-state assertions and retain other X-Men/Blade/F4 guards; Wave019 regression pins exact qualifying provenance. Historical documents unchanged.
- Final full suite 624 tests OK / 6 gated skips. Build audit/content issues 0; canonical/review hashes unchanged across rebuild and all three graph export hashes deterministic.
- Strict CSV shapes valid, FK 0, integrity ok, inventory coverage all empty/zero. Relations 164 total / 161 active / 69 verified / 92 seeds / 3 superseded. Sources 106 / evidence 196 / reviews 170.
- Graph 131 works / 355 edges / 562 reasons; prewatch 199, story paths 83/83. Full recursive JSON comparison: six scalar changes only (edge 180 reference/weak -> core/very strong with Japanese label/note, reason 304 status and fingerprint). Existing policy supplies this metadata; no viewer/policy code changes.
- CRLF-aware whitespace check passes; known generated report newline conventions retained.

## Remaining gates

Independent and ordinary ChatGPT whole-diff reviews, exact-head seven-job CI, normal PR merge, merged-main suite and exact-SHA Pages/HTTPS verification are pending. The whole-work audit remains incomplete.
