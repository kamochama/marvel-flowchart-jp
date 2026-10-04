# Browser audit bounded teardown

## Boundary

- Base: `67aaf37670a0c16e335528eaa332a259db700594` (PR110 integrated).
- Branch: `codex/browser-audit-bounded-teardown`.
- Ordinary ChatGPT approved this bounded repair before implementation.
- Only mobile-shell/publication-order runner lifecycle and regression tests change.
- No UI, canonical CSV, evidence/review ledger, graph, Phase6 runner, workflow,
  assertion, retry-count or outer watchdog changes.
- The historical PR110 240-second timeout location/cause was not established.
  This repair addresses independently demonstrated shutdown weaknesses; it does
  not claim to have identified or reproduced that historical timeout.

## Contract

1. Ignore unused Chrome stderr; create an isolated POSIX process group.
2. Kill that original group even after its parent exits. On Windows, terminate
   the live tree with taskkill `/T /F`, hidden and with a five-second timeout.
3. Bound parent exit waiting to five seconds and clear its timer on exit.
4. Remove the unique Chrome profile with at most three retries / 50ms delay.
   A retained profile is a diagnostic, not a UI semantic failure.
5. Uncertain/failed tree termination is a failure, never a silent success.
   Tag teardown failures as fatal at both existing launch/audit retry boundaries;
   do not start a new browser while the previous tree's isolation is unknown.
   Report the known PID and retained profile instead of claiming it stopped.
6. Stop Chrome before the fixture server; close the server even if stop fails.
7. Record lifecycle stages on stderr. Flush final JSON before explicit exit,
   including infrastructure failures, without increasing retries/watchdogs.

## Regression evidence

- Before implementation, each runner failed the missing-infrastructure JSON
  and permanent profile cleanup error regressions (four failing subcases).
- Real descendant heartbeat is confirmed live before calling the actual
  runner `stopChrome`, then checked stopped afterwards; profile removal is
  checked separately. Windows parent-live cases already passed before repair.
- Parent-exited process-group regression is POSIX-only; Windows skips it.
- Permanent filesystem and OS tree-kill errors are injected only at the OS
  boundary. The fixture executes the runner's actual functions, not copies.
- Independent/ordinary ChatGPT review found the original retry layers could
  hide a termination failure. Added RED: two retry subcases performed a second
  attempt. GREEN now requires both actual retry controllers to propagate fatal
  teardown without accepting a hypothetical successful second attempt.
- Tests also verify known parent/descendant PID state (Linux zombies are exited)
  and Chrome-stop/profile-remove stage ordering, not heartbeat alone.
- Six lifecycle tests pass locally, one POSIX-only skip. The primary runs use
  elevated execution for Windows taskkill; sandbox-only taskkill is denied and
  correctly fails rather than being recorded as a success.
- Final corrected full suite: 634 tests, seven skips, 33.389 seconds.
- Corrected real Chrome mobile-shell/publication-order/Phase6: three PASS,
  25.050 seconds; publication cards=131, failures=0, syntheticEdges=0.
- Two ordinary builds preserve SHA256 of all 21 canonical CSVs, the review
  ledger, graph JSON and index.html exactly; protected tracked diff is empty.
- Build: audit/content audit zero; 131 works, 356 edges, 563 reasons,
  199 prewatch edges, 83 story paths; tracked canonical/HTML/graph unchanged.

## Integration gates

Independent full-diff review, ordinary ChatGPT full-diff
review, all seven CI jobs, normal PR merge and exact-HEAD Pages verification
remain required. Source research for the all-work audit remains a separate
unfinished batch and is not promoted or marked complete by this repair.
