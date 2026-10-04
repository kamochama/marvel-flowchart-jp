# Wave021 execution and review ledger

Base: `5e44ae2402816c9101034f3198d4d1571a64f7c3` (PR107). Scope is the three status-only story continuations named in the Wave021 plan. The all-work audit remains open.

## Source rulings

- [Disney / Marvel production brief](https://lumiere-a.akamaihd.net/v1/documents/the_falcon_and_the_winter_soldier_production_brief_fina_875edcc9.pdf), printed p.2: series follows Endgame and is rooted in Steve presenting Sam the shield. Supports the complete existing Endgame → FATWS note. No new shield event/chronology assertion.
- [Sony original Homecoming ABOUT synopsis](https://www.sonypictures.com/movies/spidermanhomecoming): Civil War debut and experience with the Avengers precede Peter returning home. Supports the existing Civil War → Homecoming note, not formal Avengers membership. The later FAQ is not the evidence used.
- [Disney July 12 2024 teaser article](https://thewaltdisneycompany.com/news/captain-america-brave-new-world-teaser-trailer/) and [February 13 2025 producer interview](https://thewaltdisneycompany.com/news/captain-america-brave-new-world-producer-interview/): Sam's FATWS finale Captain America mantle and continuing Sam story support FATWS → Brave New World. Existing strong/probable fields are retained, not upgraded.
- Main agent independently read these sources. Ordinary non-Work ChatGPT reviewed the source plan in [the continuing audit conversation](https://chatgpt.com/c/6ac1bb97-6934-83ee-acee-9aedada32826), ruling all three PROMOTE, recommending four sources/four evidence/three reviews and preserving the exclusions in the plan.

## Fresh verification

- Exact provenance/unchanged-tuple regression observed RED on all three legacy statuses before writes; GREEN afterward. Focused provenance/audit/content checks: 19 tests OK.
- Initial full suite failed two inventory checks: it ran before the derived graph rebuild (three stale reason statuses) and the observed-count fixture still recorded 69 verified/92 seeds. Rebuilding removed the stale-status failure; only the count mismatch remained. Update the observed fixture to 72/89, preserving all direction/projection/provenance assertions. Final suite: 625 tests OK, six environment-gated skips, 26.886 seconds.
- Two ordinary builds succeeded; audit/content issues 0, protected canonical CSV and persistent review hashes unchanged by build; flowchart/reason/edge and logical DB manifest hashes repeat exactly.
- Strict CSV shapes valid; SQLite FK rows 0, integrity `ok`; both independent inventories have empty/zero structural/provenance coverage failures.
- Relations: 164 total / 161 active / 72 verified / 89 seeds / 3 superseded. Sources 110 / evidence 200 / reviews 173. Graph: 131 works / 355 edges / 562 reasons, prewatch 199, story paths 83/83.
- Recursive full JSON comparison has exactly 16 scalar differences: three reason verification statuses; existing edge-policy importance/importance_ja/importance_note/strength on those three pairs (reference/weak → recommended/strong); logical fingerprint. No list, key, endpoint, reason ID, node, character, tier policy or viewer change. Public impact: these three existing story links now qualify as recommended through existing policy.
- CRLF-aware `git diff --check` passes. User files in the parent checkout untouched.

## Pending integration gates

Independent full-diff review, ordinary ChatGPT implementation review, exact-head seven-job CI, normal PR merge, merged-main verification and exact-SHA Pages/public checks remain pending. No claim of all-work closure is made.
