# Marvel Library DB v1 Production Status Evidence Promotion Batch 004 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote exactly one existing Brand New Day production-status snapshot to `source_verified` using Sony Pictures Japan's current official movie listing, without changing release-date or Japanese-release facts.

**Architecture:** Preserve the existing status fact ID and its `released` / `2026-08-28` / `confirmed` semantics. Make the existing source URL precise, add one qualifying primary evidence row, and record one auditable `legacy_seed -> source_verified` review transition. Production status remains outside graph derivation.

**Tech Stack:** Bundled Python 3.13, CSV, JSON, SHA-256, unittest, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-marvel-library-db-v1-design.md` and `docs/superpowers/plans/2026-08-28-marvel-library-db-v1-releases-production-status.md`.

## Global Constraints

- Canonical truth stays under `data/library/`; generated SQLite/audit outputs are disposable.
- A `source_verified` fact requires qualifying evidence and a consistent persistent review transition.
- Preserve target ID and fields `released`, `2026-08-28`, and `confirmed`; change only verification status and note.
- Use `sony-bnd-current-2026-08` with precise URL `https://www.sonypictures.jp/movies`; Sony's current listing labels the title `劇場公開中`.
- Keep the BND U.S. release `source_verified`, the JP release `legacy_seed` with blank date, and every other status `legacy_seed`.
- Do not infer a historical Japanese release date or alter graph facts.
- Use RED test, minimal data/evidence/review change, GREEN tests, full verification, then PR.

---

### Task 1: Add the RED contract

**Files:** Create `tests/library_v5/test_production_status_evidence_promotion_batch004.py`.

**Interfaces:** Read CSVs with `csv.DictReader`. Define `TARGET`, `EVIDENCE_ID`, and `REVIEW_ID` exactly as below; assert only TARGET is verified, its status fields are unchanged, evidence/review fields match, and all release rows retain their current statuses.

- [x] **Step 1: Write the failing test**

```python
import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TARGET = "production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"
EVIDENCE_ID = "evidence-production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"
REVIEW_ID = "review-2026-08-30-production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28"


def rows(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ProductionStatusEvidencePromotionBatch004Tests(unittest.TestCase):
    def test_status_is_verified_with_exact_primary_evidence_and_review(self):
        statuses = {row["production_status_assertion_id"]: row for row in rows("data/library/production_status_assertions.csv")}
        target = statuses[TARGET]
        self.assertEqual(target["status"], "released")
        self.assertEqual(target["asserted_at"], "2026-08-28")
        self.assertEqual(target["certainty"], "confirmed")
        self.assertEqual(target["verification_status"], "source_verified")
        evidence = {row["evidence_id"]: row for row in rows("data/library/evidence.csv")}[EVIDENCE_ID]
        self.assertEqual(evidence["fact_table"], "production_status_assertions.csv")
        self.assertEqual(evidence["fact_id"], TARGET)
        self.assertEqual(evidence["source_id"], "sony-bnd-current-2026-08")
        self.assertEqual(evidence["evidence_role"], "primary")
        self.assertEqual(evidence["verified_at"], "2026-08-30")
        review = {row["review_id"]: row for row in rows("data/content_audit/reviews.csv")}[REVIEW_ID]
        self.assertEqual(review["fact_table"], "production_status_assertions.csv")
        self.assertEqual(review["fact_id"], TARGET)
        self.assertEqual(review["previous_verification_status"], "legacy_seed")
        self.assertEqual(review["new_verification_status"], "source_verified")
        self.assertEqual(review["review_action"], "verified_source")
        self.assertEqual(review["evidence_ids"], EVIDENCE_ID)

    def test_release_rows_and_other_statuses_remain_unchanged(self):
        statuses = rows("data/library/production_status_assertions.csv")
        self.assertTrue(all(row["verification_status"] == "legacy_seed" for row in statuses if row["production_status_assertion_id"] != TARGET))
        releases = {row["release_id"]: row for row in rows("data/library/releases.csv")}
        self.assertEqual(releases["release-spider-man-brand-new-day-2026-07-31-primary"]["verification_status"], "source_verified")
        self.assertEqual(releases["release-spider-man-brand-new-day-2026-07-31-jp"]["verification_status"], "legacy_seed")
        self.assertEqual(releases["release-spider-man-brand-new-day-2026-07-31-jp"]["release_date"], "")
```

