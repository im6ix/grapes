async def test_revert_all_removes_the_tool(h, ctx, two_ints):
    ctx.register_tool(
        "add",
        lambda a, b: a + b,
        description="Add two integers",
        parameters=two_ints,
    )
    await ctx.revert_all()

    assert "add" not in h.tools
