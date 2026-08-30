"""Seed normalized release and production-status facts from canonical works metadata.

This migration deliberately writes only candidate files under the caller-provided
output directory.  Installing those candidates into ``data/library`` remains an
audited, explicit step outside this module.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Mapping, Sequence


RELEASE_FIELDS = [
    "release_id",
    "work_id",
    "territory",
    "release_kind",
    "release_date",
    "release_precision",
    "status",
    "certainty",
    "verification_status",
    "notes",
]
STATUS_FIELDS = [
    "production_status_assertion_id",
    "work_id",
    "status",
    "asserted_at",
    "certainty",
    "verification_status",
    "notes",
]

_RELEASE_KINDS = {
    "theatrical",
    "streaming",
    "broadcast",
    "festival",
    "re_release",
    "special",
    "series_start",
    "imax_series_start",
    "undated",
}
_RELEASE_KIND_MAP = {
    "home-video": "home_video",
    "imax-series-start": "imax_series_start",
    "series-start": "series_start",
}
_PRECISIONS = {"day", "month", "year"}
_ISO_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_ISO_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_ISO_YEAR = re.compile(r"^(\d{4})$")
_US_SOURCE = re.compile(r"(?<![A-Za-z])(?:U\.S\.|US)(?![A-Za-z])", re.IGNORECASE)


def _value(row: Mapping[str, str], key: str) -> str:
    value = row.get(key, "")
    return "" if value is None else str(value).strip()


def _iso_date(value: str) -> str:
    """Return an ISO year/month/day value only when its shape and calendar are valid."""
    value = value.strip()
    if _ISO_DAY.fullmatch(value):
        try:
            year, month, day = (int(part) for part in value.split("-"))
            date(year, month, day)
        except ValueError:
            return ""
        return value
    if _ISO_MONTH.fullmatch(value):
        year, month = (int(part) for part in value.split("-"))
        if not 1 <= month <= 12:
            return ""
        try:
            date(year, month, 1)
        except ValueError:
            return ""
        return value
    if _ISO_YEAR.fullmatch(value):
        try:
            date(int(value), 1, 1)
        except ValueError:
            return ""
        return value
    return ""


def _release_kind(value: str) -> tuple[str, str]:
    original = value.strip()
    if original in _RELEASE_KINDS:
        return original, ""
    mapped = _RELEASE_KIND_MAP.get(original)
    if mapped is not None:
        return mapped, ""
    return "other", f"Original release_kind={original!r} was mapped to other."


def _status(value: str) -> tuple[str, str]:
    original = value.strip()
    lowered = original.lower()
    if lowered.startswith("released"):
        return "released", ""
    if lowered.startswith("announced"):
        return "announced", ""
    return "unknown", f"Original works.status={original!r} was mapped to unknown."


def _certainty(value: str) -> str:
    lowered = value.strip().lower()
    if lowered.startswith("confirmed"):
        return "confirmed"
    if lowered.startswith("probable"):
        return "probable"
    if lowered.startswith("uncertain"):
        return "uncertain"
    return "unknown"


def _precision(raw_precision: str, parsed_date: str) -> str:
    if not parsed_date:
        return "none"
    precision = raw_precision.strip().lower()
    if precision in _PRECISIONS:
        return precision
    return "none"


def _territory(source_note: str) -> str:
    return "US" if _US_SOURCE.search(source_note.strip()) else "unknown"


def _join_notes(*notes: str) -> str:
    return " ".join(note.strip() for note in notes if note and note.strip())


def _release_row(work: Mapping[str, str], *, suffix: str, date_source: str, territory: str) -> dict[str, str]:
    work_id = _value(work, "work_id")
    raw_date = _value(work, date_source)
    parsed_date = _iso_date(raw_date)
    release_kind, kind_note = _release_kind(_value(work, "release_kind"))
    precision = _precision(_value(work, "release_precision"), parsed_date)
    status, status_note = _status(_value(work, "status"))
    date_note = ""
    if raw_date and not parsed_date:
        date_note = f"Original {date_source}={raw_date!r} was not copied because it is not an ISO YYYY-MM-DD, YYYY-MM, or YYYY value."
    if suffix == "jp":
        base_note = "Migrated from works.csv japan_date metadata as a legacy seed; evidence-backed Japanese release audit remains pending."
        if _value(work, "japan_type"):
            base_note += f" Original japan_type={_value(work, 'japan_type')!r}."
    else:
        base_note = "Migrated from works.csv release metadata as a legacy seed; evidence-backed release audit remains pending."
    notes = _join_notes(base_note, kind_note, status_note, date_note)
    return {
        "release_id": f"release-{work_id}-{suffix}",
        "work_id": work_id,
        "territory": territory,
        "release_kind": release_kind,
        "release_date": parsed_date,
        "release_precision": precision,
        "status": status,
        "certainty": _certainty(_value(work, "release_certainty")),
        "verification_status": "legacy_seed",
        "notes": notes,
    }


def _status_row(work: Mapping[str, str], snapshot_date: str) -> dict[str, str]:
    work_id = _value(work, "work_id")
    status, status_note = _status(_value(work, "status"))
    notes = _join_notes(
        "Current status snapshot migrated from works.csv as a legacy seed; asserted_at is the migration review date, not an invented historical milestone.",
        status_note,
    )
    return {
        "production_status_assertion_id": f"production-status-{work_id}-snapshot-{snapshot_date}",
        "work_id": work_id,
        "status": status,
        "asserted_at": snapshot_date,
        "certainty": _certainty(_value(work, "release_certainty")),
        "verification_status": "legacy_seed",
        "notes": notes,
    }


def seed_release_rows(
    work_rows: Sequence[Mapping[str, str]], snapshot_date: str = "2026-08-28"
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Build deterministic release and current-status seed rows from work rows."""
    if not _iso_date(snapshot_date) or len(snapshot_date) != 10:
        raise ValueError(f"snapshot_date must be ISO YYYY-MM-DD: {snapshot_date!r}")

    normalized: list[Mapping[str, str]] = []
    seen: set[str] = set()
    for index, work in enumerate(work_rows, start=1):
        work_id = _value(work, "work_id")
        if not work_id:
            raise ValueError(f"work row {index} lacks work_id")
        if work_id in seen:
            raise ValueError(f"duplicate work_id in work input: {work_id}")
        seen.add(work_id)
        normalized.append(work)

    releases: list[dict[str, str]] = []
    statuses: list[dict[str, str]] = []
    for work in normalized:
        releases.append(
            _release_row(
                work,
                suffix="primary",
                date_source="release_sort_date",
                territory=_territory(_value(work, "release_source_note")),
            )
        )
        japan_date = _value(work, "japan_date")
        if japan_date:
            releases.append(_release_row(work, suffix="jp", date_source="japan_date", territory="JP"))
        statuses.append(_status_row(work, snapshot_date))

    releases.sort(key=lambda row: row["release_id"])
    statuses.sort(key=lambda row: row["production_status_assertion_id"])

    work_ids = {_value(work, "work_id") for work in normalized}
    primary_by_work = {
        work_id: sum(row["work_id"] == work_id and row["release_id"].endswith("-primary") for row in releases)
        for work_id in work_ids
    }
    status_by_work = {
        work_id: sum(row["work_id"] == work_id for row in statuses)
        for work_id in work_ids
    }
    invalid_primary = [work_id for work_id, count in primary_by_work.items() if count != 1]
    invalid_status = [work_id for work_id, count in status_by_work.items() if count != 1]
    if invalid_primary or invalid_status:
        raise ValueError(
            "seed cardinality violation: "
            f"primary releases={sorted(invalid_primary)!r}, statuses={sorted(invalid_status)!r}"
        )
    return releases, statuses


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return [dict(row) for row in reader]


