from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..context import Context


def run(
    ctx: Context,
    model: Callable[[list[dict[str, Any]]]],
    message: str,
    max_steps: int = 10,
) -> str:

    messages: list[dict[str, Any]] = [{"role": "user", "content": message}]

    for _ in range(max_steps):
        reply = model(messages)

        if reply["type"] == "answer":
            return reply["content"]

        name = reply["name"]
        args = reply["args"]
        result = ctx.call_tool(name, *args)
        messages.append({"role": "tool", "content": str(result)})
    raise RuntimeError("too many steps")
