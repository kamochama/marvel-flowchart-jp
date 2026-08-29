# Marvel Library DB v1 Release Evidence Promotion Batch 003 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote exactly one existing U.S. theatrical release fact for *Avengers: Secret Wars* to `source_verified` using Marvel's official movie listing, without promoting its production-status snapshot or inventing a Japanese row.

**Architecture:** Add one qualifying `primary` evidence row and one auditable `legacy_seed -> source_verified` review transition for the existing `releases.csv` fact. Preserve the stable release ID, work metadata, announced status, date, territory, and graph policy. The release fact remains separate from the production-status assertion; no work relation, event, transition, or graph edge is changed.

**Tech Stack:** Python 3.13 bundled Codex runtime, `csv`, `hashlib`, `json`, `unittest`, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md`, with release/status constraints in `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md`.

## Global Constraints

- `data/library/` remains the human-auditable canonical source of truth; SQLite and `data/derived/` are generated products.
- A `source_verified` fact requires qualifying `primary` or `supporting` evidence and a consistent persistent review history.
- Preserve existing primary keys and IDs; do not rewrite `works.csv`, release dates, release kinds, territories, or graph policy.
- The sole target is `release-avengers-secret-wars-2027-12-17-primary`.
- Target fields remain `US`, `theatrical`, `2027-12-17`, `day`, `announced`, and `confirmed`; only verification status and notes change.
- Use existing source `marvel-movies-current-v4` (`https://www.marvel.com/movies/`), which explicitly lists Secret Wars with the 2027-12-17 date.
- Do not promote `production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28`; it remains `legacy_seed`.
- No Japanese Secret Wars release row exists; do not create one or infer a territory/date from another row.
- Do not add or remove a work relation, event, transition, appearance, alias, membership, possession, or credit.
- Use TDD: write the failing regression test, run it RED, make the smallest canonical/evidence/review change, then run it GREEN and execute full verification.
- Ordinary builds must not mutate canonical CSVs or persistent review ledgers; generated audit/DB outputs are disposable except the tracked flowchart fingerprint update.

---

### Task 1: Add the RED contract for the bounded promotion

**Files:**
- Create: `tests/library_v5/test_release_status_evidence_promotion_batch003.py`

**Interfaces:**
- The test reads repository CSVs with `csv.DictReader` and checks exact target, evidence, and review IDs.
- The test never calls the network and never mutates canonical files.

- [x] **Step 1: Write the failing test**

```python
import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "release-avengers-secret-wars-2027-12-17-primary"
EVIDENCE_ID = "evidence-release-avengers-secret-wars-2027-12-17-primary"
REVIEW_ID = "review-2026-08-29-release-avengers-secret-wars-2027-12-17-primary"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseEvidencePromotionBatch003Tests(unittest.TestCase):
    def test_only_secret_wars_primary_is_added_to_promoted_release_set(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        promoted = {
            release_id
            for release_id, row in releases.items()
            if row["verification_status"] == "source_verified"
        }
        expected_existing = {
            "release-avengers-doomsday-2026-12-18-primary",
            "release-spider-man-beyond-the-spider-verse-tba-primary",
            "release-visionquest-2026-10-14-primary",
            "release-spider-man-brand-new-day-2026-07-31-primary",
        }
        self.assertEqual(promoted, expected_existing | {TARGET})
        self.assertEqual(releases[TARGET]["territory"], "US")
        self.assertEqual(releases[TARGET]["release_kind"], "theatrical")
        self.assertEqual(releases[TARGET]["release_date"], "2027-12-17")
        self.assertEqual(releases[TARGET]["release_precision"], "day")
        self.assertEqual(releases[TARGET]["status"], "announced")
        self.assertEqual(releases[TARGET]["certainty"], "confirmed")
        self.assertEqual(releases[TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", releases[TARGET]["notes"])

    def test_secret_wars_release_has_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "releases.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "marvel-movies-current-v4")
        self.assertEqual(ev["evidence_role"], "primary")
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "releases.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_secret_wars_status_snapshot_remains_legacy_seed(self):
        statuses = {
            row["production_status_assertion_id"]: row
            for row in _rows("data/library/production_status_assertions.csv")
        }
        snapshot = statuses["production-status-avengers-secret-wars-2027-12-17-snapshot-2026-08-28"]
        self.assertEqual(snapshot["verification_status"], "legacy_seed")


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the focused test and verify RED**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest tests.library_v5.test_release_status_evidence_promotion_batch003 -v
```

