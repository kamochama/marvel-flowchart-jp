# Wave016 review and dispositions

Base: `bb982ad495caf16c789c6935c4ba8586caf1a68e`.

## Source decisions

- Promote `work-relation-the-defenders-2017-luke-cage-s2-2018-story-link`: [Marvel's Season 2 announcement](https://www.marvel.com/articles/tv-shows/marvel-s-luke-cage-moves-always-forward-with-season-2), published 2016-12-05, explicitly places Luke's second-season return after his Defenders appearance. This is an editorial/story continuation, not proof of a specific causal event. `story_link` is the library's controlled vocabulary, not a quotation from Marvel.
- Defer `work-relation-the-defenders-2017-iron-fist-s2-2018-story-link`: [Marvel's Season 2 announcement](https://www.marvel.com/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-marvel-s-iron-fist) describes Danny protecting his city but does not identify Defenders as the antecedent. The Disney+ episode description similarly identifies Chinatown protection only. No inference from a shared character or date order.
- Defer `work-relation-the-defenders-2017-jessica-jones-s2-2018-story-link`: [Marvel's Season 2 announcement](https://www.marvel.com/amp/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-critically-acclaimed-marvel-s-jessica-jones) describes unfinished business but does not directly establish the Defenders -> Season 2 story link. No qualifying relation-specific primary support found in this bounded search; this is not proof that none exists.

Deferred facts remain unchanged as `legacy_seed`; this does not delete their current graph connections. Additional source research may reopen them later.

## Minimal change

One existing relation changes verification status only. One official source, one exact-fact primary evidence row, and one `legacy_seed -> source_verified` review transition are added. No changes to relation ID, endpoints, kind, strength, continuity scope, certainty, or notes. No viewer, release/status, appearance/identity, event, transition, or chronology changes.

Canonical `directness=strong` is unchanged. The existing export policy does respond to the verified provenance: the one corresponding edge changes derived `strength` from `weak` to `strong` and `importance` from `reference` to `recommended`, with matching Japanese label/explanation. This can affect the site-proposal presentation of that connection. The export policy and viewer implementation are unchanged; no edge is added or deleted. The logical DB fingerprint and the matching reason's verification status also change. The complete JSON comparison finds only these six scalar differences.

## Verification so far

- New regression: RED at the verification-status assertion before canonical edits; GREEN after exact provenance was added.
- Full bundled-Python suite: 621 tests, OK, 6 environment-gated browser skips.
- Build: audit/content-audit issues 0; 131 works / 355 edges / 562 reasons, prewatch 199, story paths 83/83.
- Explicit relation inventory: 164 total, 161 active, 66 verified, 95 seeds, 3 superseded; coverage failures empty/0.
- Rebuild: canonical hashes unchanged, deterministic graph exports, strict CSV shapes valid, SQLite FK 0 and integrity `ok`.
- Diff whitespace audit uses `git -c core.whitespace=cr-at-eol diff --check` to preserve the existing tracked reports' CRLF format without all-line churn. Known transient build outputs were removed; they are regenerable.
- Independent read-only source/diff review found no Critical/Important issue; its CRLF/transient-output Minor was addressed as above. Deferred neighboring facts stay unchanged.
- Hosted Chrome jobs and integration/Pages gates remain pending. This is not yet a published completion record.

## Ordinary ChatGPT review

The ordinary non-Work review of base `bb982ad` through implementation head `2ba906423173b44a9a96bbc1c73e5a52eb3a36fb` returned semantic LGTM, Critical 0, Important 0, and no blocking Minor. It independently checked the PR and all three official announcements. Its nonblocking wording note is that source `after/following` describes editorial continuation, not exact fictional chronology; the evidence already excludes the latter.

The review is conditional on all required Chrome/CI jobs being GREEN. It does not claim independent reruns of local tests or completed deployment. Review conversation: `https://chatgpt.com/c/6ac1bb97-6934-83ee-acee-9aedada32826`.
