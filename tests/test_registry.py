from grapes.plugins import calculator_plugin, file_search_plugin, greeter_plugin


async def test_child_ctx(h, ctx):
    dispose_calc = await ctx.mount(calculator_plugin)
    await ctx.mount(file_search_plugin)
    await dispose_calc()
    assert "add" not in h.tools
    assert "search_file" in h.tools


async def test_parent_sees_child(h, ctx):
    await ctx.mount(calculator_plugin)
    await ctx.mount(file_search_plugin)
    await ctx.revert_all()
    assert "add" not in h.tools
    assert "search_file" not in h.tools


async def test_dispose_then_revert_all_is_safe(h, ctx):
    dispose = await ctx.mount(greeter_plugin)
    await dispose()
    await ctx.revert_all()
    assert "greet" not in h.tools
