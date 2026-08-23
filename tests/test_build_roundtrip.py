from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'index.html'
BUILD = ROOT / 'scripts' / 'build_public.py'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'index.html'
        subprocess.run(
            [sys.executable, str(BUILD), '--baseline-only', '--output', str(out)],
            cwd=ROOT,
            check=True,
        )
        assert out.read_bytes() == BASELINE.read_bytes(), (sha256(out), sha256(BASELINE))
        print(f'PASS: byte-identical roundtrip {sha256(out)}')


if __name__ == '__main__':
    main()
