from grapes import Harness
from grapes.plugins import calculator_plugin, file_search_plugin, greeter_plugin


async def test_child_ctx():
    h = Harness()
    ctx = h.create_context()
    dispose_calc = await ctx.use(calculator_plugin)
    await ctx.use(file_search_plugin)
    await dispose_calc()
    assert "add" not in h.tools
    assert "search_file" in h.tools


async def test_parent_sees_child():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(calculator_plugin)
    await ctx.use(file_search_plugin)
    await ctx.undo()
    assert "add" not in h.tools
    assert "search_file" not in h.tools


async def test_dispose_then_undo_is_safe():
    h = Harness()
    ctx = h.create_context()
    dispose = await ctx.use(greeter_plugin)
    await dispose()
    await ctx.undo()
    assert "greet" not in h.tools
