# Marvel Library DB v1 Release/Status Evidence Promotion Batch 001 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote exactly three already-seeded primary release facts to `source_verified` using existing official source records, while leaving all production-status assertions, Japanese release rows, graph derivation, and other seed rows unchanged.

**Architecture:** The batch adds one primary evidence row and one `verified_source` review transition for each selected `releases.csv` fact. The existing release rows keep their stable IDs and dates; only `verification_status`, `evidence.csv`, and `reviews.csv` gain the audited promotion. The SQLite compiler and HTML export consume the same release data as before, and a regression test proves that no release/status row outside the three named facts changes and no work-pair output is manufactured.

**Tech Stack:** Python 3.13 bundled Codex runtime, `csv`, `hashlib`, `unittest`, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` (sections 4.10, 5, 7, 10 Phase 2, 12, and 13), with the release/status boundary in `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md`.

## Global Constraints

- `data/library/` remains the human-auditable canonical source of truth; SQLite and files under `data/derived/` are generated products.
- A `source_verified` fact requires qualifying `primary` or `supporting` evidence and a consistent persistent review history.
- Preserve existing primary keys and IDs; do not rewrite `works.csv`, release dates, territories, or graph policy.
- A release fact describes one territory/kind/date assertion and must not create a work-to-work edge.
- Do not infer a territory, exact date, production milestone, or historical status date when the source does not establish it.
- Ordinary builds must not mutate canonical CSVs or `data/content_audit/reviews.csv`; generated audit/DB outputs are disposable.
- Use TDD: write the failing regression test, run it RED, make the smallest data/audit change, then run it GREEN and execute the full verification surface.
- The batch is limited to these three existing primary release facts:
  - `release-avengers-doomsday-2026-12-18-primary` — source `doomsday-jp`.
  - `release-spider-man-brand-new-day-2026-07-31-primary` — source `sony-bnd-2026-07-03`.
  - `release-spider-man-beyond-the-spider-verse-tba-primary` — source `sony-beyond-2026`.
- Do not promote the matching `production_status_assertions.csv` snapshots, any `-jp` release rows, or any other `legacy_seed` row in this batch.
- Do not add or remove a `work_relation`, event, transition, appearance, alias, membership, possession, or credit.

---

### Task 1: Add the RED contract for the exact promotion set

**Files:**
- Create: `tests/library_v5/test_release_status_evidence_promotion_batch001.py`

**Interfaces:**
- The test reads repository CSVs with `csv.DictReader` and asserts the exact target IDs, evidence IDs, and review IDs listed below.
- The test must not call the network or mutate canonical files.

- [ ] **Step 1: Write the failing test**

  Add this complete test module:

  ```python
  import csv
  from pathlib import Path
  import unittest

  ROOT = Path(__file__).resolve().parents[2]
  TARGETS = {
      "release-avengers-doomsday-2026-12-18-primary": {
          "evidence_id": "evidence-release-avengers-doomsday-2026-12-18-primary",
          "source_id": "doomsday-jp",
          "review_id": "review-2026-08-29-release-avengers-doomsday-2026-12-18-primary",
      },
      "release-spider-man-brand-new-day-2026-07-31-primary": {
          "evidence_id": "evidence-release-spider-man-brand-new-day-2026-07-31-primary",
          "source_id": "sony-bnd-2026-07-03",
          "review_id": "review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary",
      },
      "release-spider-man-beyond-the-spider-verse-tba-primary": {
          "evidence_id": "evidence-release-spider-man-beyond-the-spider-verse-tba-primary",
          "source_id": "sony-beyond-2026",
          "review_id": "review-2026-08-29-release-spider-man-beyond-the-spider-verse-tba-primary",
      },
  }

  def _rows(relative_path):
      with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
          return list(csv.DictReader(handle))


  class ReleaseStatusEvidencePromotionBatch001Tests(unittest.TestCase):
      def test_only_three_named_primary_releases_are_promoted(self):
          releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
          promoted = {
              release_id
              for release_id, row in releases.items()
              if row["verification_status"] == "source_verified"
          }
          self.assertEqual(promoted, set(TARGETS))
          for release_id in TARGETS:
              self.assertEqual(releases[release_id]["verification_status"], "source_verified")

      def test_promoted_releases_have_matching_primary_evidence_and_review(self):
          evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
          reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
          for release_id, expected in TARGETS.items():
              ev = evidence[expected["evidence_id"]]
              self.assertEqual(ev["fact_table"], "releases.csv")
              self.assertEqual(ev["fact_id"], release_id)
              self.assertEqual(ev["source_id"], expected["source_id"])
              self.assertEqual(ev["evidence_role"], "primary")
              review = reviews[expected["review_id"]]
              self.assertEqual(review["fact_table"], "releases.csv")
              self.assertEqual(review["fact_id"], release_id)
              self.assertEqual(review["previous_verification_status"], "legacy_seed")
              self.assertEqual(review["new_verification_status"], "source_verified")
              self.assertEqual(review["review_action"], "verified_source")
              self.assertEqual(review["evidence_ids"], expected["evidence_id"])

      def test_status_snapshots_and_other_release_rows_remain_legacy_seed(self):
          releases = _rows("data/library/releases.csv")
          statuses = _rows("data/library/production_status_assertions.csv")
          self.assertTrue(all(row["verification_status"] == "legacy_seed" for row in statuses))
          self.assertTrue(
              all(
                  row["verification_status"] == "legacy_seed"
                  for row in releases
                  if row["release_id"] not in TARGETS
              )
          )


  if __name__ == "__main__":
      unittest.main()
  ```

- [ ] **Step 2: Run the focused test and verify the intended RED result**

  Run from the repository root:

  ```powershell
  $MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
  & $MarvelPython -m unittest tests.library_v5.test_release_status_evidence_promotion_batch001 -v
  ```

  Expected result: failure in the first two tests because all 269 release/status facts are still `legacy_seed` and none of the three release fact IDs has a release-specific evidence/review pair. The third test may pass; that is acceptable because it protects the non-target rows.

### Task 2: Install the three evidence-backed review transitions

**Files:**
- Modify: `data/library/releases.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`
- Create: `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch001.json`

**Interfaces:**
- The three existing release rows retain all fields except `verification_status`, which changes from `legacy_seed` to `source_verified`.
- Each new evidence row uses `fact_table=releases.csv`, the exact target `fact_id`, `evidence_role=primary`, and the existing source ID shown in Task 1.
- Each new review row records `previous_verification_status=legacy_seed`, `new_verification_status=source_verified`, `review_action=verified_source`, and exactly one evidence ID.
- The applied record is a JSON audit artifact containing the batch ID, target fact IDs, evidence/review IDs, source IDs, pre/post row counts, and SHA-256 hashes of the three canonical inputs after the write.

- [ ] **Step 1: Update only the target release statuses**

  Change only these three `verification_status` cells in `data/library/releases.csv`:

  ```text
  release-avengers-doomsday-2026-12-18-primary -> source_verified
  release-spider-man-brand-new-day-2026-07-31-primary -> source_verified
  release-spider-man-beyond-the-spider-verse-tba-primary -> source_verified
  ```

  Do not alter release dates, kinds, territories, certainty, notes, the `-jp` rows, or any other row.

- [ ] **Step 2: Append the exact evidence rows**

  Append these UTF-8 CSV records; the complete notes fields are quoted because they contain commas:

  ```text
  evidence-release-avengers-doomsday-2026-12-18-primary,releases.csv,release-avengers-doomsday-2026-12-18-primary,doomsday-jp,primary,"Marvel Japan's official Avengers: Doomsday page lists the U.S. theatrical opening date as 2026-12-18.",2026-08-29
  evidence-release-spider-man-brand-new-day-2026-07-31-primary,releases.csv,release-spider-man-brand-new-day-2026-07-31-primary,sony-bnd-2026-07-03,primary,"Sony Pictures Japan's official press record lists the U.S. theatrical opening date as 2026-07-31.",2026-08-29
  evidence-release-spider-man-beyond-the-spider-verse-tba-primary,releases.csv,release-spider-man-beyond-the-spider-verse-tba-primary,sony-beyond-2026,primary,"Sony Group's official release-schedule record lists the U.S. theatrical release date as 2027-06-18.",2026-08-29
  ```

- [ ] **Step 3: Append the exact review rows**

  Append these records to `data/content_audit/reviews.csv`; quote each complete notes field because it contains commas:

  ```text
  review-2026-08-29-release-avengers-doomsday-2026-12-18-primary,releases.csv,release-avengers-doomsday-2026-12-18-primary,legacy_seed,source_verified,verified_source,evidence-release-avengers-doomsday-2026-12-18-primary,2026-08-29,"Promotes the existing U.S. theatrical release fact from legacy_seed after checking the official Marvel Japan release record; no Japanese release row or production-status snapshot is changed."
  review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary,releases.csv,release-spider-man-brand-new-day-2026-07-31-primary,legacy_seed,source_verified,verified_source,evidence-release-spider-man-brand-new-day-2026-07-31-primary,2026-08-29,"Promotes the existing U.S. theatrical release fact from legacy_seed after checking the official Sony Pictures Japan release record; no Japanese release row or production-status snapshot is changed."
  review-2026-08-29-release-spider-man-beyond-the-spider-verse-tba-primary,releases.csv,release-spider-man-beyond-the-spider-verse-tba-primary,legacy_seed,source_verified,verified_source,evidence-release-spider-man-beyond-the-spider-verse-tba-primary,2026-08-29,"Promotes the existing U.S. theatrical release fact from legacy_seed after checking the official Sony Group release-schedule record; the date precision remains day and no production-status snapshot is changed."
  ```

- [ ] **Step 4: Record the applied batch and run strict shape checks**

  Write `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch001.json` from the following deterministic Python construction, so the hashes are the actual post-write SHA-256 digests:

  ```json
  {
    "batch_id": "2026-08-29-release-status-evidence-promotion-batch001",
    "fact_table": "releases.csv",
    "promoted_fact_ids": [
      "release-avengers-doomsday-2026-12-18-primary",
      "release-spider-man-brand-new-day-2026-07-31-primary",
      "release-spider-man-beyond-the-spider-verse-tba-primary"
    ],
    "evidence_ids": [
      "evidence-release-avengers-doomsday-2026-12-18-primary",
      "evidence-release-spider-man-brand-new-day-2026-07-31-primary",
      "evidence-release-spider-man-beyond-the-spider-verse-tba-primary"
    ],
    "review_ids": [
      "review-2026-08-29-release-avengers-doomsday-2026-12-18-primary",
      "review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary",
      "review-2026-08-29-release-spider-man-beyond-the-spider-verse-tba-primary"
    ],
    "source_ids": ["doomsday-jp", "sony-bnd-2026-07-03", "sony-beyond-2026"],
    "release_row_count_before": 138,
    "release_row_count_after": 138,
    "production_status_row_count": 131,
    "verification_scope": "Only the three named primary release facts are source_verified; all other release/status facts remain legacy_seed.",
    "post_write_sha256": {}
  }
  ```

  Before writing the JSON, populate `post_write_sha256` with this executable expression and serialize with sorted keys and two-space indentation:

  ```python
  from hashlib import sha256
  from pathlib import Path

  record["post_write_sha256"] = {
      path: sha256(Path(path).read_bytes()).hexdigest()
      for path in (
          "data/library/releases.csv",
          "data/library/evidence.csv",
          "data/content_audit/reviews.csv",
      )
  }
  Path("data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch001.json").write_text(
      json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
      encoding="utf-8",
  )
  ```

  Run a strict CSV shape scan that rejects any row whose field count differs from its header; do not rely only on `DictReader` dictionary access.

### Task 3: Verify audit, graph compatibility, and deterministic build

**Files:**
- Test: `tests/library_v5/test_release_status_evidence_promotion_batch001.py`
- Inspect: `data/library/releases.csv`, `data/library/evidence.csv`, `data/content_audit/reviews.csv`, `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch001.json`

**Interfaces:**
- Audit must report zero issues, including no `source_verified_without_evidence` and no review-integrity issue.
- The graph compatibility contract is unchanged: `work_edges_all`, `work_pair_reasons`, `prewatch_edges`, and reproduced story paths must equal the pre-batch values.

- [ ] **Step 1: Run the focused test and verify GREEN**

  ```powershell
  & $MarvelPython -m unittest tests.library_v5.test_release_status_evidence_promotion_batch001 -v
  ```

  Expected: all three tests pass.

- [ ] **Step 2: Run the full bundled-Python suite**

  ```powershell
  & $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
  ```

  Expected: zero failures, with the test count reported by the current checkout.

- [ ] **Step 3: Run the ordinary build and inspect the audit summary**

  ```powershell
  & $MarvelPython -m scripts.library_v5.build --repo-root .
  ```

  Confirm `audit_ok:true`, `audit_issue_count:0`, review-integrity issues `0`, SQLite foreign-key rows `0`, and SQLite `integrity_check` equal to `ok`. Confirm the graph compatibility observations remain `work_edges_all=361`, `work_pair_reasons=569`, `prewatch_edges=199`, and `83/83` story paths reproduced.

- [ ] **Step 4: Inspect the diff and clean generated outputs**

  Run `git diff --check` and inspect `git diff -- data/library/releases.csv data/library/evidence.csv data/content_audit/reviews.csv`. Remove only known disposable build outputs and Python `__pycache__` directories; never remove canonical CSVs or `data/content_audit/reviews.csv`.

### Task 4: Commit and hand off the bounded batch

**Files:**
- Commit: the test, three canonical/audit CSV changes, and the applied record.

- [ ] **Step 1: Commit the verified batch**

  ```powershell
  git add tests/library_v5/test_release_status_evidence_promotion_batch001.py data/library/releases.csv data/library/evidence.csv data/content_audit/reviews.csv data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch001.json
  git diff --cached --check
  git commit -m "audit: promote selected release facts"
  ```

- [ ] **Step 2: Re-run status and record the handoff**

  Run `git status --short --branch` and record the commit SHA, test count, build audit summary, and the fact that all non-target release/status rows remain `legacy_seed`. Push a new PR only after the full local verification is green; stop before merging until the user explicitly approves the production integration.

---

## Self-review checklist

- The plan changes one fact table only and names all three fact IDs, evidence IDs, review IDs, and source IDs explicitly.
- The RED test fails against the current all-`legacy_seed` state before any canonical data edit.
- The plan never promotes a production-status snapshot or creates a graph edge from a release fact.
- The only expected row-count change is zero; only three existing release status cells and six audit rows are added.
- Full suite, ordinary build, audit integrity, graph compatibility, and strict CSV shape checks are explicit.
