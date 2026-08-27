from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Iterable


class LegacyExtractionError(ValueError):
    pass


_CHAR_REQUIRED = ("character", "work_id", "title_ja", "title_en")
_RETURN_REQUIRED = (
    "target_work_id",
    "entity",
    "representative_prior_work_id",
    "evidence",
    "continuity_certainty",
    "source_url",
)


def _extract_json_array_after_marker(text: str, marker: str) -> list[dict[str, object]]:
    marker_index = text.find(marker)
    if marker_index < 0:
        raise LegacyExtractionError(f"missing marker: {marker}")
    equal_index = text.find("=", marker_index + len(marker))
    if equal_index < 0:
        raise LegacyExtractionError(f"missing assignment after marker: {marker}")
    start = text.find("[", equal_index + 1)
    if start < 0:
        raise LegacyExtractionError(f"{marker} is not assigned an array")

    depth = 0
    in_string = False
    escaped = False
    end = None
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise LegacyExtractionError(f"unterminated JSON array for {marker}")

    try:
        value = json.loads(text[start:end])
    except json.JSONDecodeError as exc:
        raise LegacyExtractionError(f"invalid JSON array for {marker}: {exc}") from exc
    if not isinstance(value, list):
        raise LegacyExtractionError(f"{marker} must be an array")
    if any(not isinstance(row, dict) for row in value):
        raise LegacyExtractionError(f"{marker} rows must be objects")
    return value


def extract_char_links(html: str) -> list[dict[str, str]]:
    raw_rows = _extract_json_array_after_marker(html, "CHAR_LINKS")
    result: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for index, raw in enumerate(raw_rows, start=1):
        missing = [field for field in _CHAR_REQUIRED if not str(raw.get(field, "")).strip()]
        if missing:
            raise LegacyExtractionError(
                f"CHAR_LINKS row {index} missing required fields: {', '.join(missing)}"
            )
        key = tuple(str(raw[field]).strip() for field in _CHAR_REQUIRED)
        if key in seen:
            continue
        seen.add(key)
        row = {field: str(raw[field]).strip() for field in _CHAR_REQUIRED}
        row["verification_status"] = "legacy_seed"
        row["legacy_source"] = "index.html:CHAR_LINKS"
        result.append(row)
    return result


def extract_entity_returns(csv_text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    if reader.fieldnames is None or any(field not in reader.fieldnames for field in _RETURN_REQUIRED):
        raise LegacyExtractionError("entity_returns.csv has an unexpected header")

    result: list[dict[str, str]] = []
    for index, raw in enumerate(reader, start=2):
        row = {field: str(raw.get(field, "") or "").strip() for field in _RETURN_REQUIRED}
        if not row["target_work_id"] or not row["entity"]:
            raise LegacyExtractionError(f"entity_returns.csv row {index} lacks target/entity")
        row["verification_status"] = "legacy_seed"
        row["legacy_source"] = "data/entity_returns.csv"
        result.append(row)
    return result


def _write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_legacy_seeds(repo_root: Path) -> dict[str, int]:
    html = (repo_root / "index.html").read_text(encoding="utf-8")
    returns_text = (repo_root / "data" / "entity_returns.csv").read_text(encoding="utf-8")
    char_rows = extract_char_links(html)
    return_rows = extract_entity_returns(returns_text)

    migration = repo_root / "data" / "migration"
    _write_csv(
        migration / "legacy_char_links.csv",
        char_rows,
        list(_CHAR_REQUIRED) + ["verification_status", "legacy_source"],
    )
    _write_csv(
        migration / "legacy_entity_returns.csv",
        return_rows,
        list(_RETURN_REQUIRED) + ["verification_status", "legacy_source"],
    )
    summary = {
        "legacy_char_links_rows": len(char_rows),
        "legacy_entity_returns_rows": len(return_rows),
    }
    (migration / "legacy_extract_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required for the extraction CLI")
    summary = write_legacy_seeds(args.repo_root.resolve())
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
