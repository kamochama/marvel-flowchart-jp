from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from tests.library_v5.browser_audit_process import run_audit_process


class BrowserAuditProcessTests(unittest.TestCase):
    def test_retries_only_outer_timeout_and_terminates_first_process_tree(self) -> None:
        first = mock.Mock(pid=101, returncode=None)
        first.poll.side_effect = [None, 0]
        first.communicate.side_effect = [
            subprocess.TimeoutExpired(["node"], 10, output="partial", stderr="trace"),
            ("partial", "trace"),
        ]
        second = mock.Mock(pid=202, returncode=0)
        second.communicate.return_value = ("ok", "")
        with mock.patch(
            "tests.library_v5.browser_audit_process.subprocess.Popen",
            side_effect=[first, second],
        ) as popen, mock.patch(
            "tests.library_v5.browser_audit_process._terminate_process_tree"
        ) as terminate:
            result = run_audit_process(["node"], timeout=10)

        self.assertEqual(result.stdout, "ok")
        self.assertEqual(result.stderr, "")
        self.assertEqual(popen.call_count, 2)
        terminate.assert_called_once_with(first)

    def test_semantic_nonzero_result_is_not_retried(self) -> None:
        failed = mock.Mock(pid=303, returncode=1)
        failed.communicate.return_value = ("report", "semantic failure")
        with mock.patch(
            "tests.library_v5.browser_audit_process.subprocess.Popen",
            return_value=failed,
        ) as popen:
            result = run_audit_process(["node"], timeout=10)

        self.assertEqual(result.returncode, 1)
        popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
