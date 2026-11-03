from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context, Plugin

Approver = Callable[[Path, str], bool]

LINES_PER_READ = 500

READ_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "File path, relative to workspace root.",
        },
        "start_line": {
            "type": "integer",
            "description": "First line to read, 1-based. Defaults to 1.",
        },
        "end_line": {
            "type": "integer",
            "description": "Last line to read, inclusive. defaults to start_line + 499",
        },
    },
    "required": ["path"],
}


def resolve_path(root: Path, path: str, approve: Approver, action: str) -> Path:
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    target = target.resolve()

    if target == root or target.is_relative_to(root):
        return target

    if approve(target, action):
        return target

    raise PermissionError(f"access denied: {target}")


def read_file(
    root: Path,
    approve: Approver,
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
) -> str:
    target = resolve_path(root, path, approve, "read")

    if not target.is_file():
        raise FileNotFoundError(f"not a file: {target}")

    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)

    if start_line < 1:
        raise ValueError("start_line must be >= 1")

    if end_line is None:
        end_line = start_line + LINES_PER_READ - 1

    if end_line < start_line:
        raise ValueError("end_line must be >= start_line")

    end_line = min(end_line, total)
    selected = lines[start_line - 1 : end_line]

    if not selected:
        return f"(no lines; file has {total} lines)"

    output = "\n".join(
        f"{number}\t{line}" for number, line in enumerate(selected, start_line)
    )

    if end_line < total:
        output += f"\n[next: start_line={end_line + 1}]"

    return output


def workspace_plugin(root: Path, approve: Approver) -> Plugin:
    root = root.resolve()

    def plugin(ctx: Context) -> None:
        def read_file_tool(
            path: str,
            start_line: int = 1,
            end_line: int | None = None,
        ) -> str:
            return read_file(root, approve, path, start_line, end_line)

        ctx.register_tool(
            "read_file",
            read_file_tool,
            description="read a text file from the workspace, 500 lines at a time",
            parameters=READ_FILE_SCHEMA,
        )

    return plugin
