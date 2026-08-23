from __future__ import annotations

import json, re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
a=HTML.index('const NODES=')+len('const NODES='); b=HTML.index('const EDGES=')
NODES=json.loads(HTML[a:b].rstrip().removesuffix(';'))
NODE_IDS={n['id'] for n in NODES}
FUTURE_IDS={n['id'] for n in NODES if n['status']!='released'}


def main():
    manifest=json.loads((ROOT/'src/v515/work-details/manifest.json').read_text(encoding='utf-8'))
    details={}
    assert max((ROOT/'src/v515/work-details'/name).stat().st_size for name in manifest['parts']) <= 12000, 'detail part exceeds connector-safe size'
    for name in manifest['parts']:
        part=json.loads((ROOT/'src/v515/work-details'/name).read_text(encoding='utf-8'))
        overlap=set(details)&set(part)
        assert not overlap, overlap
        details.update(part)
    assert manifest['count']==len(details)
    assert set(details)==NODE_IDS, {'missing':sorted(NODE_IDS-set(details)), 'extra':sorted(set(details)-NODE_IDS)}
    syn=[]; roles=[]
    for wid,d in details.items():
        assert set(d)=={'synopsis_ja','map_role_ja'}, wid
        s=d['synopsis_ja'].strip(); r=d['map_role_ja'].strip()
        assert 35 <= len(s) <= 260, (wid,'synopsis',len(s),s)
        assert 20 <= len(r) <= 220, (wid,'role',len(r),r)
        assert '<' not in s and '>' not in s and '<' not in r and '>' not in r, wid
        assert '\n' not in s and '\n' not in r, wid
        syn.append(s); roles.append(r)
    assert max(Counter(syn).values()) == 1, 'duplicate synopsis'
    assert max(Counter(roles).values()) <= 3, 'map-role text over-reused'
    for wid in FUTURE_IDS:
        text=details[wid]['synopsis_ja']
        assert any(k in text for k in ['公式', '発表', '詳細', '続編', '公開予定']), (wid,text)
    print(f'PASS: {len(details)}/131 work details; future={len(FUTURE_IDS)}')

if __name__=='__main__': main()
