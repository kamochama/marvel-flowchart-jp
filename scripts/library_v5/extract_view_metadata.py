"""Extract and validate presentation-only flowchart metadata.

The checked-in JSON files are the durable source for view metadata.  The HTML
reader in this module is intentionally a one-shot migration aid; ordinary
builds use :func:`load_view_metadata` and never open ``index.html``.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections.abc import Collection, Iterable
from pathlib import Path


class ViewMetadataError(ValueError):
    """Raised when view metadata is absent, malformed, or unsafe to merge."""


_NODE_FIELDS = ("branch", "branch_en", "priority", "chronology")
_CHRONOLOGY_FIELDS = ("lane", "order", "track", "certainty", "note")
_LANE_FIELDS = ("id", "label", "sub", "tone")
_DETAIL_FIELDS = ("synopsis_ja", "map_role_ja")


def _pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ViewMetadataError(f"duplicate object key: {key}")
        result[key] = value
    return result


def _mask_js_non_code(text: str) -> str:
    """Mask comments and quoted literals while retaining source positions."""
    chars = list(text)
    state: str | None = None
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if state == "line_comment":
            if char == "\n":
                state = None
            else:
                chars[index] = " "
            index += 1
            continue
        if state == "block_comment":
            if text.startswith("*/", index):
                chars[index] = chars[index + 1] = " "
                index += 2
                state = None
            else:
                if char != "\n":
                    chars[index] = " "
                index += 1
            continue
        if state in {"'", '"', "`"}:
            chars[index] = " "
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == state:
                state = None
            index += 1
            continue
        if text.startswith("//", index):
            chars[index] = chars[index + 1] = " "
            index += 2
            state = "line_comment"
            continue
        if text.startswith("/*", index):
            chars[index] = chars[index + 1] = " "
            index += 2
            state = "block_comment"
            continue
        if char in {"'", '"', "`"}:
            chars[index] = " "
            state = char
        index += 1
    return "".join(chars)


def _marker_pattern(marker: str) -> re.Pattern[str]:
    if marker.startswith("const "):
        name = marker.split(None, 1)[1]
        return re.compile(rf"\bconst\s+{re.escape(name)}\s*=")
    if marker == "window.WORK_DETAILS=Object.freeze(":
        return re.compile(r"\bwindow\s*\.\s*WORK_DETAILS\s*=")
    raise ViewMetadataError(f"unsupported marker: {marker}")


def _skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _object_freeze_open(text: str, index: int) -> int | None:
    match = re.match(r"Object\s*\.\s*freeze\s*\(", text[index:])
    return index + match.end() if match else None


def _marked_json(text: str, marker: str, *, expected: str) -> object:
    marker_pattern = _marker_pattern(marker)
    all_matches = list(marker_pattern.finditer(text))
    if not all_matches:
        raise ViewMetadataError(f"missing marker: {marker}")
    if len(all_matches) != 1:
        raise ViewMetadataError(f"duplicate marker: {marker}")
    code_matches = list(marker_pattern.finditer(_mask_js_non_code(text)))
    if not code_matches:
        raise ViewMetadataError(f"marker is inside a comment or quoted literal: {marker}")
    if len(code_matches) != 1:
        raise ViewMetadataError(f"duplicate executable marker: {marker}")

    assignment = code_matches[0]
    cursor = _skip_whitespace(text, assignment.end())
    requires_freeze = marker != "const NODES"
    if requires_freeze:
        frozen_cursor = _object_freeze_open(text, cursor)
        if frozen_cursor is None:
            raise ViewMetadataError(f"expected Object.freeze assignment after marker: {marker}")
        cursor = _skip_whitespace(text, frozen_cursor)
    elif _object_freeze_open(text, cursor) is not None:
        cursor = _skip_whitespace(text, _object_freeze_open(text, cursor) or cursor)
    opener = "[" if expected == "array" else "{"
    if cursor >= len(text) or text[cursor] != opener:
        raise ViewMetadataError(f"{marker} payload must begin with JSON {expected} after its assignment")
    start = cursor

    stack: list[str] = []
    in_string = False
    escaped = False
    end: int | None = None
    matching = {"[": "]", "{": "}"}
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
        elif char in matching:
            stack.append(char)
        elif char in ("]", "}"):
            if not stack or matching[stack[-1]] != char:
                raise ViewMetadataError(f"malformed JSON {expected} for {marker}")
            stack.pop()
            if not stack:
                end = index + 1
                break
    if end is None or in_string or stack:
        raise ViewMetadataError(f"unterminated JSON {expected} for {marker}")
    if requires_freeze and not text[end:].lstrip().startswith(")"):
        raise ViewMetadataError(f"malformed Object.freeze wrapper for {marker}")

    try:
        value = json.loads(text[start:end], object_pairs_hook=_pairs_without_duplicates)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ViewMetadataError(f"invalid JSON {expected} for {marker}: {exc}") from exc
    if expected == "array" and not isinstance(value, list):
        raise ViewMetadataError(f"{marker} must be an array")
    if expected == "object" and not isinstance(value, dict):
        raise ViewMetadataError(f"{marker} must be an object")
    return value


def _string(value: object, *, field: str, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ViewMetadataError(f"{context} requires non-empty string {field}")
    return value


def _exact_fields(value: dict[str, object], fields: Iterable[str], *, context: str) -> None:
    expected = set(fields)
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ViewMetadataError(f"{context} fields mismatch: missing={missing!r} extra={extra!r}")


def _validate_lanes(raw_lanes: object) -> list[dict[str, str]]:
    if not isinstance(raw_lanes, list) or any(not isinstance(row, dict) for row in raw_lanes):
        raise ViewMetadataError("chronology lanes must be an array of objects")
    lanes: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_lanes, start=1):
        assert isinstance(raw, dict)
        _exact_fields(raw, _LANE_FIELDS, context=f"chronology lane {index}")
        lane_id = _string(raw["id"], field="id", context=f"chronology lane {index}")
        if lane_id in seen:
            raise ViewMetadataError(f"duplicate chronology lane id: {lane_id}")
        seen.add(lane_id)
        lanes.append({field: _string(raw[field], field=field, context=f"chronology lane {index}") for field in _LANE_FIELDS})
    if not lanes:
        raise ViewMetadataError("chronology lanes must not be empty")
    return lanes


def _validate_chronology(raw: object, work_ids: set[str], lane_ids: set[str]) -> dict[str, dict[str, object]]:
    if not isinstance(raw, dict):
        raise ViewMetadataError("chronology metadata must be an object")
    actual_ids = set(raw)
    unknown = sorted(actual_ids - work_ids)
    if unknown:
        raise ViewMetadataError(f"unknown chronology work ID(s): {unknown!r}")
    result: dict[str, dict[str, object]] = {}
    seen_orders: set[tuple[str, int]] = set()
    for work_id in sorted(raw):
        value = raw[work_id]
        if not isinstance(value, dict):
            raise ViewMetadataError(f"chronology metadata for {work_id} must be an object")
        _exact_fields(value, _CHRONOLOGY_FIELDS, context=f"chronology metadata {work_id}")
        lane = _string(value["lane"], field="lane", context=f"chronology metadata {work_id}")
        if lane not in lane_ids:
            raise ViewMetadataError(f"unknown chronology lane {lane!r} for {work_id}")
        order = value["order"]
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise ViewMetadataError(f"chronology metadata {work_id} requires non-negative integer order")
        key = (lane, order)
        if key in seen_orders:
            raise ViewMetadataError(f"duplicate chronology lane/order: {lane}:{order}")
        seen_orders.add(key)
        result[work_id] = {
            "lane": lane,
            "order": order,
            "track": _string(value["track"], field="track", context=f"chronology metadata {work_id}"),
            "certainty": _string(value["certainty"], field="certainty", context=f"chronology metadata {work_id}"),
            "note": _string(value["note"], field="note", context=f"chronology metadata {work_id}"),
        }
    return result


def _validate_node_metadata(raw_nodes: object, chronology: dict[str, dict[str, object]], work_ids: set[str]) -> dict[str, dict[str, object]]:
    if not isinstance(raw_nodes, list) or any(not isinstance(row, dict) for row in raw_nodes):
        raise ViewMetadataError("NODES must be an array of objects")
    result: dict[str, dict[str, object]] = {}
    for index, raw in enumerate(raw_nodes, start=1):
        assert isinstance(raw, dict)
        work_id = raw.get("id")
        if not isinstance(work_id, str) or not work_id.strip():
            raise ViewMetadataError(f"NODES row {index} requires non-empty id")
        if work_id in result:
            raise ViewMetadataError(f"duplicate work ID in NODES: {work_id}")
        if work_id not in work_ids:
            raise ViewMetadataError(f"unknown work ID in NODES: {work_id}")
        result[work_id] = {
            "branch": _string(raw.get("branch"), field="branch", context=f"NODES row {index}"),
            "branch_en": _string(raw.get("branch_en"), field="branch_en", context=f"NODES row {index}"),
            "priority": _string(raw.get("priority"), field="priority", context=f"NODES row {index}"),
            "chronology": chronology.get(work_id),
        }
    actual_ids = set(result)
    if actual_ids != work_ids:
        raise ViewMetadataError(
            f"NODES work ID coverage mismatch: missing={sorted(work_ids - actual_ids)!r} "
            f"extra={sorted(actual_ids - work_ids)!r}"
        )
    return {work_id: result[work_id] for work_id in sorted(result)}


def _validate_details(raw_details: object, work_ids: set[str]) -> dict[str, dict[str, str]]:
    if not isinstance(raw_details, dict):
        raise ViewMetadataError("WORK_DETAILS must be an object")
    actual_ids = set(raw_details)
    unknown = sorted(actual_ids - work_ids)
    missing = sorted(work_ids - actual_ids)
    if unknown:
        raise ViewMetadataError(f"unknown details work ID(s): {unknown!r}")
    if missing:
        raise ViewMetadataError(f"missing details work ID(s): {missing!r}")
    result: dict[str, dict[str, str]] = {}
    for work_id in sorted(raw_details):
        value = raw_details[work_id]
        if not isinstance(value, dict):
            raise ViewMetadataError(f"details for {work_id} must be an object")
        _exact_fields(value, _DETAIL_FIELDS, context=f"details {work_id}")
        result[work_id] = {
            field: _string(value[field], field=field, context=f"details {work_id}")
            for field in _DETAIL_FIELDS
        }
    return result


def extract_view_metadata(html: str, work_ids: Collection[str]) -> dict[str, object]:
    """Extract all presentation metadata from the pre-cutover HTML.

    ``work_ids`` is the authoritative DB ID set.  Every presentation record
    must cover it exactly, so a stale or partial migration cannot silently
    produce an incomplete view.
    """
    authoritative_ids = {str(value) for value in work_ids if str(value).strip()}
    if not authoritative_ids:
        raise ViewMetadataError("authoritative work IDs must not be empty")
    raw_nodes = _marked_json(html, "const NODES", expected="array")
    raw_lanes = _marked_json(html, "const CHRONOLOGY_LANES", expected="array")
    raw_chronology = _marked_json(html, "const CHRONOLOGY_META", expected="object")
    raw_details = _marked_json(html, "window.WORK_DETAILS=Object.freeze(", expected="object")
    lanes = _validate_lanes(raw_lanes)
    chronology = _validate_chronology(raw_chronology, authoritative_ids, {row["id"] for row in lanes})
    node_metadata = _validate_node_metadata(raw_nodes, chronology, authoritative_ids)
    details = _validate_details(raw_details, authoritative_ids)
    return {
        "node_metadata": node_metadata,
        "chronology_lanes": lanes,
        "details": details,
    }


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs_without_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError, ViewMetadataError) as exc:
        raise ViewMetadataError(f"view metadata JSON invalid: {path}") from exc


def _validate_node_view_document(document: object, work_ids: Collection[str], *, path: Path) -> dict[str, object]:
    if not isinstance(document, dict):
        raise ViewMetadataError(f"node view document must be an object: {path}")
    allowed = {"schema_version", "node_metadata", "chronology_lanes"}
    if set(document) != allowed:
        raise ViewMetadataError(f"node view document fields mismatch: {path}")
    if document["schema_version"] != "1":
        raise ViewMetadataError(f"node view schema version mismatch: {path}")
    authoritative_ids = {str(value) for value in work_ids if str(value).strip()}
    lanes = _validate_lanes(document["chronology_lanes"])
    nodes = document["node_metadata"]
    if not isinstance(nodes, dict):
        raise ViewMetadataError(f"node metadata must be an object: {path}")
    if set(nodes) != authoritative_ids:
        raise ViewMetadataError(f"node metadata work ID coverage mismatch: {path}")
    chronology: dict[str, dict[str, object]] = {}
    for work_id, metadata in nodes.items():
        if not isinstance(metadata, dict):
            raise ViewMetadataError(f"node metadata for {work_id} must be an object: {path}")
        _exact_fields(metadata, _NODE_FIELDS, context=f"node metadata {work_id}")
        if metadata["chronology"] is not None:
            chronology[work_id] = metadata["chronology"]  # type: ignore[assignment]
    normalized_chronology = _validate_chronology(chronology, authoritative_ids, {row["id"] for row in lanes})
    normalized: dict[str, dict[str, object]] = {}
    for work_id in sorted(nodes):
        metadata = nodes[work_id]
        assert isinstance(metadata, dict)
        normalized[work_id] = {
            "branch": _string(metadata["branch"], field="branch", context=f"node metadata {work_id}"),
            "branch_en": _string(metadata["branch_en"], field="branch_en", context=f"node metadata {work_id}"),
            "priority": _string(metadata["priority"], field="priority", context=f"node metadata {work_id}"),
            "chronology": normalized_chronology.get(work_id),
        }
    return {"node_metadata": normalized, "chronology_lanes": lanes}


def _validate_details_document(document: object, work_ids: Collection[str], *, path: Path) -> dict[str, object]:
    if not isinstance(document, dict):
        raise ViewMetadataError(f"details document must be an object: {path}")
    allowed = {"schema_version", "details"}
    if set(document) != allowed:
        raise ViewMetadataError(f"details document fields mismatch: {path}")
    if document["schema_version"] != "1":
        raise ViewMetadataError(f"details schema version mismatch: {path}")
    details = _validate_details(document["details"], {str(value) for value in work_ids if str(value).strip()})
    return {"details": details}


def load_view_metadata(repo_root: Path, work_ids: Collection[str]) -> dict[str, object]:
    """Load tracked JSON presentation inputs without consulting HTML.

    A temporary fixture from earlier DB tasks may not include view inputs; in
    that case an empty presentation overlay is retained for compatibility. If
    either file exists, both are required and strictly validated.
    """
    view_root = repo_root.resolve() / "views" / "flowchart"
    node_path = view_root / "node_view.json"
    details_path = view_root / "details.json"
    if not node_path.exists() and not details_path.exists():
        return {"node_metadata": {}, "chronology_lanes": [], "details": {}}
    if not node_path.exists() or not details_path.exists():
        raise ViewMetadataError("flowchart view metadata requires node_view.json and details.json")
    node_doc = _validate_node_view_document(_read_json(node_path), work_ids, path=node_path)
    details_doc = _validate_details_document(_read_json(details_path), work_ids, path=details_path)
    return {
        "node_metadata": node_doc["node_metadata"],
        "chronology_lanes": node_doc["chronology_lanes"],
        "details": details_doc["details"],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_bytes(serialized.encode("utf-8"))


def _work_ids(repo_root: Path) -> list[str]:
    with (repo_root / "data" / "library" / "works.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "work_id" not in reader.fieldnames:
            raise ViewMetadataError("works.csv lacks work_id column")
        result: list[str] = []
        seen: set[str] = set()
        for row in reader:
            work_id = str(row.get("work_id", ""))
            if not work_id.strip() or work_id in seen:
                raise ViewMetadataError(f"works.csv has missing or duplicate work ID: {work_id!r}")
            seen.add(work_id)
            result.append(work_id)
        if not result:
            raise ViewMetadataError("works.csv has no work IDs")
        return result


def write_view_metadata(repo_root: Path) -> dict[str, int]:
    """Perform the one-shot HTML migration and write deterministic UTF-8 JSON."""
    repo_root = repo_root.resolve()
    html_path = repo_root / "index.html"
    if not html_path.exists():
        raise ViewMetadataError(f"index.html not found: {html_path}")
    extracted = extract_view_metadata(html_path.read_text(encoding="utf-8"), _work_ids(repo_root))
    _write_json(
        repo_root / "views" / "flowchart" / "node_view.json",
        {
            "schema_version": "1",
            "node_metadata": extracted["node_metadata"],
            "chronology_lanes": extracted["chronology_lanes"],
        },
    )
    _write_json(
        repo_root / "views" / "flowchart" / "details.json",
        {"schema_version": "1", "details": extracted["details"]},
    )
    return {
        "node_metadata": len(extracted["node_metadata"]),  # type: ignore[arg-type]
        "details": len(extracted["details"]),  # type: ignore[arg-type]
        "chronology_lanes": len(extracted["chronology_lanes"]),  # type: ignore[arg-type]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="One-shot extraction of flowchart presentation metadata from index.html")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true", help="write views/flowchart/node_view.json and details.json")
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required for the extraction CLI")
    print(json.dumps(write_view_metadata(args.repo_root), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
