# PUBLIC v5.16.0 Source Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PUBLIC v5.15.0 の機能・データ・操作を変えず、`src/app` / `src/data` / `src/config` だけから PUBLIC v5.16.0 を決定的に生成できる正本ソース構造へ移行する。

**Architecture:** 現行の v5.14.1 baseline + v5.15 patch builder は `scripts/build_v515_legacy.py` に凍結し、v5.15 回帰 oracle としてのみ残す。v5.16 は canonical JSON、静的 shell、manifest 順の CSS/JS、データ駆動 overview generator を一方向に組み立て、compatibility build の parity gate を通った後だけ `scripts/build_public.py` を新経路へ切り替える。

**Tech Stack:** Python 3.13、標準ライブラリ、Graphviz `dot`、vanilla HTML/CSS/JavaScript、GitHub Actions / GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-08-24-v516-source-foundation-design.md`

## Global Constraints

- 作品 **131**、有向接続 **199**、人物リンク **155**、主要フロー **76作品 / 5区分**、作品詳細 **131 / 131** を変更しない。
- OR FNV-1a 64 = `9c38afad0f8ac3fe`、AND = `ad48d8c46ae1bd61`、PATH = `8b9847fcda5cdf96`、単一ゴール予習 = `a3c6f1c12199a903` を固定する。
- `ニュー・ミュータント` に架空直接接続を追加しない。
- 左クリック / タップ / 検索結果は詳細フォーカスのみ。PC右クリックと詳細CTAだけがゴール集合を変更する。
- Shared Room クライアント契約、スマホ1本指パン / 2本指ズーム / タップ詳細を変更しない。
- 通常ビルドは `src/baseline/` と `src/v515/` を読まない。legacy / compatibility 検査だけが読める。
- npm、React、Vue、ES module 移行、新規外部ビルドサービスを導入しない。
- Pages配布は `index.html / README.md / AUDIT.md / AUDIT.json / preview.png / .nojekyll` の6ファイル固定。
- GitHub Pages Direct Deploy の方式は変更しない。

---

### Task 1: Freeze the v5.15 legacy oracle

**Files:**
- Create: `scripts/build_v515_legacy.py`
- Create: `tests/test_v516_legacy_oracle.py`
- Modify: `.github/workflows/build-public.yml`

**Interfaces:**
- Produces `python scripts/build_v515_legacy.py --output <path>` and `--baseline-only`.
- Output must remain PUBLIC v5.15.0 and baseline SHA-256 must remain `1d3d57aaba730740f8aad78351806fc3cdbbd8d07cc91a5f82bed6ab10a2fdad`.

- [ ] **Step 1: Write the failing oracle test**

```python
from __future__ import annotations
import hashlib, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '1d3d57aaba730740f8aad78351806fc3cdbbd8d07cc91a5f82bed6ab10a2fdad'

def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); legacy = td/'legacy.html'; baseline = td/'baseline.html'
        subprocess.run([sys.executable, str(ROOT/'scripts/build_v515_legacy.py'), '--output', str(legacy)], check=True)
        subprocess.run([sys.executable, str(ROOT/'scripts/build_v515_legacy.py'), '--baseline-only', '--output', str(baseline)], check=True)
        text = legacy.read_text(encoding='utf-8')
        assert 'PUBLIC v5.15.0' in text and 'PUBLIC v5.16.0' not in text
        assert hashlib.sha256(baseline.read_bytes()).hexdigest() == EXPECTED
    print('PASS: frozen v5.15 legacy oracle')

if __name__ == '__main__': main()
```

- [ ] **Step 2: Run it before implementation**

Run: `python tests/test_v516_legacy_oracle.py`  
Expected: FAIL because `scripts/build_v515_legacy.py` does not exist.

- [ ] **Step 3: Freeze the builder**

Copy current `scripts/build_public.py` byte-for-byte to `scripts/build_v515_legacy.py`. Do not change normal build in this task.

- [ ] **Step 4: Add the oracle test to CI**

Add `python tests/test_v516_legacy_oracle.py` to the verify step.

- [ ] **Step 5: Verify and commit**

Run: `python tests/test_v516_legacy_oracle.py`  
Expected: PASS.

Commit: `test: freeze v5.15 build oracle`

---

### Task 2: Extract canonical data and configuration

**Files:**
- Create: `src/data/works.json`
- Create: `src/data/edges.json`
- Create: `src/data/people-links.json`
- Create: `src/data/work-details/manifest.json` and its `part-*.json`
- Create: `src/config/overview-groups.json`
- Create: `src/config/group-labels.json`
- Create: `src/config/featured-route.json`
- Create: `scripts/source_model.py`
- Create: `tests/test_v516_source_data.py`

**Interfaces:**
- `source_model.load_model() -> dict` returns keys `works`, `edges`, `people_links`, `work_details`, `overview_groups`, `group_labels`, `featured_route`.
- `featured-route.json` contains exactly `enabled,targetId,label,eyebrow,description`.

- [ ] **Step 1: Write a failing data-contract test**

```python
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from source_model import load_model

