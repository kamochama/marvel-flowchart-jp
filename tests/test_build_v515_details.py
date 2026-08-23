from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'scripts' / 'build_public.py'
BASELINE = ROOT / 'index.html'
def load_details():
    base=ROOT/'src/v515/work-details'
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    out={}
    for name in manifest['parts']:
        out.update(json.loads((base/name).read_text(encoding='utf-8')))
    return out

DETAILS = load_details()
MARKER = 'window.WORK_DETAILS=Object.freeze('


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        base = td / 'baseline.html'
        built = td / 'v515.html'
        subprocess.run([sys.executable, str(BUILD), '--baseline-only', '--output', str(base)], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(BUILD), '--output', str(built)], cwd=ROOT, check=True)

        baseline_bytes = BASELINE.read_bytes()
        assert base.read_bytes() == baseline_bytes, (sha256(base.read_bytes()), sha256(baseline_bytes))

        text = built.read_text(encoding='utf-8')
        assert MARKER in text, 'v5.15 WORK_DETAILS injection missing'
        start = text.index(MARKER) + len(MARKER)
        end = text.index(');</script>', start)
        injected = json.loads(text[start:end])
        assert injected == DETAILS
        assert len(injected) == 131
        assert built.read_bytes() != baseline_bytes
        print('PASS: baseline remains exact; default build injects 131 work details')


if __name__ == '__main__':
    main()
