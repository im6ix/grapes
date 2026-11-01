from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from grapes.agent.llm import Llm

if TYPE_CHECKING:
    from ..context import Context


async def run_agent(
    ctx: Context,
    message: str,
    max_steps: int = 10,
    messages: list[dict[str, Any]] | None = None,
) -> str:
    if messages is None:
        messages = []

    llm = ctx.lookup("llm")
    if not isinstance(llm, Llm):
        raise TypeError("no llm mounted")
    messages.append({"role": "user", "content": message})
    for _ in range(max_steps):
        reply = await llm.complete(messages, ctx.tool_schemas())
        if reply["type"] == "answer":
            messages.append({"role": "assistant", "content": reply["content"]})
            return reply["content"]

        name = reply["name"]
        args = reply["args"]
        call_id = reply["id"]
        ctx.logger.info(f"tool call: {name} {args}")
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {"name": name, "arguments": json.dumps(args)},
                    }
                ],
            }
        )

        try:
            result = await ctx.call_tool(name, **args)
            ctx.logger.info(f"tool result {result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(result),
                }
            )
        except Exception as error:
            error_message = f"ERROR: {type(error).__name__}: {error}"
            ctx.logger.error(error_message)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": error_message,
                }
            )
    raise RuntimeError("too many steps")
