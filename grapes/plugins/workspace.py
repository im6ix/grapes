from __future__ import annotations

import unicodedata
from collections.abc import Callable
from os.path import dirname, join
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context, Plugin

Approver = Callable[[Path, str], bool]

LINES_PER_READ = 500
ENTRIES_PER_LIST = 200


READ_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "File or directory path, relative to workspace root.",
        },
        "start_line": {
            "type": "integer",
            "description": "First line or directory entry, 1-based. Defaults to 1.",
        },
        "end_line": {
            "type": "integer",
            "description": "Last line or entry, inclusive.",
        },
    },
    "required": ["path"],
}

EDIT_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "File path, relative to workspace root.",
        },
        "content": {
            "type": "string",
            "description": "Lines to insert. Omit to only remove lines.",
        },
        "start_line": {
            "type": "integer",
            "description": "Line to insert before, 1-based. Omit to append at the end.",
        },
        "end_line": {
            "type": "integer",
            "description": "Last line to remove, inclusive. Only used with start_line.",
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


def _canonical(name: str) -> str:
    return (
        unicodedata.normalize("NFC", name)
        .replace("\u00a0", " ")
        .replace("\u202f", " ")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )


def _names(path: Path) -> list[str] | None:
    try:
        return [entry.name for entry in path.iterdir()]
    except FileNotFoundError:
        return None


def _similar(names: list[str], name: str) -> list[str]:
    base = name.lower()
    return [n for n in names if base in n.lower() or n.lower() in base][:3]


def alternate_path(target: Path) -> Path | None:
    names = _names(target.parent)
    if names is None:
        return None
    base = _canonical(target.name)
    matches = [
        name
        for name in names
        if _canonical(name) == base and (target.parent / name).is_file()
    ]
    return target.parent / matches[0] if len(matches) == 1 else None


def missing_message(path: str, target: Path) -> str:
    names = _names(target.parent)
    if names is None:
        child, parent = target.parent, target.parent.parent
        while parent != child:
            names = _names(parent)
            if names is not None:
                parts = [
                    f"File not found: {path}",
                    f"The folder {child} does not exist. "
                    f"The nearest folder that does is {parent}.",
                ]
                suggestions = _similar(names, child.name)
                if suggestions:
                    parts.append(
                        "Did you mean one of these?\n"
                        + "\n".join(join(str(parent), n) for n in suggestions)
                    )
                return "\n\n".join(parts)
            child, parent = parent, parent.parent
        return f"File not found: {path}"

    suggestions = _similar(names, target.name)
    if not suggestions:
        return f"File not found: {path}"
    return f"File not found: {path}\n\nDid you mean one of these?\n" + "\n".join(
        join(dirname(path), n) for n in suggestions
    )


def read_file(
    root: Path,
    approve: Approver,
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
    *,
    seen: set[Path],
) -> str:
    target = resolve_path(root, path, approve, "read")

    if not target.exists():
        alternate = alternate_path(target)
        if alternate is None:
            raise FileNotFoundError(missing_message(path, target))
        target = alternate

    if target.is_dir():
        return list_dir(target, start_line, end_line)

    if not target.is_file():
        raise FileNotFoundError(f"not a file: {target}")

    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    seen.add(target)
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


def list_dir(target: Path, start_line: int = 1, end_line: int | None = None) -> str:
    if start_line < 1:
        raise ValueError("start_line must be >= 1")
    if end_line is None:
        end_line = start_line + ENTRIES_PER_LIST - 1

    if end_line < start_line:
        raise ValueError("end_line must be >= start_line")

    entries: list[tuple[int, str]] = []
    for entry in target.iterdir():
        if entry.is_symlink():
            entries.append((1, entry.name))
        elif entry.is_dir():
            entries.append((0, entry.name + "/"))
        elif entry.is_file():
            entries.append((1, entry.name))
    entries.sort()

    total = len(entries)
    end = min(end_line, total)
    selected = entries[start_line - 1 : end]

    if not selected:
        return f"(no entries; directory has {total} entries)"

    output = "\n".join(name for _, name in selected)
    if end < total:
        output += f"\n[next: start_line={end + 1}]"
    return output


def workspace_plugin(root: Path, approve: Approver) -> Plugin:
    root = root.resolve()

    def plugin(ctx: Context) -> None:
        seen: set[Path] = set()

        def read_file_tool(
            path: str,
            start_line: int = 1,
            end_line: int | None = None,
        ) -> str:
            return read_file(root, approve, path, start_line, end_line, seen=seen)

        ctx.register_tool(
            "read_file",
            read_file_tool,
            description=(
                "read a text file or list a directory in the workspace; "
                "files 500 lines at a time, directories one level"
            ),
            parameters=READ_FILE_SCHEMA,
        )

        def edit_file_tool(
            path: str,
            content: str | None = None,
            start_line: int | None = None,
            end_line: int | None = None,
        ) -> str:
            return edit_file(root, approve, seen, path, content, start_line, end_line)

        ctx.register_tool(
            "edit_file",
            edit_file_tool,
            description=(
                "insert or remove lines in a file that was read first; "
                "omit start_line to append, give start_line and end_line to remove"
            ),
            parameters=EDIT_FILE_SCHEMA,
        )

    return plugin


def edit_file(
    root: Path,
    approve: Approver,
    seen: set[Path],
    path: str,
    content: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:

    target = resolve_path(root, path, approve, "write")

    if not target.is_file():
        raise FileNotFoundError(f"not a file: {target}")
    if target not in seen:
        raise PermissionError(f"{path} was not read; read it first")

    lines = target.read_text(encoding="utf-8").splitlines()

    if start_line is None:
        at = len(lines)
        stop = at
    else:
        if start_line < 1:
            raise ValueError("start_line must be >= 1")
        at = start_line - 1
        if at > len(lines):
            raise ValueError(f"start_line {start_line} is past the end")
        stop = at
        if end_line is not None:
            if end_line < start_line:
                raise ValueError("end_line must be >= start_line")
            stop = min(end_line, len(lines))

    lines[at:stop] = (content or "").splitlines()
    new_text = "\n".join(lines) + "\n" if lines else ""

    target.write_text(new_text, encoding="utf-8")

    added = len((content or "").splitlines())
    removed = stop - at

    if start_line is None:
        return f"appended {added} lines; file now has {len(lines)} lines"
    if removed == 0:
        return (
            f"inserted {added} lines at {start_line}; file now has {len(lines)} lines"
        )
    if added == 0:
        return (
            f"removed {removed} lines at {start_line}; file now has {len(lines)} lines"
        )
    return f"replaced {removed} lines with {added} at {start_line}; file now has {len(lines)} lines"
