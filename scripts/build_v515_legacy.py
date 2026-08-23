#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from generate_overview import render_overview_svg

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src' / 'baseline'
V515 = ROOT / 'src' / 'v515'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_baseline() -> bytes:
    manifest = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
    chunks: list[bytes] = []
    for entry in manifest['parts']:
        data = (BASE / entry['path']).read_bytes()
        if len(data) != entry['bytes']:
            raise SystemExit(f"size mismatch: {entry['path']}")
        if sha(data) != entry['sha256']:
            raise SystemExit(f"sha mismatch: {entry['path']}")
        chunks.append(data)
    built = b''.join(chunks)
    if len(built) != manifest['bytes'] or sha(built) != manifest['sha256']:
        raise SystemExit('baseline manifest mismatch')
    built.decode(manifest.get('encoding', 'utf-8'))
    return built


def apply_v515(data: bytes) -> bytes:
    text = data.decode('utf-8')
    text = text.replace('PUBLIC v5.14.1','PUBLIC v5.15.0')
    text = text.replace("version:'5.14.1-public'","version:'5.15.0-public'")
    text = text.replace('<div class="help-step"><b>1. 作品を選ぶ</b><p>図の作品名をクリックするか、上部の検索欄から探します。複数作品をそのままゴールにできます。</p></div>', '<div class="help-step"><b>1. 作品を見る</b><p>図の作品名を左クリック／タップすると、あらすじと関連ラインを表示します。ゴール追加は詳細欄のボタン、PCでは右クリックでもできます。</p></div>')
    text = text.replace('作品をタップするとゴールに追加されます。','作品をタップして詳細を開き、「ゴールに追加」を押してください。')
    text = text.replace('タップ／クリックでゴールに追加。複数選択もできます。','タップ／クリックで詳細を開き、「ゴールに追加」から複数選択できます。')
    detail_dir = V515 / 'work-details'
    manifest = json.loads((detail_dir / 'manifest.json').read_text(encoding='utf-8'))
    details = {}
    for name in manifest['parts']:
        part = json.loads((detail_dir / name).read_text(encoding='utf-8'))
        overlap = set(details) & set(part)
        if overlap:
            raise SystemExit(f'duplicate work detail ids: {sorted(overlap)}')
        details.update(part)
    if len(details) != manifest['count']:
        raise SystemExit('work detail manifest count mismatch')
    styles = (V515 / 'styles.css').read_text(encoding='utf-8') if (V515 / 'styles.css').exists() else ''
    if styles:
        text = text.replace('</head>', f'<style id="v515-styles">\n{styles}\n</style>\n</head>', 1)
    overview_start = text.index('<div id="overview"')
    overview_end = text.index('<div id="mcu"', overview_start)
    overview_svg = render_overview_svg(text)
    overview_panel = f'<div id="overview" class="panel active"><div class="svg-wrap">{overview_svg}</div></div>\n'
    text = text[:overview_start] + overview_panel + text[overview_end:]

    payload = json.dumps(details, ensure_ascii=False, separators=(',', ':'))
    runtime = (V515 / 'runtime.js').read_text(encoding='utf-8') if (V515 / 'runtime.js').exists() else ''
    block = f'<script id="v515-work-details">window.WORK_DETAILS=Object.freeze({payload});</script>\n'
    if runtime:
        block += f'<script id="v515-runtime">\n{runtime}\n</script>\n'
    marker = '</body>'
    if marker not in text:
        raise SystemExit('missing </body> insertion point')
    return text.replace(marker, block + marker, 1).encode('utf-8')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline-only', action='store_true', help='emit the immutable v5.14.1 baseline without v5.15 transforms')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    data = load_baseline()
    if not args.baseline_only:
        data = apply_v515(data)
    Path(args.output).write_bytes(data)
    print(f'build {len(data)} bytes sha256={sha(data)} -> {args.output}')


if __name__ == '__main__':
    main()
