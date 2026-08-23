from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'src' / 'app'


def main() -> None:
    shell = (APP / 'shell.html').read_text(encoding='utf-8')
    for marker in ('<!--MARVEL_STYLES-->', '<!--MARVEL_OVERVIEW-->', '<!--MARVEL_SCRIPTS-->'):
        assert shell.count(marker) == 1
    forbidden = (
        'const NODES=',
        'const EDGES=',
        'const CHAR_LINKS=',
        'window.FEATURED_ROUTE=Object.freeze(',
        'window.WORK_DETAILS=Object.freeze(',
    )
    assert not any(token in shell for token in forbidden)

    styles = json.loads((APP / 'styles' / 'manifest.json').read_text(encoding='utf-8'))
    runtime = json.loads((APP / 'runtime' / 'manifest.json').read_text(encoding='utf-8'))
    assert styles == ['000-base.css', '010-responsive.css', '020-v515-details.css']
    assert len(runtime) == 15
    assert runtime[0] == '000-core.js'
    assert runtime[-1] == '140-details-v515.js'
    bodies = '\n'.join((APP / 'runtime' / name).read_text(encoding='utf-8') for name in runtime)
    assert not any(token in bodies for token in forbidden)
    print('PASS: v5.16 app source boundaries')


if __name__ == '__main__':
    main()
