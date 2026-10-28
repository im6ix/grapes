import asyncio
from grapes import Harness


def test_async_teardown_runs_on_revert_all():
    log = []

    async def teardown() -> None:
        log.append("down")

    async def main() -> None:
        h = Harness()
        ctx = h.create_context()
        ctx.effect(lambda: log.append("up"), teardown)
        await ctx.revert_all()

    asyncio.run(main())
    assert log == ["up", "down"]
