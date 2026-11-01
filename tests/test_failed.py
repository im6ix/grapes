import pytest

from grapes.context import Tool
from grapes.fiber import FiberState
from grapes.plugins import greeter_plugin


def make_tool(name: str) -> Tool:
    return Tool(
        name,
        name,
        {"type": "object", "properties": {}},
        lambda: name,
    )


async def test_plugin_load_drains_effects(h, ctx):
    def bad_plugin(ctx) -> None:
        ctx.register_tool(
            "half",
            lambda: print("bad_plugin"),
            description="A tool from a plugin that fails",
            parameters={"type": "object", "properties": {}},
        )
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await ctx.mount(bad_plugin)

    assert "half" not in h.tools
    assert h.registry.fibers[0].state is FiberState.FAILED

    await ctx.mount(greeter_plugin)
    assert "greet" in h.tools

    await ctx.revert_all()
    assert len(h.registry.fibers) == 0
    assert "greet" not in h.tools


async def test_failed_teardown_does_not_block_revert_all(h, ctx):
    def keep() -> None:
        h.tools["kept"] = make_tool("kept")

    def unkeep() -> None:
        h.tools.pop("kept")

    def doom() -> None:
        h.tools["doomed"] = make_tool("doomed")

    def boom() -> None:
        raise RuntimeError("teardown boom")

    ctx.effect(keep, unkeep)
    ctx.effect(doom, boom)

    await ctx.revert_all()
    assert "kept" not in h.tools


async def test_failed_fiber_stays_failed_on_refresh(h, ctx):
    calls = 0

    def attempt(ctx):
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await ctx.mount(attempt)

    fiber = h.registry.fibers[0]
    assert fiber.state is FiberState.FAILED
    assert calls == 1

    fiber.refresh()
    try:
        await fiber.wait_until_settled()
    except RuntimeError:
        pass

    assert fiber.state is FiberState.FAILED
    assert calls == 1
