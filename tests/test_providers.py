from grapes import Harness


async def test_two_providers_one_key():
    h = Harness()
    ctx = h.create_context()

    d1 = ctx.set("language", "en")
    d2 = ctx.set("language", "fr")

    await d2()
    assert ctx.get("language") == "en"

    await d1()
    assert ctx.get("language") is None
