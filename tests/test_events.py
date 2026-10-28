from grapes import Harness


def test_subscribe_and_publish():
    h = Harness()
    ctx = h.create_context()
    calls = []

    def handler(value):
        calls.append(value)

    ctx.subscribe("ping", handler)
    ctx.publish("ping", 1)
    assert calls == [1]


async def test_revert_all_removes_subscription():
    h = Harness()
    ctx = h.create_context()
    calls = []

    def handler(value):
        calls.append(value)

    ctx.subscribe("ping", handler)
    await ctx.revert_all()
    ctx.publish("ping", 1)
    assert calls == []
