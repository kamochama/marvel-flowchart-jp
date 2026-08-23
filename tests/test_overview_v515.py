from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'scripts' / 'build_public.py'
FOX = {
    'x-men-2000','x2-x-men-united-2003','x-men-the-last-stand-2006',
    'x-men-origins-wolverine-2009','x-men-first-class-2011','the-wolverine-2013',
    'x-men-days-of-future-past-2014','deadpool-2016','x-men-apocalypse-2016',
    'logan-2017','deadpool-2-2018','dark-phoenix-2019','the-new-mutants-2020',
}
GROUP_TEXT = [
    'MCU / INFINITY SAGA',
    'アベンジャーズ結成からサノスとの決戦まで',
    'MCU / MULTIVERSE SAGA',
    'エンドゲーム後からマルチバースと次の大型合流へ',
    'DISNEY+ / TV',
    '映画本流と交差するドラマ・配信シリーズ',
    'FOX X-MEN UNIVERSE',
    '旧X-MEN映画・ウルヴァリン・デッドプールをたどる系統',
    'ANIMATION / SPECIAL',
    'アニメーション・スペシャル作品',
]


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'index.html'
        subprocess.run([sys.executable, str(BUILD), '--output', str(out)], cwd=ROOT, check=True)
        html = out.read_text(encoding='utf-8')
        start = html.index('<div id="overview"')
        end = html.index('<div id="mcu"', start)
        overview = html[start:end]

        node_ids = set(re.findall(r'<g[^>]*class="node"[^>]*>\s*<title>([^<]+)</title>', overview))
        assert len(node_ids) == 76, len(node_ids)
        assert FOX <= node_ids, sorted(FOX - node_ids)

        for text in GROUP_TEXT:
            assert text in overview, text

        assert 'font-size="20.00"' in overview
        assert 'stroke-width="3"' in overview
        assert 'fill="#101827"' in overview

        edge_titles = re.findall(r'<g[^>]*class="edge[^\"]*"[^>]*>\s*<title>([^<]+)</title>', overview)
        new_mutants_edges = [e for e in edge_titles if 'the-new-mutants-2020' in e]
        assert new_mutants_edges == [], new_mutants_edges
        print(f'PASS: overview nodes={len(node_ids)} fox={len(FOX)} new-mutants-edges=0')


if __name__ == '__main__':
    main()
