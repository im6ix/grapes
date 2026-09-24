from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context


def calculator_plugin(ctx: Context) -> None:
    ctx.register_tool("add", lambda a, b: a + b)
    ctx.register_tool("subtract", lambda a, b: a - b)
    ctx.register_tool("multiply", lambda a, b: a * b)
    ctx.register_tool("divide", lambda a, b: a / b)
