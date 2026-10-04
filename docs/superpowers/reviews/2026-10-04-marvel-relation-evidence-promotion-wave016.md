# Wave016 review and dispositions

Base: `bb982ad495caf16c789c6935c4ba8586caf1a68e`.

## Source decisions

- Promote `work-relation-the-defenders-2017-luke-cage-s2-2018-story-link`: [Marvel's Season 2 announcement](https://www.marvel.com/articles/tv-shows/marvel-s-luke-cage-moves-always-forward-with-season-2), published 2016-12-05, explicitly places Luke's second-season return after his Defenders appearance. This is an editorial/story continuation, not proof of a specific causal event. `story_link` is the library's controlled vocabulary, not a quotation from Marvel.
- Defer `work-relation-the-defenders-2017-iron-fist-s2-2018-story-link`: [Marvel's Season 2 announcement](https://www.marvel.com/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-marvel-s-iron-fist) describes Danny protecting his city but does not identify Defenders as the antecedent. The Disney+ episode description similarly identifies Chinatown protection only. No inference from a shared character or date order.
- Defer `work-relation-the-defenders-2017-jessica-jones-s2-2018-story-link`: [Marvel's Season 2 announcement](https://www.marvel.com/amp/articles/tv-shows/marvel-netflix-announce-release-date-for-second-season-of-critically-acclaimed-marvel-s-jessica-jones) describes unfinished business but does not directly establish the Defenders -> Season 2 story link. No qualifying relation-specific primary support found in this bounded search; this is not proof that none exists.

Deferred facts remain unchanged as `legacy_seed`; this does not delete their current graph connections. Additional source research may reopen them later.

## Minimal change

One existing relation changes verification status only. One official source, one exact-fact primary evidence row, and one `legacy_seed -> source_verified` review transition are added. No changes to relation ID, endpoints, kind, strength, continuity scope, certainty, or notes. No viewer, release/status, appearance/identity, event, transition, or chronology changes.

## Verification so far

- New regression: RED at the verification-status assertion before canonical edits; GREEN after exact provenance was added.
- Full bundled-Python suite: 621 tests, OK, 6 environment-gated browser skips.
- Build: audit/content-audit issues 0; 131 works / 355 edges / 562 reasons, prewatch 199, story paths 83/83.
- Explicit relation inventory: 164 total, 161 active, 66 verified, 95 seeds, 3 superseded; coverage failures empty/0.
- Hosted Chrome jobs, ordinary ChatGPT review, and integration/Pages gates remain pending. This is not yet a published completion record.