def main():
    m = load_model(); works=m['works']; edges=m['edges']; people=m['people_links']; details=m['work_details']
    ids=[w['id'] for w in works]; idset=set(ids)
    assert len(works)==len(idset)==131
    assert len(edges)==199 and len(people)==155 and set(details)==idset
    assert all(e['source'] in idset and e['target'] in idset for e in edges)
    assert all(p['work_id'] in idset for p in people)
    overview=[wid for key in ('infinity','multiverse','tv','fox','animation') for wid in m['overview_groups'][key]]
    assert len(overview)==len(set(overview))==76 and set(overview)<=idset
    f=m['featured_route']; assert set(f)=={'enabled','targetId','label','eyebrow','description'} and f['targetId'] in idset
    nm='the-new-mutants-2020'; assert not any(e['source']==nm or e['target']==nm for e in edges)
    print('PASS: v5.16 canonical data/config contract')

if __name__ == '__main__': main()
```

- [ ] **Step 2: Verify failure**

Run: `python tests/test_v516_source_data.py`  
Expected: FAIL because canonical source does not exist.

- [ ] **Step 3: Extract values without editing them**

Generate v5.15 with `build_v515_legacy.py`. Decode the JSON literals after `const NODES=`, `const EDGES=`, `const CHAR_LINKS=` using `json.JSONDecoder().raw_decode`, then write them as UTF-8 JSON with `ensure_ascii=False`. Copy v5.15 work-detail parts, overview groups, and group labels byte-for-byte.

Create `src/config/featured-route.json` with the existing values:

```json
{
  "enabled": true,
  "targetId": "avengers-doomsday-2026-12-18",
  "label": "ドゥームズデイへの道",
  "eyebrow": "今見るなら",
  "description": "主要フローを長くたどって表示"
}
```

- [ ] **Step 4: Implement `source_model.py` validation**

`load_model()` must reject duplicate work IDs, unknown edge endpoints, unknown people-link IDs, detail-ID mismatch, duplicate/missing overview IDs, or an unknown featured target with `ValueError`.

- [ ] **Step 5: Verify and commit**

Run: `python tests/test_v516_source_data.py`  
Expected: PASS.

Commit: `refactor: extract canonical marvel data`

---

### Task 3: Extract app shell, styles, and runtime

**Files:**
- Create: `src/app/shell.html`
- Create: `src/app/styles/manifest.json`, `000-base.css`, `010-responsive.css`, `020-v515-details.css`
- Create: `src/app/runtime/manifest.json`
- Create runtime files `000-core.js`, `010-selection-v55.js`, `020-preparation-v56.js`, `030-shared-room-v512.js`, `040-selection-core-v510.js`, `050-audit-edge-paint.js`, `060-fan-edge-paint.js`, `070-family-focus.js`, `080-mobile-ui.js`, `090-public-help.js`, `100-watch-workspace.js`, `110-watch-back.js`, `120-navigation-v514.js`, `130-featured-route.js`, `140-details-v515.js`
- Create: `tests/test_v516_app_source.py`

**Interfaces:**
- `shell.html` markers are exactly `<!--MARVEL_STYLES-->`, `<!--MARVEL_OVERVIEW-->`, `<!--MARVEL_SCRIPTS-->`.
- CSS/JS order is determined only by manifest arrays.

- [ ] **Step 1: Write the failing app-source test**

```python
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; APP=ROOT/'src/app'

def main():
    shell=(APP/'shell.html').read_text(encoding='utf-8')
    for x in ('<!--MARVEL_STYLES-->','<!--MARVEL_OVERVIEW-->','<!--MARVEL_SCRIPTS-->'): assert shell.count(x)==1
    forbidden=('const NODES=','const EDGES=','const CHAR_LINKS=','window.FEATURED_ROUTE=Object.freeze(','window.WORK_DETAILS=Object.freeze(')
    assert not any(x in shell for x in forbidden)
    styles=json.loads((APP/'styles/manifest.json').read_text(encoding='utf-8'))
    runtime=json.loads((APP/'runtime/manifest.json').read_text(encoding='utf-8'))
    assert styles==['000-base.css','010-responsive.css','020-v515-details.css']
    assert len(runtime)==15 and runtime[0]=='000-core.js' and runtime[-1]=='140-details-v515.js'
    bodies='\n'.join((APP/'runtime'/n).read_text(encoding='utf-8') for n in runtime)
    assert not any(x in bodies for x in forbidden)
    print('PASS: v5.16 app source boundaries')

