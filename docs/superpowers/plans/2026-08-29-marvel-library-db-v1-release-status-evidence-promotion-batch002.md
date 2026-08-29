# Marvel Library DB v1 Release/Status Evidence Promotion Batch 002 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote exactly one existing U.S. theatrical release fact for *Spider-Man: Brand New Day* to `source_verified` using the official Sony Pictures Japan announcement, without promoting its Japanese row or production-status snapshot.

**Architecture:** Add one qualifying `primary` evidence row and one auditable `legacy_seed -> source_verified` review transition for the existing `releases.csv` fact. Preserve the stable release ID, work metadata, date, territory, graph exports, and all other release/status rows. The batch is intentionally smaller than a work-level status migration because the source establishes the release announcement but does not by itself provide a separate historical production-status assertion.

**Tech Stack:** Python 3.13 bundled Codex runtime, `csv`, `hashlib`, `json`, `unittest`, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` (sections 4.1, 4.10, 5, 7, 10 Phase 2, 12, and 13), with release/status constraints in `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md`.

## Global Constraints

- `data/library/` remains the human-auditable canonical source of truth; SQLite and `data/derived/` are generated products.
- A `source_verified` fact requires qualifying `primary` or `supporting` evidence and a consistent persistent review history.
- Preserve existing primary keys and IDs; do not rewrite `works.csv`, release dates, release kinds, territories, or graph policy.
- A release fact describes one territory/kind/date assertion and must not create a work-to-work edge.
- Do not infer the Japanese date from the Japanese prose `2026年7月31日`; the `-jp` row remains nullable with `release_precision=none`.
- Do not promote `production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28`; its snapshot remains `legacy_seed`.
- Ordinary builds must not mutate canonical CSVs or `data/content_audit/reviews.csv`; generated audit/DB outputs are disposable.
- Use TDD: write the failing regression test, run it RED, make the smallest canonical/evidence/review change, then run it GREEN and execute full verification.
- The sole target is `release-spider-man-brand-new-day-2026-07-31-primary`.
- Evidence source is the existing `sony-bnd-2026-07-03` source row (`https://www.sonypictures.jp/corp/press/2026-07-03`), whose official announcement states the 7/31 simultaneous release and separately labels the U.S. release date.
- Do not add or remove a work relation, event, transition, appearance, alias, membership, possession, or credit.

---

### Task 1: Add the RED contract for the bounded promotion

**Files:**
- Create: `tests/library_v5/test_release_status_evidence_promotion_batch002.py`

**Interfaces:**
- The test reads repository CSVs with `csv.DictReader` and checks exact target, evidence, and review IDs.
- The test never calls the network and never mutates canonical files.

- [x] **Step 1: Write the failing test**

```python
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TARGET = "release-spider-man-brand-new-day-2026-07-31-primary"
EVIDENCE_ID = "evidence-release-spider-man-brand-new-day-2026-07-31-primary"
REVIEW_ID = "review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary"


def _rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseStatusEvidencePromotionBatch002Tests(unittest.TestCase):
    def test_only_brand_new_day_primary_is_added_to_promoted_release_set(self):
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
        }
        self.assertEqual(promoted, expected_existing | {TARGET})
        self.assertEqual(releases[TARGET]["territory"], "US")
        self.assertEqual(releases[TARGET]["release_date"], "2026-07-31")
        self.assertEqual(releases[TARGET]["release_precision"], "day")
        self.assertEqual(releases[TARGET]["verification_status"], "source_verified")
        self.assertNotIn("legacy seed", releases[TARGET]["notes"])

    def test_brand_new_day_release_has_primary_evidence_and_review_transition(self):
        evidence = {row["evidence_id"]: row for row in _rows("data/library/evidence.csv")}
        reviews = {row["review_id"]: row for row in _rows("data/content_audit/reviews.csv")}
        ev = evidence[EVIDENCE_ID]
        self.assertEqual(ev["fact_table"], "releases.csv")
        self.assertEqual(ev["fact_id"], TARGET)
        self.assertEqual(ev["source_id"], "sony-bnd-2026-07-03")
        self.assertEqual(ev["evidence_role"], "primary")
        review = reviews[REVIEW_ID]
        self.assertEqual(review["fact_table"], "releases.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_japanese_release_and_status_snapshot_remain_legacy_seed(self):
        releases = {row["release_id"]: row for row in _rows("data/library/releases.csv")}
        statuses = {row["production_status_assertion_id"]: row for row in _rows("data/library/production_status_assertions.csv")}
        jp = releases["release-spider-man-brand-new-day-2026-07-31-jp"]
        self.assertEqual(jp["verification_status"], "legacy_seed")
        self.assertEqual(jp["release_date"], "")
        snapshot = statuses["production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"]
        self.assertEqual(snapshot["verification_status"], "legacy_seed")


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the focused test and verify RED**

Run from this worktree root:

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest tests.library_v5.test_release_status_evidence_promotion_batch002 -v
```

Expected result: the first two tests fail because the target is still `legacy_seed` and has no release-specific evidence/review pair. The third test passes and protects the intentionally deferred rows.

---

### Task 2: Install the single evidence-backed review transition

**Files:**
- Modify: `data/library/releases.csv`
- Modify: `data/library/evidence.csv`
- Modify: `data/content_audit/reviews.csv`
- Create: `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch002.json`

