#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MAX_BYTES = 64 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_utf8(data: bytes, limit: int = MAX_BYTES) -> list[bytes]:
    parts: list[bytes] = []
    start = 0
    while start < len(data):
        end = min(start + limit, len(data))
        while end > start:
            try:
                data[start:end].decode('utf-8')
                break
            except UnicodeDecodeError:
                end -= 1
        if end == start:
            raise RuntimeError('could not find UTF-8 boundary')
        parts.append(data[start:end])
        start = end
    return parts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    src = Path(args.input)
    out = Path(args.output)
    parts_dir = out / 'parts'
    parts_dir.mkdir(parents=True, exist_ok=True)
    for old in parts_dir.glob('part-*.html'):
        old.unlink()

    data = src.read_bytes()
    parts = split_utf8(data)
    manifest_parts = []
    for i, chunk in enumerate(parts):
        name = f'part-{i:03d}.html'
        path = parts_dir / name
        path.write_bytes(chunk)
        manifest_parts.append({'path': f'parts/{name}', 'bytes': len(chunk), 'sha256': sha(chunk)})

    manifest = {
        'format': 1,
        'encoding': 'utf-8',
        'source': src.name,
        'max_part_bytes': MAX_BYTES,
        'bytes': len(data),
        'sha256': sha(data),
        'parts': manifest_parts,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"split {len(data)} bytes into {len(parts)} parts; sha256={manifest['sha256']}")


if __name__ == '__main__':
    main()
