from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src' / 'baseline'
BUILD = ROOT / 'scripts' / 'build_public.py'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'index.html'
        subprocess.run(
            [sys.executable, str(BUILD), '--baseline-only', '--output', str(out)],
            cwd=ROOT,
            check=True,
        )
        data = out.read_bytes()
        assert len(data) == manifest['bytes'], (len(data), manifest['bytes'])
        assert sha256_bytes(data) == manifest['sha256'], (sha256_bytes(data), manifest['sha256'])
        print(f"PASS: baseline roundtrip {manifest['sha256']}")


if __name__ == '__main__':
    main()