- [x] **Step 2: Run the focused test and verify RED**

```powershell
$MarvelPython = 'C:\Users\ataka\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $MarvelPython)) { throw "Bundled Python runtime not found: $MarvelPython" }
& $MarvelPython -m unittest tests.library_v5.test_production_status_evidence_promotion_batch004 -v
```

Expected: target status/evidence/review assertions fail because the canonical status is still `legacy_seed`.

---

### Task 2: Install the single evidence-backed transition

**Files:** Modify `data/library/sources.csv`, `data/library/production_status_assertions.csv`, `data/library/evidence.csv`, and `data/content_audit/reviews.csv`; create `data/content_audit/applied/2026-08-30-production-status-evidence-promotion-batch004.json`.

**Interfaces:** Keep source ID `sony-bnd-current-2026-08`; set its URL to `https://www.sonypictures.jp/movies` and checked point to the exact `劇場公開中` listing. Change only the target status verification fields. Append the exact evidence and review rows represented by Task 1. Quote notes fields containing commas. Record 131 status rows, 138 release rows, exact IDs, and SHA-256 hashes for all four changed CSVs.

- [x] **Step 1: Update source and status rows**

```text
sony-bnd-current-2026-08,Brand New Day公開後ストーリー,Sony Pictures Japan,『スパイダーマン：ブランド・ニュー・デイ』を「劇場公開中」と掲載する現行映画一覧,https://www.sonypictures.jp/movies
production-status-spider-man-brand-new-day-2026-07-31-snapshot-2026-08-28,spider-man-brand-new-day-2026-07-31,released,2026-08-28,confirmed,source_verified,Current Sony Pictures Japan movie listing confirms the work is currently in theatrical release; asserted_at remains the audit snapshot date and does not infer a historical Japanese release date.
```

- [x] **Step 2: Append evidence and review rows**

Use the exact `EVIDENCE_ID` and `REVIEW_ID` rows asserted in Task 1, with `verified_at/reviewed_at=2026-08-30`, `evidence_role=primary`, `review_action=verified_source`, and one evidence ID.

- [x] **Step 3: Write applied record and run strict CSV shape/hash checks**

Use two-space JSON indentation. Every CSV row must have exactly its header field count; every recorded hash must match the bytes after writing.

---

### Task 3: Verify and publish the PR

**Files:** Test `tests/library_v5/test_production_status_evidence_promotion_batch004.py`; inspect all changed files.

- [x] **Step 1: Run focused GREEN and the exact full suite**

```powershell
& $MarvelPython -m unittest tests.library_v5.test_production_status_evidence_promotion_batch004 -v
& $MarvelPython -m unittest discover -s tests/library_v5 -p 'test_*.py' -v
```

- [x] **Step 2: Run deterministic DB build**

```powershell
& $MarvelPython -m scripts.library_v5.build --repo-root .
```

Require audit/content-audit issues 0, SQLite/FK/integrity clean, `work_edges_all=361`, `work_pair_reasons=569`, `prewatch_edges=199`, and story paths `83/83`; graph payload remains unchanged.

- [ ] **Step 3: Commit, push, and open PR**

```powershell
git diff --check
git add data/library/sources.csv data/library/production_status_assertions.csv data/library/evidence.csv data/content_audit/reviews.csv data/content_audit/applied/2026-08-30-production-status-evidence-promotion-batch004.json tests/library_v5/test_production_status_evidence_promotion_batch004.py docs/superpowers/plans/2026-08-30-marvel-library-db-v1-production-status-evidence-promotion-batch004.md
git commit -m "audit: verify Brand New Day production status"
git push -u origin codex/production-status-evidence-promotion-batch004
```

Create the PR against `main`, wait for CI, and stop before merge pending explicit integration authorization.
