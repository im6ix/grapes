from .fiber import Fiber


class Registry:
    def __init__(self, harness):
        self.harness = harness
        self.fibers = []

    def use(self, ctx, plugin, inject=None):
        fiber = Fiber(self.harness, plugin, inject)
        self.fibers.append(fiber)

        def setup():
            fiber.refresh()

        def teardown():
            fiber.deactivate()
            self.fibers.remove(fiber)

        return ctx.effect(setup, teardown)
