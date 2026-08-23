from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src' / 'data'
CONFIG = ROOT / 'src' / 'config'
OVERVIEW_KEYS = ('infinity', 'multiverse', 'tv', 'fox', 'animation')
FEATURED_KEYS = {'enabled', 'targetId', 'label', 'eyebrow', 'description'}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _load_work_details() -> dict[str, dict]:
    root = DATA / 'work-details'
    manifest = _load_json(root / 'manifest.json')
    parts = manifest.get('parts', [])
    if not parts:
        raise ValueError('work detail parts missing')
    details: dict[str, dict] = {}
    for name in parts:
        part = _load_json(root / name)
        overlap = set(details) & set(part)
        if overlap:
            raise ValueError(f'duplicate work detail ids: {sorted(overlap)}')
        details.update(part)
    if len(details) != manifest.get('count'):
        raise ValueError('work detail manifest count mismatch')
    return details


def load_model() -> dict:
    works = _load_json(DATA / 'works.json')
    edges = _load_json(DATA / 'edges.json')
    people_links = _load_json(DATA / 'people-links.json')
    work_details = _load_work_details()
    overview_groups = _load_json(CONFIG / 'overview-groups.json')
    group_labels = _load_json(CONFIG / 'group-labels.json')
    featured_route = _load_json(CONFIG / 'featured-route.json')

    ids = [work.get('id') for work in works]
    if any(not wid for wid in ids) or len(ids) != len(set(ids)):
        raise ValueError('duplicate or missing work ids')
    idset = set(ids)

    for edge in edges:
        if edge.get('source') not in idset or edge.get('target') not in idset:
            raise ValueError(f'unknown edge endpoint: {edge}')
    for link in people_links:
        if link.get('work_id') not in idset:
            raise ValueError(f'unknown people-link work id: {link}')
    if set(work_details) != idset:
        missing = sorted(idset - set(work_details))
        extra = sorted(set(work_details) - idset)
        raise ValueError(f'work detail id mismatch: missing={missing} extra={extra}')

    if set(overview_groups) != set(OVERVIEW_KEYS):
        raise ValueError('overview group keys mismatch')
    if set(group_labels) != set(OVERVIEW_KEYS):
        raise ValueError('group label keys mismatch')
    overview_ids = [wid for key in OVERVIEW_KEYS for wid in overview_groups[key]]
    if len(overview_ids) != 76 or len(overview_ids) != len(set(overview_ids)):
        raise ValueError('overview membership must contain 76 unique work ids')
    unknown_overview = sorted(set(overview_ids) - idset)
    if unknown_overview:
        raise ValueError(f'unknown overview ids: {unknown_overview}')

    if set(featured_route) != FEATURED_KEYS:
        raise ValueError('featured-route keys mismatch')
    if featured_route['targetId'] not in idset:
        raise ValueError('featured-route target is not a known work')

    return {
        'works': works,
        'edges': edges,
        'people_links': people_links,
        'work_details': work_details,
        'overview_groups': overview_groups,
        'group_labels': group_labels,
        'featured_route': featured_route,
    }
