from grapes import Harness


async def test_two_providers_one_key():
    h = Harness()
    ctx = h.create_context()

    d1 = ctx.provide("language", "en")
    d2 = ctx.provide("language", "fr")

    await d2()
    assert ctx.lookup("language") == "en"

    await d1()
    assert ctx.lookup("language") is None

async def test_replacing_a_provider_reloads_the_consumer():
    h = Harness()
    ctx = h.create_context()
    log = []

    def consumer(ctx):
        value = ctx.lookup("x")
        ctx.effect(
            lambda: log.append(("load", value)),
            lambda: log.append(("unload", ctx.lookup("x")))
        )

    ctx.provide("x", 1)
    await ctx.mount(consumer, inject=["x"])
    assert log == [("load", 1)]

    ctx.provide("x", 1)
    await h.wait_until_idle()
    assert log == [("load", 1), ("unload", 1), ("load", 1)]


async def test_current_entry_returns_the_newest_provider():
    h = Harness()
    ctx = h.create_context()
    assert h.reflect.current_entry("x") is None
    ctx.provide("x", 1)
    first = h.reflect.current_entry("x")
    assert first is not None and first[1] == 1
    ctx.provide("x", 2)
    second = h.reflect.current_entry("x")
    assert second is not None
    assert second[1] == 2 and second[0] != first[0]