if __name__ == '__main__': main()
```

- [ ] **Step 2: Verify failure**

Run: `python tests/test_v516_app_source.py`  
Expected: FAIL because `src/app` does not exist.

- [ ] **Step 3: Extract shell and styles from freshly generated v5.15**

Preserve current three style bodies in document order. Replace all inline styles with one styles marker, the complete overview panel with the overview marker, and the 16 current inline scripts with one scripts marker.

- [ ] **Step 4: Extract runtime without second-source data**

From script block 0, remove only the leading `NODES`, `EDGES`, `CHAR_LINKS` assignments and keep the remainder as `000-core.js`. Map current blocks 1–12 one-to-one to 010–120. From featured block 13 remove only `window.FEATURED_ROUTE=Object.freeze(...)` and store the IIFE as `130-featured-route.js`. Do not create a runtime file for block 14 (work-details payload). Store block 15 as `140-details-v515.js`.

- [ ] **Step 5: Write manifests, verify, commit**

Run: `python tests/test_v516_app_source.py`  
Expected: PASS.

Commit: `refactor: extract canonical app source`

---

### Task 4: Add canonical compatibility builder and parity gate

**Files:**
- Create: `scripts/build_v516.py`
- Modify: `scripts/generate_overview.py`
- Create: `tests/test_v516_compatibility.py`
- Create: `tests/test_v516_deterministic.py`

**Interfaces:**
- `build_v516.build_html(version: str='5.16.0') -> bytes`.
- `generate_overview.render_overview_svg_from_model(works, edges, overview_groups, group_labels) -> str`.
- CLI supports `python scripts/build_v516.py --version 5.15.0 --output <path>`.

- [ ] **Step 1: Write failing compatibility tests**

`test_v516_compatibility.py` builds legacy v5.15 and canonical `--version 5.15.0`, decodes NODES/EDGES/CHAR_LINKS/WORK_DETAILS/FEATURED_ROUTE from both, and asserts deep equality plus equal style/runtime order.

Create deterministic test:

```python
from __future__ import annotations
import hashlib, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as td:
        a=Path(td)/'a.html'; b=Path(td)/'b.html'
        cmd=[sys.executable,str(ROOT/'scripts/build_v516.py'),'--version','5.15.0']
        subprocess.run(cmd+['--output',str(a)],check=True); subprocess.run(cmd+['--output',str(b)],check=True)
        assert hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    print('PASS: deterministic canonical build')

if __name__ == '__main__': main()
```

- [ ] **Step 2: Verify intended failures**

Run `python tests/test_v516_compatibility.py` and `python tests/test_v516_deterministic.py`.  
Expected: FAIL because builder/API do not exist.

- [ ] **Step 3: Refactor overview generator without rendering changes**

Move current rendering logic to `render_overview_svg_from_model(...)`. Keep DOT attributes, edge styling, class annotations, Graphviz invocation, and validation unchanged. Keep `render_overview_svg(source)` as a legacy adapter so `build_v515_legacy.py` keeps working.

- [ ] **Step 4: Implement canonical composition**

`build_v516.py` must: load canonical model; read shell; inject styles in manifest order; render overview from canonical works/edges/config; inject compact NODES/EDGES/CHAR_LINKS payload before `000-core.js`; inject runtime 010–120; inject FEATURED_ROUTE immediately before featured runtime; inject WORK_DETAILS in its current dedicated script; inject `140-details-v515.js` as `id="v515-runtime"`; replace each shell marker once; return UTF-8 bytes. Use `json.dumps(..., ensure_ascii=False, separators=(',', ':'))` for deterministic embedded payloads.

- [ ] **Step 5: Pass parity + deterministic tests and commit**

Run both tests. Expected: PASS.

Commit: `build: add canonical v5.16 builder`

---

### Task 5: Switch normal build to PUBLIC v5.16.0

**Files:**
- Modify: `scripts/build_public.py`
- Modify: `tests/test_source_layout.py`
- Create: `tests/test_v516_public_build.py`
- Modify: `.github/workflows/build-public.yml`

**Interfaces:**
- Normal command remains `python scripts/build_public.py --output index.html`.
- Implementation becomes a thin wrapper around `build_v516.build_html('5.16.0')`.

- [ ] **Step 1: Write failing normal-build test**

```python
from __future__ import annotations
import subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=(ROOT/'scripts/build_public.py').read_text(encoding='utf-8')
    assert 'baseline' not in source and 'v515' not in source
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'index.html'
        subprocess.run([sys.executable,str(ROOT/'scripts/build_public.py'),'--output',str(out)],check=True)
        text=out.read_text(encoding='utf-8')
        assert 'PUBLIC v5.16.0' in text and 'PUBLIC v5.15.0' not in text
        for x in ('const NODES=','const EDGES=','const CHAR_LINKS=','window.WORK_DETAILS=Object.freeze(','window.FEATURED_ROUTE=Object.freeze('): assert x in text
    print('PASS: canonical PUBLIC v5.16.0 build')

