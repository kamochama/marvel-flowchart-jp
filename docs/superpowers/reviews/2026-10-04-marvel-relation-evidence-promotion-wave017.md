# Wave017 review and execution record

Base: `3d61b4e8343be2397a7080273e05cac54c7d1c25` (PR #103 merged; Pages 37172650137 success; merged-main 621 tests OK and HTTPS HTTP 200 verified).

## Decisions

- Promote only `work-relation-spider-man-2-2004-spider-man-3-2007-sequel`. [Sony's work-specific FAQ](https://www.sonypictures.com/movies/spiderman3) explicitly describes the third/final Raimi film continuing the first two and following Spider-Man 2's events. This directly supports the preserved `sequel/story/direct/same_or_intended/confirmed` tuple and `Raimi trilogy.` notes. No character identity, numbered Earth, independent chronology, release/status or event/transition assertion is added.
- Spider-Man (2002) -> Spider-Man 2 is already verified by Wave011 and is unchanged.
- Defer `work-relation-daredevil-s3-2018-daredevil-born-again-s1-2025-sequel`. [Disney's Born Again article](https://thewaltdisneycompany.com/news/daredevil-born-again/) supports series-level Matt/Fisk story continuation and familiar characters, not the exact S3 endpoint. A source auditor recommended promotion by combining that with an old S3 character article; the primary rejected this composition because character overlap plus the last season does not directly establish the exact predecessor tuple. Keep the seed and line intact. This is evidence insufficiency, not a claim that the relation is false.

## TDD and verification

- Baseline: 621 tests OK, 6 gated skips.
- New exact-fact regression observed RED on legacy status before data edits, then GREEN after one source/evidence/review addition and one status-only promotion.
- Full suite initially exposed three historical deferred-state assertions in Wave011/012/013. Ruling: replace only this relation's outdated current-state assertion with its newly verified state and retain all other deferred guards; new Wave017 test requires exact qualifying provenance and unchanged tuple. Historical documents are not rewritten.
- Final suite: 622 tests OK, 6 gated skips.
- Ordinary build: audit/content issues 0, 131 works / 355 edges / 562 reasons, prewatch 199, story paths 83/83.
- Inventory: total 164, active 161, verified 67, seeds 94, superseded 3; all coverage issue arrays empty, projection mismatch and orphan counts 0.
- Canonical/review hashes unchanged across rebuild; all three graph exports deterministic; strict canonical CSV/review shapes valid; SQLite FK 0, integrity `ok`.
- Full JSON structure comparison: six scalar differences only. Existing policy changes the one edge from reference/weak to core/very strong with matching Japanese label/note; matching reason verification status and logical fingerprint change. No topology, viewer or export-policy implementation changes.
- CRLF-aware whitespace check: `git -c core.whitespace=cr-at-eol diff --check`.

## Reviews and integration gate

Independent source audit supports the Sony continuation. Ordinary non-Work ChatGPT plan review supports this bounded promotion and the Daredevil defer, with a caution about historical deferred tests addressed above. Conversation: https://chatgpt.com/c/6ac1bb97-6934-83ee-acee-9aedada32826 .

Full-diff independent and ChatGPT implementation review, all seven hosted jobs, normal PR integration and Pages verification remain pending; do not call this published or the all-work audit complete.
