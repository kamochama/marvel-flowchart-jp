# Marvel Library v5 relation evidence promotion wave012 plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 既存の直接続編関係のうち、公式一次資料が関係の方向と意味を直接支持する3件だけを`legacy_seed`から`source_verified`へ昇格する。

**Architecture:** canonical relation tupleは変更せず、relation-specificな公式source、同一factのprimary evidence、`legacy_seed -> source_verified` review transitionを追加する。derived graphは既存のrelation statusを再投影するだけで、edge/reasonのID・方向・数は変えない。

**Tech Stack:** bundled Python 3、CSV、unittest、既存のDB builder / connectivity audit。

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-v5-audit-status-clarification.md`、`docs/superpowers/plans/2026-09-13-marvel-explicit-relation-audit.md`。

## Global Constraints

- `data/library/work_relations.csv`は対象3行の`verification_status`だけを変更し、relation ID、方向、kind、scope、directness、continuity scope、certainty、notesは保持する。
- `sources.csv`、`evidence.csv`、`reviews.csv`は各対象factについて1行ずつ追加し、`(fact_table, fact_id)`を厳密に一致させる。
- release/status、appearances、identity、chronology、events、transitions、HTML、derived CSVの意味論は変更しない。
- 公式一覧やRelated Moviesだけではなく、対象関係を本文で直接説明する一次資料だけを採用する。
- Iron Man 2→3、Spider-Man 2→3、Blade、旧X-Men、Fantastic Fourは直接性が不足するため今回のwaveから除外し、`legacy_seed`のまま保持する。
- Windowsではbundled PythonをPowerShellの`&` call operatorと`-B`で起動する。

---

### Task 1: RED promotion contract

**Files:**
- Create: `tests/library_v5/test_relation_evidence_promotion_wave012.py`
- Read: `data/library/work_relations.csv`, `data/library/sources.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`

**Interfaces:**
- Consumes: canonical CSVs and existing derived graph files.
- Produces: exact source/evidence/review and unchanged tuple assertions for the three target relations.

- [x] **Step 1: Write the failing test**

  Assert the following target relation IDs, exact tuples, and provenance IDs:

  ```python
  TARGETS = {
      "work-relation-captain-america-the-winter-soldier-2014-captain-america-civil-war-2016-sequel": {
          "source_id": "disney-captain-america-civil-war-third-installment-2016",
          "evidence_id": "evidence-captain-america-winter-soldier-civil-war-third-installment-disney-2016",
          "review_id": "review-2026-09-14-winter-soldier-civil-war-sequel",
          "url": "https://thewaltdisneycompany.com/news/brand-new-trailer-and-posters-released-for-marvels-captain-america-civil-war/",
      },
      "work-relation-thor-the-dark-world-2013-thor-ragnarok-2017-sequel": {
          "source_id": "disney-thor-ragnarok-third-installment-2017",
          "evidence_id": "evidence-thor-dark-world-ragnarok-third-installment-disney-2017",
          "review_id": "review-2026-09-14-thor-dark-world-ragnarok-sequel",
          "url": "https://thewaltdisneycompany.com/app/uploads/2017-asm-transcript.pdf",
      },
      "work-relation-thor-ragnarok-2017-thor-love-and-thunder-2022-sequel": {
          "source_id": "marvel-thor-love-and-thunder-fourth-installment-2022",
          "evidence_id": "evidence-thor-ragnarok-love-and-thunder-fourth-installment-marvel-2022",
          "review_id": "review-2026-09-14-thor-ragnarok-love-and-thunder-sequel",
          "url": "https://www.marvel.com/watch/trailers-and-extras/kevin-feige-says-thor-love-and-thunder-is-more-than-just-ragnarok-2",
      },
  }
  ```

  The test must also assert that each row remains `sequel/story/direct/same_or_intended/confirmed`, that the two deferred sentinel rows `iron-man-2-2010 -> iron-man-3-2013` and `spider-man-2-2004 -> spider-man-3-2007` remain `legacy_seed`, and that graph counts remain `131/355/562`.

- [x] **Step 2: Run the focused test to verify RED**

  ```powershell
  $MarvelPython='C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  & $MarvelPython -B -m unittest tests.library_v5.test_relation_evidence_promotion_wave012 -v
  ```

  Expected: the three new source/evidence/review IDs are absent and the test fails.

---

### Task 2: Add exact provenance and minimal status transitions

**Files:**
- Modify: `data/library/sources.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`
- Modify: `data/library/work_relations.csv`
- Test: `tests/library_v5/test_relation_evidence_promotion_wave012.py`

**Interfaces:**
- Consumes: the three exact relation IDs and URLs from Task 1.
- Produces: one official source, one same-fact primary evidence row, one review transition, and one status-only relation update per target.

- [x] **Step 1: Register the source rows**

  Add the three URLs exactly as declared in `TARGETS`. The checked points must be narrowly scoped:

  - Disney's Civil War announcement calls Civil War the third Captain America installment; this supports the existing Winter Soldier→Civil War relation only.
  - Disney's 2017 shareholder transcript calls Thor: Ragnarok the third Thor installment; this supports the existing Dark World→Ragnarok relation only.
  - Marvel's Kevin Feige page calls Love and Thunder the fourth Thor installment and explicitly frames it as more than “Ragnarok 2”; this supports the existing Ragnarok→Love and Thunder relation only.

- [x] **Step 2: Add one exact primary evidence row per relation**

  Set `fact_table=work_relations.csv`, `fact_id=<relation_id>`, `evidence_role=primary`, and use the matching source ID. Do not reuse appearance, release, or generic movie-list evidence.

- [x] **Step 3: Add one auditable review transition per relation**

  Use `review_action=verified_source`, `from_status=legacy_seed`, `to_status=source_verified`, and reference only the matching evidence ID. Keep any certainty value unchanged.

- [x] **Step 4: Change only the three relation statuses**

  Change `verification_status` from `legacy_seed` to `source_verified` for the three exact rows. Do not rewrite notes or any tuple field.

- [x] **Step 5: Run focused tests to verify GREEN**

  ```powershell
  & $MarvelPython -B -m unittest tests.library_v5.test_relation_evidence_promotion_wave012 -v
  ```

---

### Task 3: Regenerate and audit the derived view

**Files:**
- Modify: generated `data/derived/**` only through the official builder.
- Create: `docs/superpowers/reviews/2026-09-14-marvel-relation-evidence-promotion-wave012.md`

- [x] **Step 1: Run the deterministic build**

  ```powershell
  & $MarvelPython -B -m scripts.library_v5.build --repo-root .
  ```

- [x] **Step 2: Verify topology and audit invariants**

  Confirm audit/content-audit issue counts are zero, SQLite foreign keys are zero, `integrity_check=ok`, graph counts remain `131 works / 355 edges / 562 reasons`, and story paths remain `83/83`. Confirm the three explicit reasons retain their IDs and pairs; only their verification status changes.

- [x] **Step 3: Write the review note**

  Record the three promoted relations, the exact source boundaries, the two deferred sentinel relations and why they remain deferred, all changed-file categories, and the rule that no release/status/event/transition fact was promoted.

---

### Task 4: Full verification and independent review gate

- [x] **Step 1: Run the complete bundled suite**

  ```powershell
  & $MarvelPython -B -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  ```

- [x] **Step 2: Check CSV shape, canonical isolation, and diff hygiene**

  Validate exact header widths for every changed CSV, confirm no release/status/events/transitions/appearance/identity CSV changed, run `git diff --check`, and ensure only known generated paths and `__pycache__` are transient.

- [x] **Step 3: Request read-only ChatGPT review**

  Send the branch SHA, base SHA, complete diff, exact fact-to-evidence/review joins, and full verification results to ordinary ChatGPT. Ask specifically whether the three official pages directly support the existing relation tuples and whether any source is being used to infer unrelated semantics.

- [ ] **Step 4: Commit, push, PR, CI, and merge**

  Commit only after the independent review and local verification are green. Push the feature branch, wait for all required browser/DB CI checks, merge through the normal PR path under standing authorization, and verify `origin/main` plus Pages HTTP 200.

## Completion boundary

This wave does not claim that all 102 deferred relations are correct or incorrect. It only records qualifying evidence for three existing relations. All other legacy rows remain explicit `needs-source` dispositions in the relation inventory.
