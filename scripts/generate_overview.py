#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V515 = ROOT / 'src' / 'v515'


def _decode_arrays(source: str):
    decoder = json.JSONDecoder()
    a = source.index('const NODES=') + len('const NODES=')
    nodes, _ = decoder.raw_decode(source[a:].lstrip())
    b = source.index('const EDGES=') + len('const EDGES=')
    edges, _ = decoder.raw_decode(source[b:].lstrip())
    return nodes, edges


def _dot_q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _cluster_label(title: str, desc: str, color: str) -> str:
    title = html.escape(title)
    desc = html.escape(desc)
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">'
        f'<TR><TD ALIGN="LEFT"><FONT FACE="Noto Sans CJK JP" POINT-SIZE="20" COLOR="{color}"><B>{title}</B></FONT></TD></TR>'
        f'<TR><TD ALIGN="LEFT"><FONT FACE="Noto Sans CJK JP" POINT-SIZE="12" COLOR="#cbd5e1">{desc}</FONT></TD></TR>'
        '</TABLE>>'
    )


def _edge_style(edge: dict) -> tuple[str, float]:
    strength = edge.get('strength', 'weak')
    if strength == 'very strong': return 'solid', 2.5
    if strength == 'strong': return 'solid', 1.65
    if strength == 'medium': return 'dashed', 1.45
    return 'dotted', 1.25


def render_overview_svg(source: str) -> str:
    nodes, edges = _decode_arrays(source)
    nm = {n['id']: n for n in nodes}
    groups = json.loads((V515 / 'overview-groups.json').read_text(encoding='utf-8'))
    labels = json.loads((V515 / 'group-labels.json').read_text(encoding='utf-8'))
    ids = [wid for key in ['infinity','multiverse','tv','fox','animation'] for wid in groups[key]]
    if len(ids) != 76 or len(set(ids)) != 76:
        raise RuntimeError('overview group membership must contain 76 unique works')
    missing = [wid for wid in ids if wid not in nm]
    if missing:
        raise RuntimeError(f'unknown overview ids: {missing}')
    idset = set(ids)
    internal = [e for e in edges if e['source'] in idset and e['target'] in idset]

    lines = [
        'digraph overview {',
        'graph [rankdir=LR, newrank=true, compound=true, splines=spline, overlap=false, nodesep=0.34, ranksep=0.70, pad=0.28, bgcolor="#0b1020", fontname="Noto Sans CJK JP", fontcolor="white", fontsize=22, labelloc=t, label="マーベル作品相関図 日本版 ① 主要フロー — 76作品 / %d接続"];' % len(internal),
        'node [shape=box, style="rounded,filled", fillcolor="#111827", color="#475569", penwidth=1.3, fontname="Noto Sans CJK JP", fontcolor="#e5e7eb", fontsize=10, margin="0.08,0.05"];',
        'edge [color="#64748b", arrowsize=0.72, fontname="Noto Sans CJK JP"];',
    ]
    for idx, key in enumerate(['infinity','multiverse','tv','fox','animation']):
        meta = labels[key]
        lines += [
            f'subgraph cluster_{idx} {{',
            f'color={_dot_q(meta["color"])}; penwidth=3.0; style="rounded,filled"; fillcolor="#101827"; margin=20; labelloc=t; labeljust=l;',
            f'label={_cluster_label(meta["title"], meta["description"], meta["color"])};',
        ]
        for wid in groups[key]:
            n = nm[wid]
            title = n['title'].replace('\n', ' ')
            label = f'{title}\\n{n["release"]}'
            lines.append(f'{_dot_q(wid)} [label={_dot_q(label)}];')
        lines.append('}')

    for e in internal:
        style, pen = _edge_style(e)
        lines.append(f'{_dot_q(e["source"])} -> {_dot_q(e["target"])} [style={style}, penwidth={pen}];')
    lines.append('}')
    dot = '\n'.join(lines) + '\n'
    proc = subprocess.run(['dot','-Tsvg'], input=dot, text=True, capture_output=True, check=True)
    svg = proc.stdout
    start = svg.index('<svg ')
    end = svg.rindex('</svg>') + len('</svg>')
    svg = svg[start:end]

    edge_map = {(e['source'],e['target']): e for e in internal}
    pattern = re.compile(r'<g id="edge(\d+)" class="edge">\s*<title>(.*?)</title>', re.S)
    def annotate(m: re.Match) -> str:
        raw = html.unescape(m.group(2)).replace('&#45;', '-')
        if '->' not in raw:
            return m.group(0)
        source_id, target_id = raw.split('->', 1)
        e = edge_map.get((source_id,target_id))
        if not e:
            return m.group(0)
        classes = ['edge']
        if e.get('audit_added'): classes.append('audit-added')
        if e.get('fan_verified'): classes.append('fan-verified')
        attrs = [f'id="edge{m.group(1)}"', f'class="{" ".join(classes)}"']
        if e.get('layer'): attrs.append(f'data-layer="{html.escape(str(e["layer"]), quote=True)}"')
        attrs.append(f'data-strength="{html.escape(str(e.get("strength","weak")), quote=True)}"')
        attrs.append(f'data-render="{html.escape(str(e.get("render_class","solid")), quote=True)}"')
        return '<g ' + ' '.join(attrs) + '>\n<title>' + m.group(2) + '</title>'
    svg = pattern.sub(annotate, svg)
    svg = svg.replace('&#45;', '-')
    return svg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', default=str(ROOT/'index.html'))
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    source = Path(args.input).read_text(encoding='utf-8')
    svg = render_overview_svg(source)
    Path(args.output).write_text(svg + '\n', encoding='utf-8')
    print(f'wrote {args.output}: nodes={svg.count("class=\"node\"")} edges={svg.count("class=\"edge")})')


if __name__ == '__main__':
    main()
