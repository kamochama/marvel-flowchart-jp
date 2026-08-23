from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from source_model import load_model  # noqa: E402


def main() -> None:
    model = load_model()
    works = model['works']
    edges = model['edges']
    people = model['people_links']
    details = model['work_details']
    ids = [w['id'] for w in works]
    idset = set(ids)
    assert len(works) == len(idset) == 131
    assert len(edges) == 199
    assert len(people) == 155
    assert set(details) == idset
    assert all(e['source'] in idset and e['target'] in idset for e in edges)
    assert all(p['work_id'] in idset for p in people)
    overview_ids = [wid for key in ('infinity','multiverse','tv','fox','animation') for wid in model['overview_groups'][key]]
    assert len(overview_ids) == len(set(overview_ids)) == 76
    assert set(overview_ids) <= idset
    featured = model['featured_route']
    assert set(featured) == {'enabled','targetId','label','eyebrow','description'}
    assert featured['targetId'] in idset
    new_mutants = 'the-new-mutants-2020'
    assert not any(e['source'] == new_mutants or e['target'] == new_mutants for e in edges)
    print('PASS: v5.16 canonical data/config contract')


if __name__ == '__main__':
    main()
