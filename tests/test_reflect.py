from grapes import Harness


async def test_provide_lookup_and_revert_all_value():
    h = Harness()
    ctx = h.create_context()
    ctx.provide("language", "en")
    assert ctx.lookup("language") == "en"
    await ctx.revert_all()
    assert ctx.lookup("language") is None
