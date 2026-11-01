async def test_provide_lookup_and_revert_all_value(ctx):
    ctx.provide("language", "en")
    assert ctx.lookup("language") == "en"
    await ctx.revert_all()
    assert ctx.lookup("language") is None
