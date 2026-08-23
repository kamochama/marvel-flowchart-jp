#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src' / 'baseline'


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline-only', action='store_true', help='emit the immutable v5.14.1 baseline without v5.15 transforms')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    data = load_baseline()
    # v5.15 transforms are added in later tasks. Until then default output is the baseline too.
    Path(args.output).write_bytes(data)
    print(f'build {len(data)} bytes sha256={sha(data)} -> {args.output}')


if __name__ == '__main__':
    main()
