from grapes import Harness


def test_register_and_emit():
    h = Harness()
    ctx = h.create_context()
    calls = []

    def handler(value):
        calls.append(value)

    ctx.on("ping", handler)
    ctx.emit("ping", 1)
    assert calls == [1]


async def test_undo_removes_listener():
    h = Harness()
    ctx = h.create_context()
    calls = []

    def handler(value):
        calls.append(value)

    ctx.on("ping", handler)
    await ctx.undo()
    ctx.emit("ping", 1)
    assert calls == []