**Interfaces:**
- The target release row keeps its ID, work ID, `US` territory, `theatrical` kind, `2026-07-31` date, day precision, released status, and confirmed certainty. Only its verification status and notes change.
- The evidence row uses `fact_table=releases.csv`, the exact target fact ID, source `sony-bnd-2026-07-03`, and `evidence_role=primary`.
- The review row records `legacy_seed` to `source_verified`, action `verified_source`, and exactly one evidence ID.
- The applied record contains deterministic row counts and SHA-256 hashes of the three canonical inputs after the write.

- [x] **Step 1: Update only the target release status and note**

Change only the target row in `data/library/releases.csv`:

```text
release-spider-man-brand-new-day-2026-07-31-primary -> verification_status=source_verified
notes=U.S. theatrical release date verified against Sony Pictures Japan's official announcement; migrated release fields and day precision retained.
```

Do not alter the `-jp` row, any status snapshot, or any other release row.

- [x] **Step 2: Append the exact primary evidence row**

```text
evidence-release-spider-man-brand-new-day-2026-07-31-primary,releases.csv,release-spider-man-brand-new-day-2026-07-31-primary,sony-bnd-2026-07-03,primary,"Sony Pictures Japan's official announcement states that Spider-Man: Brand New Day has a simultaneous U.S./Japan theatrical release on July 31, 2026 and separately lists the U.S. release date.",2026-08-29
```

- [x] **Step 3: Append the exact review row**

```text
review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary,releases.csv,release-spider-man-brand-new-day-2026-07-31-primary,legacy_seed,source_verified,verified_source,evidence-release-spider-man-brand-new-day-2026-07-31-primary,2026-08-29,"Promotes the existing U.S. theatrical release fact from legacy_seed after checking Sony Pictures Japan's official announcement; the Japanese release row and production-status snapshot remain legacy_seed."
```

- [x] **Step 4: Write the applied record and run strict CSV shape checks**

Write `data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch002.json` with sorted keys and two-space indentation:

```json
{
  "batch_id": "2026-08-29-release-status-evidence-promotion-batch002",
  "evidence_ids": ["evidence-release-spider-man-brand-new-day-2026-07-31-primary"],
  "fact_table": "releases.csv",
  "post_write_sha256": {},
  "production_status_row_count": 131,
  "promoted_fact_ids": ["release-spider-man-brand-new-day-2026-07-31-primary"],
  "release_row_count_after": 138,
  "release_row_count_before": 138,
  "review_ids": ["review-2026-08-29-release-spider-man-brand-new-day-2026-07-31-primary"],
  "source_ids": ["sony-bnd-2026-07-03"],
  "verification_scope": "Only the Brand New Day U.S. primary release fact is source_verified in this batch; all other release/status facts remain at their prior verification status."
}
```

Populate `post_write_sha256` from the actual bytes of `data/library/releases.csv`, `data/library/evidence.csv`, and `data/content_audit/reviews.csv`. Then run a strict `csv.reader` shape scan that rejects every row whose field count differs from its header; quote complete notes fields containing commas.

---

### Task 3: Verify audit, graph compatibility, and deterministic build

**Files:**
- Test: `tests/library_v5/test_release_status_evidence_promotion_batch002.py`
- Inspect: the three canonical CSVs and the applied record

- [x] **Step 1: Run the focused test and verify GREEN**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_release_status_evidence_promotion_batch002 -v
```

- [x] **Step 2: Run the exact full bundled-Python suite**

```powershell
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
```

The suite must pass without weakening an existing regression test.

- [x] **Step 3: Run the deterministic DB build**

```powershell
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Confirm audit issues and content-audit issues are zero, the SQLite integrity/FK checks are clean, and graph compatibility remains `work_edges_all=361`, `work_pair_reasons=569`, `prewatch_edges=199`, and `story_paths_reproduced=83/83`. Remove only known generated outputs after inspection.

- [x] **Step 4: Inspect the diff and commit the bounded batch**

```powershell
git diff --check
git diff --stat
git diff -- data/library/releases.csv data/library/evidence.csv data/content_audit/reviews.csv data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch002.json tests/library_v5/test_release_status_evidence_promotion_batch002.py
git add data/library/releases.csv data/library/evidence.csv data/content_audit/reviews.csv data/content_audit/applied/2026-08-29-release-status-evidence-promotion-batch002.json data/derived/flowchart.json tests/library_v5/test_release_status_evidence_promotion_batch001.py tests/library_v5/test_release_status_evidence_promotion_batch002.py docs/superpowers/plans/2026-08-29-marvel-library-db-v1-release-status-evidence-promotion-batch002.md
git commit -m "audit: promote Brand New Day release fact"
```

The cumulative regression contract in the existing batch001 test now expects the three previously promoted releases plus this batch's single target; it still asserts that every other release and all status snapshots remain `legacy_seed`. The tracked flowchart artifact changes only its logical fingerprint because canonical release content changed; edge, reason, and compatibility counts remain unchanged.

---

### Task 4: Review and integration gate

- [ ] **Step 1: Push the branch and request read-only review**

Push `codex/release-status-audit`, then have a fresh Luna/xhigh reviewer check that only the target release fact was promoted, evidence/review links are exact, and no graph or Japanese-date inference was introduced.

- [ ] **Step 2: Stop at the PR gate**

Create a PR against `main`, wait for CI, and report the batch, evidence URL, tests, build counts, and any deferred candidates. Do not merge or publish without a new explicit merge authorization for this batch.
