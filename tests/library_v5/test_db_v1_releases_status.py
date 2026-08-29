import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


WORK = {
    "work_id": "work-a",
    "release_sort_date": "2020-01-01",
    "release_kind": "theatrical",
    "release_precision": "day",
    "release_source_note": "U.S. theatrical release record.",
    "release_certainty": "confirmed",
    "status": "released",
    "japan_date": "",
    "japan_type": "",
}


class ReleaseStatusSeedTests(unittest.TestCase):
    def test_seed_migration_has_one_primary_release_and_status_per_work(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        releases, statuses = seed_release_rows([WORK])
        self.assertEqual(len(releases), 1)
        self.assertEqual(len(statuses), 1)
        self.assertEqual(releases[0]["work_id"], statuses[0]["work_id"])
        self.assertEqual(releases[0]["verification_status"], "legacy_seed")
        self.assertEqual(releases[0]["release_id"], "release-work-a-primary")
        self.assertEqual(statuses[0]["production_status_assertion_id"], "production-status-work-a-snapshot-2026-08-28")

    def test_seed_mapping_does_not_invent_dates_or_territories(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        work = {
            **WORK,
            "work_id": "work-undated",
            "release_sort_date": "",
            "release_kind": "undated",
            "release_precision": "none",
            "release_source_note": "",
        }
        releases, _ = seed_release_rows([work])
        row = releases[0]
        self.assertEqual(row["release_precision"], "none")
        self.assertEqual(row["release_date"], "")
        self.assertEqual(row["territory"], "unknown")

    def test_seed_output_is_byte_deterministic(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        first = seed_release_rows([WORK])
        second = seed_release_rows([WORK])
        self.assertEqual(first, second)

    def test_japanese_date_is_a_separate_release_without_guessing_territory(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        work = {
            **WORK,
            "work_id": "work-jp",
            "japan_date": "2025-07-25",
            "japan_type": "日本劇場公開",
        }
        releases, _ = seed_release_rows([work])
        self.assertEqual([row["release_id"] for row in releases], ["release-work-jp-jp", "release-work-jp-primary"])
        jp = next(row for row in releases if row["release_id"].endswith("-jp"))
        self.assertEqual(jp["territory"], "JP")
        self.assertEqual(jp["release_date"], "2025-07-25")
        self.assertEqual(jp["release_precision"], "day")
        self.assertEqual(jp["release_kind"], "theatrical")

    def test_status_and_release_kind_mapping_is_explicit(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        rows = [
            {**WORK, "work_id": "announced", "status": "announced/upcoming", "release_kind": "home-video"},
            {**WORK, "work_id": "unknown", "status": "delayed", "release_kind": "unclassified"},
        ]
        releases, statuses = seed_release_rows(rows)
        by_work_release = {row["work_id"]: row for row in releases if row["release_id"].endswith("-primary")}
        by_work_status = {row["work_id"]: row for row in statuses}
        self.assertEqual(by_work_release["announced"]["release_kind"], "home_video")
        self.assertEqual(by_work_status["announced"]["status"], "announced")
        self.assertEqual(by_work_release["unknown"]["release_kind"], "other")
        self.assertIn("unclassified", by_work_release["unknown"]["notes"])
        self.assertEqual(by_work_status["unknown"]["status"], "unknown")
        self.assertIn("delayed", by_work_status["unknown"]["notes"])

    def test_dates_only_accept_iso_year_month_or_day_without_guessing(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        rows = [
            {**WORK, "work_id": "year", "release_sort_date": "2020", "release_precision": "year"},
            {**WORK, "work_id": "month", "release_sort_date": "2020-01", "release_precision": "month"},
            {**WORK, "work_id": "invalid", "release_sort_date": "2020/01/01", "release_precision": "day"},
        ]
        releases, _ = seed_release_rows(rows)
        by_work = {row["work_id"]: row for row in releases}
        self.assertEqual((by_work["year"]["release_date"], by_work["year"]["release_precision"]), ("2020", "year"))
        self.assertEqual((by_work["month"]["release_date"], by_work["month"]["release_precision"]), ("2020-01", "month"))
        self.assertEqual((by_work["invalid"]["release_date"], by_work["invalid"]["release_precision"]), ("", "none"))

    def test_write_seed_outputs_only_writes_requested_candidate_directory(self):
        from scripts.library_v5.migrate_releases_status import write_seed_outputs

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = root / "data" / "library"
            library.mkdir(parents=True)
            works = library / "works.csv"
            works.write_text(
                "work_id,release_sort_date,release_kind,release_precision,release_source_note,release_certainty,status,japan_date,japan_type\n"
                "work-a,2020-01-01,theatrical,day,U.S. record.,confirmed,released,,\n",
                encoding="utf-8",
            )
            canonical_releases = library / "releases.csv"
            canonical_statuses = library / "production_status_assertions.csv"
            canonical_releases.write_text("release_id,work_id\n", encoding="utf-8")
            canonical_statuses.write_text("production_status_assertion_id,work_id\n", encoding="utf-8")
            before = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (works, canonical_releases, canonical_statuses)
            }

            result = write_seed_outputs(root, root / "data" / "migration" / "normalized-releases-status")
            self.assertEqual(result["work_count"], 1)
            self.assertEqual(result["release_count"], 1)
            self.assertEqual(result["status_count"], 1)
            self.assertEqual(
                {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (works, canonical_releases, canonical_statuses)},
                before,
            )
            self.assertTrue((root / "data/migration/normalized-releases-status/releases.csv").exists())
            summary = json.loads((root / "data/migration/normalized-releases-status/summary.json").read_text(encoding="utf-8"))
            with works.open(encoding="utf-8", newline="") as handle:
                original_row = dict(next(csv.DictReader(handle)))
            self.assertEqual(summary["work_rows"], [original_row])

    def test_seed_rows_reject_missing_or_duplicate_work_ids(self):
        from scripts.library_v5.migrate_releases_status import seed_release_rows

        with self.assertRaises(ValueError):
            seed_release_rows([{**WORK, "work_id": ""}])
        with self.assertRaises(ValueError):
            seed_release_rows([WORK, WORK])


if __name__ == "__main__":
    unittest.main()