if __name__ == '__main__': main()
```

- [ ] **Step 2: Verify failure before switch**

Run: `python tests/test_v516_public_build.py`  
Expected: FAIL because normal build is still v5.15 legacy.

- [ ] **Step 3: Switch only after Task 4 is green**

Replace `scripts/build_public.py` with a thin argparse/output wrapper around `build_v516.build_html('5.16.0')`. It must not import/read baseline or v515 paths.

- [ ] **Step 4: Tighten source-layout test**

Assert the canonical shell/manifests/data/config files exist, while keeping the old baseline manifest integrity assertion as a recovery check. Assert `build_public.py` contains neither `baseline` nor `v515`.

- [ ] **Step 5: Update CI**

Add v5.16 oracle/source/app/compatibility/deterministic/public-build tests. Change only the public version grep to `PUBLIC v5.16.0`. Keep configure/upload/deploy/report jobs unchanged.

- [ ] **Step 6: Run full workflow test set**

Run the pre-existing tests plus all v5.16 tests. Old tests may change only version-specific expectations; do not weaken counts, semantic hashes, interaction checks, or six-file contract.

- [ ] **Step 7: Commit**

Commit: `refactor: switch public build to canonical source`

---

### Task 6: Release audit, PR, merge, and production artifact verification

**Files:**
- Modify: `AUDIT.md`
- Modify: `AUDIT.json`
- Modify: `README.md` only if it displays the public version
- Create/rename: `tests/test_release_contract_v516.py`
- Modify: `.github/workflows/build-public.yml` if test filename changes

**Interfaces:**
- Artifact remains exact six root files.
- Main commit status context remains `marvel-pages`.

- [ ] **Step 1: Write v5.16 release assertion before audit metadata change**

Require `AUDIT.json['version']=='5.16.0'`, `allPass is True`, prior data/hash assertions, and exact six-file package contract.

- [ ] **Step 2: Confirm it fails only on v5.15 metadata**

Run: `python tests/test_release_contract_v516.py`.  
Expected: FAIL on version/source-foundation metadata only.

- [ ] **Step 3: Update audit without claiming feature changes**

Keep all prior regression values and add:

```json
"sourceFoundation": {
  "canonicalBuild": true,
  "normalBuildUsesBaseline": false,
  "normalBuildUsesV515Patch": false,
  "deterministic": true,
  "legacyOracleRetained": true,
  "parityWithV515": true
}
```

`AUDIT.md` must describe v5.16 as a source-foundation migration and explicitly state that 131/199/155, overview 76, details 131/131, semantic hashes, interaction behavior, featured route, Shared Room client, and six-file release contract are unchanged.

- [ ] **Step 4: Run complete test/build command set again**

Build `index.html`, run every old and v5.16 test, then verify `PUBLIC v5.16.0`.

- [ ] **Step 5: Open PR**

Title: `PUBLIC v5.16.0: canonical source foundation`  
Body: no work/edge/person/detail/featured/Shared Room behavior changes; source-architecture migration with v5.15 parity gate.

- [ ] **Step 6: Fix any failed PR check at the root cause**

Do not edit oracle hashes/counts to make mismatches pass.

- [ ] **Step 7: Merge with expected head SHA after PR CI is green**

Then query the main commit `marvel-pages` status and inspect the target Actions run. Build, deploy, report must all succeed.

- [ ] **Step 8: Verify the production downloadable artifact**

It must contain exactly `.nojekyll`, `AUDIT.json`, `AUDIT.md`, `README.md`, `index.html`, `preview.png`. `index.html` must contain `PUBLIC v5.16.0`; `AUDIT.json` must have `allPass:true` and all `sourceFoundation` flags true/false as specified.

- [ ] **Step 9: No follow-up bot commit**

The merged source commit itself must be the commit whose `marvel-pages` status becomes green.
