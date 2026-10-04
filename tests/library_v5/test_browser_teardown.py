from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from tests.library_v5.browser_audit_process import run_audit_process

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'tests' / 'library_v5'
RUNNERS = ('browser_mobile_shell_audit.mjs', 'browser_publication_order_audit.mjs')


class BrowserTeardownTests(unittest.TestCase):
    def fixture(self, runner: str, mode: str):
        result = run_audit_process(
            ['node', str(HERE / 'browser_teardown_fixture.mjs'), str(HERE / runner), mode],
            cwd=ROOT, timeout=15, attempts=1,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout), result.stderr

    def test_stop_chrome_terminates_real_descendant_before_removing_profile(self):
        for runner in RUNNERS:
            with self.subTest(runner=runner):
                report, _ = self.fixture(runner, 'parent-live')
                self.assertTrue(report['stopped'], 'descendant heartbeat continued after stopChrome')
                self.assertTrue(report['profileRemoved'])
                self.assertLess(report['elapsed'], 7000)

    @unittest.skipIf(os.name == 'nt', 'POSIX process-group case; Windows tree case above')
    def test_stop_chrome_terminates_group_after_parent_exits(self):
        for runner in RUNNERS:
            with self.subTest(runner=runner):
                report, _ = self.fixture(runner, 'parent-exited')
                self.assertTrue(report['stopped'], 'exited parent must not hide live descendants')

    def test_profile_cleanup_error_returns_with_diagnostic(self):
        for runner in RUNNERS:
            with self.subTest(runner=runner):
                report, stderr = self.fixture(runner, 'profile-error')
                self.assertTrue(report['returned'])
                self.assertTrue(report['retained'])
                self.assertIn('fixture profile busy', stderr)

    def test_infrastructure_error_emits_json_and_nonzero_exit(self):
        for runner in RUNNERS:
            with self.subTest(runner=runner):
                result = run_audit_process(
                    ['node', str(HERE / runner), '--root', str(ROOT / 'missing-fixture-root')],
                    cwd=ROOT, timeout=15, attempts=1,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stdout.strip(), 'infrastructure failure omitted diagnostic JSON')
                report = json.loads(result.stdout)
                self.assertTrue(report['failures'])
                self.assertIn('report-write', result.stderr)

    def test_tree_kill_failure_is_reported_not_silently_accepted(self):
        for runner in RUNNERS:
            with self.subTest(runner=runner):
                result = run_audit_process(
                    ['node', str(HERE / 'browser_teardown_fixture.mjs'), str(HERE / runner), 'kill-error'],
                    cwd=ROOT, timeout=15, attempts=1,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stdout.strip(), 'tree kill failure omitted JSON')
                report = json.loads(result.stdout)
                self.assertIn('fixture tree kill denied', report['failures'][0])
                self.assertIn('chrome-stop-start', result.stderr)
                self.assertIn('report-write', result.stderr)