def _write_csv(path: Path, rows: Sequence[Mapping[str, str]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_seed_outputs(repo_root: Path, output_dir: Path, snapshot_date: str = "2026-08-28") -> dict[str, object]:
    """Write candidate CSVs and a deterministic summary, never canonical tables."""
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    source_path = repo_root / "data" / "library" / "works.csv"
    canonical_dir = repo_root / "data" / "library"
    try:
        output_dir.relative_to(canonical_dir)
    except ValueError:
        pass
    else:
        raise ValueError("candidate output directory must not be inside data/library")

    source_rows = _read_csv(source_path)
    releases, statuses = seed_release_rows(source_rows, snapshot_date)
    output_dir.mkdir(parents=True, exist_ok=True)
    releases_path = output_dir / "releases.csv"
    statuses_path = output_dir / "production_status_assertions.csv"
    _write_csv(releases_path, releases, RELEASE_FIELDS)
    _write_csv(statuses_path, statuses, STATUS_FIELDS)

    ordered_source_rows = sorted((dict(row) for row in source_rows), key=lambda row: _value(row, "work_id"))
    summary: dict[str, object] = {
        "snapshot_date": snapshot_date,
        "source_file": "data/library/works.csv",
        "source_sha256": _sha256(source_path),
        "work_count": len(source_rows),
        "release_count": len(releases),
        "status_count": len(statuses),
        "primary_release_count": sum(row["release_id"].endswith("-primary") for row in releases),
        "japanese_release_count": sum(row["release_id"].endswith("-jp") for row in releases),
        "row_counts": {
            "works": len(source_rows),
            "releases": len(releases),
            "production_status_assertions": len(statuses),
        },
        "candidate_files": {
            "releases.csv": {"path": "releases.csv", "sha256": _sha256(releases_path)},
            "production_status_assertions.csv": {
                "path": "production_status_assertions.csv",
                "sha256": _sha256(statuses_path),
            },
        },
        "mapping_rules": [
            "One primary release row and one current production-status snapshot are generated for every work.",
            "A non-empty japan_date generates a separate JP release row; only ISO YYYY-MM-DD, YYYY-MM, or YYYY dates are copied.",
            "Status values beginning with released or announced map to the corresponding enum; all others map to unknown with the original text in notes.",
            "home-video, imax-series-start, and series-start map to home_video, imax_series_start, and series_start; unknown release kinds map to other with the original value in notes.",
            "US territory is assigned only when release_source_note explicitly contains U.S. or US; all other primary rows use unknown.",
            "Every imported fact remains legacy_seed pending a later evidence-backed audit and promotion batch.",
        ],
        "work_rows": ordered_source_rows,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = write_seed_outputs(args.repo_root, args.output_dir)
    # Keep the CLI stream safe for the repository's Windows cp932 consoles;
    # the on-disk summary remains UTF-8 and preserves the original work text.
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
