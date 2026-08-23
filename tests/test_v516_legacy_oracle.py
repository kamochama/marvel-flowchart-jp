from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '1d3d57aaba730740f8aad78351806fc3cdbbd8d07cc91a5f82bed6ab10a2fdad'


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        legacy = td / 'legacy.html'
        baseline = td / 'baseline.html'
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_v515_legacy.py'), '--output', str(legacy)], check=True)
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_v515_legacy.py'), '--baseline-only', '--output', str(baseline)], check=True)
        text = legacy.read_text(encoding='utf-8')
        assert 'PUBLIC v5.15.0' in text
        assert 'PUBLIC v5.16.0' not in text
        assert hashlib.sha256(baseline.read_bytes()).hexdigest() == EXPECTED
    print('PASS: frozen v5.15 legacy oracle')


if __name__ == '__main__':
    main()
