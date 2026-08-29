from __future__ import annotations

import csv
import json
from pathlib import Path

from .ids import slug_id


def derive_story_path_compat(
    legacy_story_paths: list[dict[str, str]],
    derived_edges: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    explained = {
        ((row.get("source_work_id") or "").strip(), (row.get("target_work_id") or "").strip()): row
        for row in derived_edges
        if (row.get("source_work_id") or "").strip() and (row.get("target_work_id") or "").strip()
    }
    story_paths: list[dict[str, str]] = []
    dispositions: list[dict[str, str]] = []
    for index, row in enumerate(legacy_story_paths, start=1):
        source = (row.get("source_id") or "").strip()
        target = (row.get("target_id") or "").strip()
        pair = (source, target)
        if pair in explained:
            copied = dict(row)
            copied["derived_edge_id"] = explained[pair].get("edge_id", "")
            copied["generation_status"] = "generated_compatibility"
            story_paths.append(copied)
            disposition = "reproduced_from_v5_graph"
            note = "Legacy path pair is explained by the current derived v5 graph."
        else:
            disposition = "unexplained_legacy_path"
            note = "Legacy path pair is not yet explained by current canonical facts; frozen migration history retains the original disposition."
        dispositions.append({
            "legacy_row_id": f"story-path-{index:06d}",
            "path_id": (row.get("path_id") or "").strip(),
            "edge_order": (row.get("edge_order") or "").strip(),
            "source_id": source,
            "target_id": target,
            "legacy_edge_id": (row.get("edge_id") or "").strip(),
            "disposition": disposition,
            "migration_note": note,
        })
    return {"story_paths": story_paths, "dispositions": dispositions}


def derive_prewatch_compat(
    legacy_connections: list[dict[str, str]],
    appearances: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    del appearances
    rows: list[dict[str, str]] = []
    for legacy in legacy_connections:
        tier = (legacy.get("prewatch_tier") or "").strip()
        if not tier or tier == "none":
            continue
        source = (legacy.get("source_id") or "").strip()
        target = (legacy.get("target_id") or "").strip()
        if not source or not target or source == target:
            continue
        rows.append({
            "prewatch_edge_id": slug_id("prewatch", source, target, tier),
            "source_work_id": source,
            "target_work_id": target,
            "tier": tier,
            "reason": (legacy.get("prewatch_reason") or legacy.get("reason") or "").strip(),
            "basis": "legacy_v4_policy_compatibility",
        })
    return sorted(rows, key=lambda r: (r["target_work_id"], r["tier"], r["source_work_id"], r["prewatch_edge_id"]))


def default_flowchart_policy() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "canonical_fact_source": False,
        "left_labels_language": "ja",
        "internal_ids_language": "stable_ascii",
        "default_edge_mode": "combined_all_pairs",
        "default_edge_visibility": "all",
        "default_importance_mode": "reference",
        "view_only_properties": [
            "lane",
            "region",
            "line_visibility",
            "line_opacity",
            "glow",
            "dimming",
            "bundling",
            "crossing_treatment",
            "card_geometry",
        ],
        "principles": {
            "view_may_hide_or_dim_fact": True,
            "view_may_not_delete_canonical_fact": True,
            "distinct_work_pairs_remain_distinct_logical_edges": True,
            "user_facing_lane_labels_are_japanese": True,
        },
        "reason_kind_rules": {
            "explicit_relation": {
                "label_ja": "明示的な作品関係",
                "label_en": "explicit work relation",
                "render_class": "solid",
                "strength_thresholds": {
                    "very strong": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["confirmed"],
                        "notes_any": ["direct", "sequel", "crossover"],
                    },
                    "strong": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["confirmed", "probable"],
                    },
                    "moderate": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["uncertain", "unknown"],
                    },
                    "weak": {"verification_statuses": ["conflicted", "legacy_seed"]},
                },
                "importance_thresholds": {
                    "core": {"strengths": ["very strong"], "notes_any": ["direct", "sequel"]},
                    "recommended": {"strengths": ["strong"]},
                    "reference": {"strengths": ["moderate", "weak"]},
                },
                "importance_ja": {
                    "core": "中核",
                    "recommended": "推奨",
                    "reference": "参照",
                },
                "importance_notes_ja": {
                    "core": "直接の続編・物語上の直接関係として中核となる接続。",
                    "recommended": "根拠のある作品関係として視聴順の理解を助ける接続。",
                    "reference": "補助的または不確実性を含む参照用の接続。",
                },
            },
            "shared_entity": {
                "label_ja": "共有キャラクター／エンティティ",
                "label_en": "shared character/entity",
                "render_class": "dashed",
                "strength_thresholds": {
                    "strong": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["confirmed"],
                    },
                    "moderate": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["probable", "uncertain", "unknown"],
                    },
                    "weak": {
                        "verification_statuses": ["conflicted", "legacy_seed"],
                        "certainty_values": ["unknown"],
                    },
                },
                "importance_thresholds": {
                    "recommended": {"strengths": ["strong"]},
                    "reference": {"strengths": ["moderate", "weak"]},
                },
                "importance_ja": {"recommended": "推奨", "reference": "参照"},
                "importance_notes_ja": {
                    "recommended": "同一エンティティの確認済み出演に基づく補助接続。",
                    "reference": "共有エンティティを示す参照用の接続。",
                },
            },
            "multiverse_transition": {
                "label_ja": "マルチバース遷移",
                "label_en": "multiverse transition",
                "render_class": "crossing",
                "strength_thresholds": {
                    "strong": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["confirmed", "probable"],
                    },
                    "moderate": {
                        "verification_statuses": ["source_verified"],
                        "certainty_values": ["uncertain", "unknown"],
                    },
                    "weak": {"verification_statuses": ["conflicted", "legacy_seed"]},
                },
                "importance_thresholds": {
                    "recommended": {"strengths": ["strong"]},
                    "reference": {"strengths": ["moderate", "weak"]},
                },
                "importance_ja": {"recommended": "推奨", "reference": "参照"},
                "importance_notes_ja": {
                    "recommended": "検証済みの遷移事実を示す接続。",
                    "reference": "遷移の不確実性を保った参照用の接続。",
                },
            },
            "fallback": {
                "label_ja": "関連接続",
                "label_en": "related connection",
                "render_class": "dotted",
                "strength_thresholds": {"weak": {}},
                "importance_thresholds": {"reference": {"strengths": ["weak"]}},
                "importance_ja": {"reference": "参照"},
                "importance_notes_ja": {"reference": "保守的な参照用の接続。"},
            },
        },
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_compatibility_outputs(repo_root: Path) -> dict[str, int]:
    legacy_story = _read_csv(repo_root / "data" / "story_paths.csv")
    derived_edges = _read_csv(repo_root / "data" / "derived" / "work_edges_all.csv")
    compat = derive_story_path_compat(legacy_story, derived_edges)
    prewatch = derive_prewatch_compat(
        _read_csv(repo_root / "data" / "connections.csv"),
        _read_csv(repo_root / "data" / "library" / "appearances.csv"),
    )

    derived = repo_root / "data" / "derived"
    view = repo_root / "views" / "flowchart"

    story_fields = list(legacy_story[0].keys()) + ["derived_edge_id", "generation_status"] if legacy_story else ["path_id", "source_id", "target_id", "derived_edge_id", "generation_status"]
    _write_csv(derived / "story_paths.csv", compat["story_paths"], story_fields)
    _write_csv(derived / "prewatch_edges.csv", prewatch, ["prewatch_edge_id", "source_work_id", "target_work_id", "tier", "reason", "basis"])

    view.mkdir(parents=True, exist_ok=True)
    (view / "policy.json").write_text(json.dumps(default_flowchart_policy(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme = """# Flowchart view configuration\n\nThis directory contains presentation policy only. Canonical Marvel facts live under `data/library/`.\n\n- User-facing lane and region labels are Japanese.\n- Edge visibility, opacity, glow, dimming, bundling, crossings, and geometry are view concerns.\n- Hiding or dimming an edge never deletes the underlying canonical fact.\n"""
    (view / "README.md").write_text(readme, encoding="utf-8")

    return {
        "story_paths_reproduced": len(compat["story_paths"]),
        "story_path_dispositions_observed": len(compat["dispositions"]),
        "prewatch_edges": len(prewatch),
    }
