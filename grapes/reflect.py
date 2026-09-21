class Reflect:
    def __init__(self, harness):
        self.harness = harness
        self.values = {}

    def get(self, name):
        return self.values.get(name)

    def provide(self, ctx, name, value):
        def setup():
            self.values[name] = value
            self.notify()

        def teardown():
            self.values.pop(name, None)
            self.notify()

        return ctx.effect(setup, teardown)

    def notify(self):
        for fiber in self.harness.registry.fibers:
            fiber.refresh()
