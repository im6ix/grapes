from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable


import json


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
        call_id = reply["id"]

        messages.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }],
        })

        result = ctx.call_tool(name, **args)
        messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": str(result),
        })
    raise RuntimeError("too many steps")
