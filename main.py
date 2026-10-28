import asyncio
import time
import json

from grapes import Harness
from grapes.plugins import calculator_plugin
from grapes.agent.chat import Chat
from grapes.agent.model import model_plugin
from grapes.agent.llm import llm_plugin


async def main() -> None:
    h = Harness()
    ctx = h.create_context()
    await ctx.mount(calculator_plugin)
    await ctx.mount(llm_plugin)
    await ctx.mount(model_plugin, inject=["llm"])

    chat = Chat(ctx)
    print("grapes chat - 'quit' or Ctrl-D to exit")
    try:
        while True:
            try:
                line = input("\n> ").strip()
            except EOFError:
                break
            if not line or line in {"quit", "exit"}:
                break
            start = time.monotonic()
            answer = await chat.ask(line)
            print(
                f"{answer}        [{time.monotonic() - start:.1f}s, {len(json.dumps(chat.messages)) // 4} tok]"
            )
    except KeyboardInterrupt:
        pass
    finally:
        await ctx.revert_all()
        print("after revert_all, tools left:", ctx.tool_schemas())


asyncio.run(main())
