from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context


_TWO_INTS = {
    "type": "object",
    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    "required": ["a", "b"],
}


def calculator_plugin(ctx: Context) -> None:
    ctx.register_tool(
        "add", lambda a, b: a + b, description="Add two integers", parameters=_TWO_INTS
    )
    ctx.register_tool(
        "subtract",
        lambda a, b: a - b,
        description="Subtract b from a",
        parameters=_TWO_INTS,
    )
    ctx.register_tool(
        "multiply",
        lambda a, b: a * b,
        description="Multiply two integers",
        parameters=_TWO_INTS,
    )
    ctx.register_tool(
        "divide", lambda a, b: a / b, description="Divide a by b", parameters=_TWO_INTS
    )
