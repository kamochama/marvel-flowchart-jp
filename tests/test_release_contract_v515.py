from __future__ import annotations
import subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    out=Path(td)/'index.html'
    subprocess.run([sys.executable,str(ROOT/'scripts'/'build_public.py'),'--output',str(out)],cwd=ROOT,check=True)
    s=out.read_text(encoding='utf-8')
    assert 'PUBLIC v5.15.0' in s
    assert "version:'5.15.0-public'" in s
    assert '左クリック／タップすると、あらすじ' in s
    assert '作品をタップするとゴールに追加されます。' not in s
    assert 'タップ／クリックでゴールに追加' not in s
    assert '左クリック / タップ' in (ROOT/'README.md').read_text(encoding='utf-8')
print('PASS: v5.15 public version and interaction guidance')
