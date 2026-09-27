from grapes import Harness


async def test_set_get_and_undo_value():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "en")
    assert ctx.get("language") == "en"
    await ctx.undo()
    assert ctx.get("language") is None
