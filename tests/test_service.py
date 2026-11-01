from grapes.service import Service


def test_service_register_itself(ctx):
    class Greeter(Service):
        def __init__(self, ctx):
            super().__init__(ctx, "greeter")

    g = Greeter(ctx)
    assert ctx.lookup("greeter") is g


async def test_revert_all_removes_service(ctx):
    class Greeter(Service):
        def __init__(self, ctx):
            super().__init__(ctx, "greeter")

    Greeter(ctx)
    await ctx.revert_all()
    assert ctx.lookup("greeter") is None
