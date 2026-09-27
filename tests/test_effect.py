from grapes import Harness


async def test_undo_removes_the_tool():
    h = Harness()
    ctx = h.create_context()
    ctx.register_tool("add", lambda a, b: a + b)
    await ctx.undo()

    assert "add" not in h.tools
