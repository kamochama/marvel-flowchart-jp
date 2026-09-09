from __future__ import annotations

import os
import signal
import subprocess
from collections.abc import Sequence


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate the Node process and descendants started for one audit."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
        )
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_audit_process(
    command: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    timeout: float,
    env: dict[str, str] | None = None,
    attempts: int = 2,
) -> subprocess.CompletedProcess[str]:
    """Run a browser audit, retrying only an outer process timeout once."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    popen_kwargs: dict[str, object] = {
        "cwd": cwd,
        "env": env,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    for attempt in range(attempts):
        process = subprocess.Popen(list(command), **popen_kwargs)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            _terminate_process_tree(process)
            try:
                partial_stdout, partial_stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                partial_stdout, partial_stderr = error.output or "", error.stderr or ""
            if attempt + 1 >= attempts:
                raise subprocess.TimeoutExpired(
                    list(command), timeout, output=partial_stdout, stderr=partial_stderr
                ) from error
            continue
        return subprocess.CompletedProcess(list(command), process.returncode, stdout, stderr)
    raise AssertionError("unreachable audit process retry state")
