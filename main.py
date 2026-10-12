import asyncio

from grapes import Harness
from grapes.plugins import calculator_plugin
from grapes.agent.chat import Chat
from grapes.agent.model import model


async def main() -> None:
    h = Harness()
    ctx = h.create_context()
    await ctx.use(calculator_plugin)

    chat = Chat(ctx, model)
    print(chat.say("use the multiply tool to work out 113 * 977."))


asyncio.run(main())
