# Wave022 execution and review ledger

Base: `7b26a71ee1b140288b967ae8f5ab4654ea0c632a` (PR108 integrated). This batch promotes only the verification status of First Avenger → Agent Carter one-shot, Civil War → Black Widow, and Endgame → Hawkeye. Full tuples and notes are unchanged; the all-work connection audit remains open.

## Verified locally

- Exact-fact regression observed three legacy-status failures before edits and passed after the three status promotions. Three official source registrations, three primary evidence rows, and three explicit review transitions were added.
- Full suite: 626 tests, OK, six environment-gated skips, 27.056 seconds.
- Two builds reproduce identical flowchart, edge, reason, and logical DB manifest hashes; protected canonical inputs and persistent reviews remain unchanged by the builds.
- Changed CSVs have exact header-width rows. A broader check encountered an existing empty trailing row at line 271 of `release_status_inventory.csv`; HEAD and working copy contain the same row, and this unrelated file was not changed.
- Audit/content issues 0, SQLite foreign-key rows 0, integrity `ok`. Explicit inventory has no missing provenance, projection mismatch, or reason orphan.
- Relations: 164 total, 75 verified, 86 seeds, three superseded. Sources 113, evidence 203, reviews 176. Graph: 131 works, 355 edges, 562 reasons; prewatch 199, reproduced story paths 83/83.
- Full recursive flowchart comparison: exactly 16 scalar differences, comprising three reason statuses, four existing recommendation metadata fields on each of the same three edges, and the logical fingerprint. No endpoints, IDs, nodes, characters, list lengths, viewer implementation, or export policy changed. Existing export policy now classifies these three supported pairs as recommended/strong instead of reference/weak.
- CRLF-aware `git diff --check` passes.

## Integration gates still pending

Independent full-diff review, ordinary non-Work ChatGPT implementation review, exact-head seven-job CI, normal PR merge, and merged-main/Pages/public verification. Local test success is not production publication or whole-work audit completion.

## Previous batch integration

PR108 / Wave021 merged normally at `7b26a71ee1b140288b967ae8f5ab4654ea0c632a`. All seven CI jobs passed on reviewed head `d36f857318211ac96c3195afc254049d3c838368`; transient publication/mobile harness timeouts were independently reproduced successfully and rerun on the unchanged head. Pages run `37206369366` succeeded on the merged SHA, both public checks returned HTTP 200, and the public flowchart SHA256 matched the deployed payload (`0A7B43A0D451828CD9B1B8F16DCBE99524E2D306A2ABFAFE8A4ED8E82B884C44`). Fresh merged-main suite: 625 tests OK, six skips. Both independent and ordinary ChatGPT full-diff reviews approved; no global completeness claim was made.
