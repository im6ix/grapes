from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context


def file_search_plugin(ctx: Context) -> None:
    ctx.register_tool("search_file", lambda: print("seraching..."))
    print("loading plugin")
