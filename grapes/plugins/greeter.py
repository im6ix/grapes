from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context


def greeter_plugin(ctx: Context) -> None:
    ctx.register_tool("greet", lambda: "hello")
