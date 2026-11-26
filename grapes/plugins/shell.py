"""`run_shell`: a bash command, with pi's semantics.

Ported from pi (`@earendil-works/pi-coding-agent`), specifically
`dist/core/tools/bash.js`, `dist/core/bash-executor.js` and
`dist/utils/shell.js`. The behavior is deliberately pi's, not ours: `bash -c`,
cwd fixed at the workspace root, no approval step, an optional timeout that
kills the process group, stdout and stderr merged, and the last 2000 lines or
50KB of output kept.

Two deliberate differences: pi spills the full output to a temp file and tells
the model its path; we have nothing to read it back with, so we only print the
hint. And pi's tool protocol can flag a result as an error while still
returning content; grapes cannot (an exception loses the output), so we return
the text with a status line instead of raising.
"""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context, Plugin

MAX_LINES = 2000
MAX_BYTES = 50 * 1024

RUN_SHELL_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "Shell command to execute",
        },
        "timeout": {
            "type": "number",
            "description": "Timeout in seconds (optional, no default timeout)",
        },
    },
    "required": ["command"],
}


def shell() -> str:
    if Path("/bin/bash").exists():
        return "/bin/bash"
    return which("bash") or "sh"


def truncate_tail(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    size = 0
    for line in reversed(lines):
        size += len(line.encode()) + 1
        if size > MAX_BYTES or len(kept) == MAX_LINES:
            break
        kept.append(line)

        if len(kept) == len(lines):
            return text

    kept.reverse()
    hint = f"[truncated: showing the last {len(kept)} of {len(lines)} lines]"
    if len(kept) < MAX_LINES:
        hint = (
            f"[truncated: showing the last {MAX_BYTES // 1024}KB of {len(lines)} lines]"
        )
    return "\n".join(kept) + "\n\n" + hint


def run(command: str, cwd: Path, timeout: float | None = None) -> tuple[str, int]:
    if timeout is not None and not timeout > 0:
        raise ValueError("timeout must be a positive number of seconds")

    process = subprocess.Popen(
        [shell(), "-c", command],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    timed_out = False
    try:
        out, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        out, _ = process.communicate()

    text = truncate_tail(out.decode("utf-8", "replace"))
    code = process.returncode

    if code < 0:
        code = 128 - code
    if timed_out:
        return append_status(text, f"Command timed out after {timeout} seconds"), code
    return text, code


def append_status(text: str, status: str) -> str:
    return f"{text}\n\n{status}" if text else status


def shell_plugin(root: Path) -> Plugin:
    def plugin(ctx: Context) -> None:
        def run_shell_tool(command: str, timeout: float | None = None) -> str:
            text, code = run(command, root, timeout)
            return append_status(text, f"[exit code {code}]")

        ctx.register_tool(
            "run_shell",
            run_shell_tool,
            description=(
                "run a bash command in the workspace root; paths inside "
                "the commands are not sandboxed"
            ),
            parameters=RUN_SHELL_SCHEMA,
        )

    return plugin
