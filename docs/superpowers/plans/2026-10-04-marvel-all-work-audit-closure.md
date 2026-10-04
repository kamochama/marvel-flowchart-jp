# Marvel all-work connection audit closure plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for integration; use read-only parallel source reviewers. Continue through all tasks under the user's standing authorization, without asking for routine per-wave permission.

**Goal:** Close the approved all-work connection audit with documented, independently reviewed source dispositions and missing-connection checks, not merely a count of promoted relations.

**Architecture:** Keep mechanical projection checks, source verification, missing-line discovery, and public presentation verification separate. Preserve canonical facts during research; apply supported corrections only in small reviewed, tested feature PRs. The final closure report must distinguish unresolved evidence from incomplete investigation.

**Tech Stack:** Bundled Python (`-B`), PowerShell, existing inventory/audit modules, Chrome/CDP, GitHub Actions/Pages, ordinary ChatGPT (not Work).

**Spec:** `docs/superpowers/plans/2026-09-02-marvel-connection-complete-audit.md`, `docs/superpowers/specs/2026-08-27-marvel-library-v5-audit-status-clarification.md`, and `AGENTS.md`.

## Baseline and authorization

- Fresh local and remote main: `5e44ae2402816c9101034f3198d4d1571a64f7c3` (PR #107).
- Observed baseline: 131 works, 355 directed edges, 562 reasons; relations 164 total / 161 active / 69 source_verified / 92 legacy_seed / 3 superseded.
- Existing all-work inventory is a structural/provenance index, not proof of semantic completeness. Its zero coverage failures cannot establish absence of missing story links.
- The user explicitly requests completion of the existing full-work audit. This authorizes continuing bounded correction waves and normal reviewed PR integration; it does not authorize inventing new semantic domains or silently relaxing source requirements.

## Global constraints

- Audit states below are report states, not new canonical `verification_status` values.
- `unreviewed`: exact source audit has not started. `needs-source`: investigation is incomplete. Neither counts toward audit closure.
- `defer`: record the exact claim, inspected primary sources/passages, inadequate support, and a reopen condition. Missing registered evidence alone is not a substantive source audit.
- A completed source investigation reads exact existing provenance and historical reviews, searches the exact title pair on the relevant official studio/Marvel/Disney/Sony/20th sites, checks official press/production notes/episode guides/synopses, and reads relevant passages (including the actual relevant PDF pages). A few generic catalogue pages or an empty search result are not enough; retain `needs-source` when these steps remain unfinished. Record access failures rather than inventing page content.
- `candidate`: primary text supports the exact tuple and factual notes, but no canonical promotion has occurred. Candidate is not retain/source_verified.
- `explicit-conflict`: identify the contradictory claims and their provenance; do not silently rewrite a disputed date, continuity, or identity.
- `superseded`: keep the historical row and review; verify its replacement and derived-pair safety when applicable.
- Do not delete a line because evidence promotion is deferred. Do not turn a comic synopsis, shared performer, catalogue listing, or shared continuity into an independently proven film relation.
- Preserve exact `(fact_table, fact_id)` provenance. Reusing a registered source URL is allowed; borrowing another fact's evidence/review is not.
- Keep viewer changes and canonical changes in separate PRs. Do not use UI filtering or changed derivation policy to hide unresolved semantic problems.
- Count targets are observations, not proof of correctness. New independently supported missing pairs may legitimately change topology in an explicit correction batch.

## Review focus

- Existing-edge coverage does not examine pairs absent from the graph.
- Broad notes may exceed an otherwise supported tuple (the Wave020 Avengers/Iron Man 3 example).
- Upcoming, cancelled, alternate-world, and same-performer cases need distinct referents and temporal snapshots.
- A candidate source can support only part of a claim; source registration does not certify every neighbouring fact.
- Browser exact-set parity validates the implemented policy, not the truth of the canonical input.

## Task 1: Complete the explicit-relation research ledger

Files: read `data/library/{work_relations,sources,evidence}.csv`, `data/content_audit/reviews.csv`; create `docs/superpowers/reviews/2026-10-04-marvel-all-work-audit-progress.md`.

- [x] Fresh-check main and reuse a clean isolated checkout on `codex/all-work-audit-closure`.
- [x] Run existing relation/connection inventories; coverage failures, projection mismatches, reason orphans, and unsupported transition edges are zero.
- [x] Start independent read-only partitions of the 92 sorted seed IDs: 0–30, 31–61, 62–91. Do not edit canonical tables concurrently.
- [ ] Join the returned exact IDs, check duplicate/missing coverage, and independently inspect every source proposed for adoption.
- [ ] For each seed record tuple/notes, checked sources or explicit unfinished status, interpretation, disposition, and next/reopen action. Carry historical defer decisions with their specific scope; do not make them permanent bans on new evidence.
- [ ] Recheck the 69 verified and 3 superseded relations for exact provenance and claim/replacement boundaries. Mechanical evidence presence is necessary but not sufficient.

## Task 2: Integrate supported relation corrections

Files: only the canonical/source/evidence/review/test/generated files named by each separate bounded wave plan.

- [ ] Select related candidates in groups of at most 3–6. A notes rewrite or kind/direction correction must be named explicitly, not presented as status-only.
- [ ] Write an exact-fact regression, observe RED, make the minimum audited change, and observe GREEN. Keep unrelated historical guards and facts unchanged.
- [ ] Run full unit/build verification, strict CSV shape, canonical isolation/determinism, exact provenance, SQLite FK/integrity, and complete diff review.
- [ ] Obtain independent and ordinary ChatGPT reviews of the full branch/base SHAs and diff, all seven browser/CI jobs, then merge normally and verify main/Pages/public HTTPS.
- [ ] Update the research ledger from candidate to integrated only after the corresponding exact-fact PR is merged. Continue to the next wave, not a permission checkpoint.

## Task 3: Check missing links for all works independently of present edges

Files: read all canonical graph-support tables, existing all-work inventories and official work-specific sources; add work-by-work sections to the progress report.

- [ ] Each work-level ledger row records `work_id`, checked predecessor/successor candidates, official sources examined, missing-relation disposition, proposed fact ID if applicable, and reasoning. A negative result is valid only after the source investigation, not by copying the current graph degree.
- [ ] Cover each of the 131 work IDs exactly once, including all zero-degree works. Record independently inspected direct predecessors, lead-ins/aftermaths, crossovers and explicit no-supported-pair dispositions.
- [ ] Search and read qualifying primary text for plausible missing pairs, rather than treating existing edges or franchise-name similarity as an oracle.
- [ ] List proposed absent pairs separately from confirmed omissions. A confirmed omission needs a specific canonical correction proposal and source support.
- [ ] Include risk families: sequel chains, one-shots, TV/film aftermath, Fox revised histories, same-performer variants, and future promotional lists.
- [ ] Apply only confirmed corrections in separate RED→GREEN waves; retain unresolved cases with source-backed defer/conflict reasons.

## Task 4: Close supporting domains without conflating them

Files: existing appearance/identity, continuity/event/transition, chronology, release/status tables and exact provenance, plus separate domain review reports/PRs.

- [ ] Trace every one of the 562 current reasons (or the newly verified live count) to its exact canonical facts; check direction, referent, support completeness and export membership.
- [ ] Re-audit appearance/identity support without same-performer identity inference; independently evaluate continuity fallback versus precise verified traveller anchors.
- [ ] Re-audit continuity/events/transitions without event-occurrence chronology inference or manufactured work pairs.
- [ ] Review chronology as a separate assertion/presentation domain; an empty canonical chronology table is not evidence that public chronology ordering has been source-audited.
- [ ] Revalidate release/status dispositions for current factual snapshots; do not treat historical PR #30 counts as current proof or equate a past announced date with actual release.
- [ ] Make any resulting changes in separate bounded domain PRs with exact evidence/reviews and full verification.

## Task 5: Final closure verification and publication

Files: final all-work report plus handoff/roadmap pointers; no unrelated UI redesign.

- [ ] Ensure no `unreviewed`/unfinished `needs-source` rows remain in the defined audit scope. Formal defer/conflict is allowed only with documented completed investigation and reopen conditions.
- [ ] Report two distinct gates: explicit-relation audit closure (all 164 baseline relations dispositioned, no unfinished research/candidates), and whole-graph semantic closure (also all works, pairs, reasons, supporting domains and absent-pair investigations). The first does not imply the second. Formal documented conflicts may remain; unfinished conflict investigations and open correction proposals may not.
- [ ] Ensure every work, current pair, current reason, supporting canonical fact, and separately investigated absent-pair candidate has an explicit disposition. Report denominators and unfinished counts, not only verified percentage.
- [ ] Re-run full bundled tests/build, deterministic/canonical hashes, audit/content/review integrity, SQLite FK 0 and integrity ok, all six real-Chrome audit families, and `git diff --check`.
- [ ] Ordinary ChatGPT independently reviews the full closure package and confirms that mechanical checks, semantic inspection and remaining uncertainty are clearly distinguished.
- [ ] Complete the normal PR/CI/merge/Pages process and verify deployed main SHA/HTTP 200. Final report states precisely what is resolved and what formally remains deferred/conflicted; never claim source_verified=100% as the completion condition.

## Execution record

2026-10-04: Existing inventory tests 16 OK; isolated baseline full suite 624 tests OK / 6 environment-gated skips (26.903s). Build succeeded with audit/content issues 0, 199 prewatch edges and 83/83 story paths. A sandbox write denial on the isolated generated directory was resolved by rerunning the unchanged normal build with elevated execution; no canonical data was edited. Ordinary ChatGPT closure-plan review completed (1m53s), recommending the two distinct closure gates, a separate missing-line ledger and the explicit investigation protocol above. Its potential source suggestions remain candidates until independently read. Source partitions are in progress. This record is not an audit-completion claim.
