#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'build-public.yml'
text = WORKFLOW.read_text(encoding='utf-8')

required = [
    'pull_request:',
    'workflow_dispatch:',
    'contents: read',
    'pages: write',
    'id-token: write',
    'statuses: write',
    'actions/configure-pages@v5',
    'actions/upload-pages-artifact@v5',
    'actions/deploy-pages@v5',
    'actions/github-script@v9',
    "github.ref == 'refs/heads/main'",
    'cp index.html README.md AUDIT.md AUDIT.json preview.png .nojekyll _site/',
    'include-hidden-files: true',
    "context: 'marvel-pages'",
    'GITHUB_RUN_ID',
]

missing = [needle for needle in required if needle not in text]
assert not missing, f'missing Pages workflow contract entries: {missing}'
assert 'contents: write' not in text, 'workflow must not need contents write permission'
assert 'git push' not in text, 'workflow must deploy directly instead of creating a bot commit'
assert 'name: marvel-flowchart-jp-public' in text
assert 'if: always()' in text, 'main workflow must report status even when build/deploy fails'
print('pages workflow contract OK')
