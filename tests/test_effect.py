from grapes import Harness


async def test_revert_all_removes_the_tool():
    h = Harness()
    ctx = h.create_context()
    ctx.register_tool(
        "add",
        lambda a, b: a + b,
        description="Add two integers",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )
    await ctx.revert_all()

    assert "add" not in h.tools
