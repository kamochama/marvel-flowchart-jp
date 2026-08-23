from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    manifest = json.loads((ROOT / 'src/baseline/manifest.json').read_text(encoding='utf-8'))
    assert manifest['parts'], 'baseline parts missing'
    assert max(p['bytes'] for p in manifest['parts']) <= 65536
    workflow = (ROOT / '.github/workflows/build-public.yml').read_text(encoding='utf-8')
    for required in [
        'scripts/build_public.py',
        'tests/test_build_roundtrip.py',
        'tests/test_pages_workflow.py',
        'src/**',
        'scripts/**',
    ]:
        assert required in workflow, required
    print('PASS: source layout and build workflow contract')


if __name__ == '__main__':
    main()
