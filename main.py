import asyncio

from grapes import Harness
from grapes.plugins import calculator_plugin


async def main() -> None:
    h = Harness()
    ctx = h.create_context()
    calculator_plugin(ctx)

    print(ctx._harness.tools["add"](3, 5))
    await ctx.undo()
    print(ctx._harness.tools)


if __name__ == "__main__":
    asyncio.run(main())