Expected result: the target status/evidence/review assertions fail because Secret Wars is still `legacy_seed`; the status-snapshot assertion passes.

---

### Task 2: Install the single evidence-backed review transition

**Files:**
- Modify: `data/library/releases.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`
- Create: `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch003.json`

**Interfaces:**
- The release row keeps its existing ID and all release/status semantics; change only `verification_status` and notes.
- The evidence row uses `fact_table=releases.csv`, the exact target fact ID, source `marvel-movies-current-v4`, and `evidence_role=primary`.
- The review row records `legacy_seed` to `source_verified`, action `verified_source`, and exactly one evidence ID.
- The applied record contains deterministic row counts and SHA-256 hashes of the three canonical inputs after the write.

- [x] **Step 1: Update only the target release status and note**

Change the target row's verification fields to:

```text
verification_status=source_verified
notes=U.S. theatrical release date verified against Marvel's official movie listing; announced release fields and day precision retained.
```

- [x] **Step 2: Append the exact primary evidence row**

```text
evidence-release-avengers-secret-wars-2027-12-17-primary,releases.csv,release-avengers-secret-wars-2027-12-17-primary,marvel-movies-current-v4,primary,"Marvel's official movie listing states that Avengers: Secret Wars will be released on 2027-12-17 in the U.S. theatrical release schedule.",2026-08-29
```

- [x] **Step 3: Append the exact review row**

```text
review-2026-08-29-release-avengers-secret-wars-2027-12-17-primary,releases.csv,release-avengers-secret-wars-2027-12-17-primary,legacy_seed,source_verified,verified_source,evidence-release-avengers-secret-wars-2027-12-17-primary,2026-08-29,"Promotes the existing U.S. theatrical Secret Wars release fact from legacy_seed after checking Marvel's official movie listing; the production-status snapshot remains legacy_seed and no Japanese row is inferred."
```

- [x] **Step 4: Write the applied record and run strict CSV shape checks**

Write `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch003.json` with sorted keys and two-space indentation. Record 138 release rows before and after, 131 production-status rows, the exact evidence/review/source IDs, and SHA-256 values for `releases.csv`, `evidence.csv`, and `reviews.csv`. Run a strict `csv.reader` shape scan and quote complete notes fields containing commas.

---

### Task 3: Verify audit, graph compatibility, and deterministic build

**Files:**
- Modify: `tests/library_v5/test_release_status_evidence_promotion_batch001.py` and `tests/library_v5/test_release_status_evidence_promotion_batch002.py` to extend their cumulative promoted set with the batch003 target while retaining each earlier batch's exact evidence/review assertions.
- Test: `tests/library_v5/test_release_status_evidence_promotion_batch003.py`

- [x] **Step 1: Run focused tests and verify GREEN**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_release_status_evidence_promotion_batch001 tests.library_v5.test_release_status_evidence_promotion_batch002 tests.library_v5.test_release_status_evidence_promotion_batch003 -v
```

- [x] **Step 2: Run the exact full bundled-Python suite**

```powershell
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
```

The suite must pass without deleting or weakening existing regression coverage.

- [x] **Step 3: Run the deterministic DB build**

```powershell
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Confirm audit issues and content-audit issues are zero, SQLite integrity/FK checks are clean, and compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, `prewatch_edges=199`, and story paths `83/83`. The tracked `flowchart.json` may change only in `generated_from.logical_fingerprint`; its nodes, edges, reasons, and characters payload must remain identical. Remove only known generated audit/DB/cache outputs after inspection.

- [ ] **Step 4: Inspect, commit, push, and open the PR**

```powershell
git diff --check
git diff --stat
git add data/library/releases.csv data/library/evidence.csv data/content_audit/reviews.csv data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch003.json data/derived/flowchart.json tests/library_v5/test_release_status_evidence_promotion_batch001.py tests/library_v5/test_release_status_evidence_promotion_batch002.py tests/library_v5/test_release_status_evidence_promotion_batch003.py docs/superpowers/plans/2026-08-29-marvel-library-db-v1-release-status-evidence-promotion-batch003.md
git commit -m "audit: promote Secret Wars release fact"
git push -u origin codex/release-status-audit-batch003
```

Create a PR against `main`, wait for CI, and report the evidence URL, tests, build counts, and deferred status work. Do not merge or publish without explicit authorization for this batch.
