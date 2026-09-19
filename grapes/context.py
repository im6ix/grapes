from .fiber import Fiber


class Context:
    def __init__(self, harness):
        self._harness = harness
        self._effects = []

    def register_tool(self, name, func):
        def setup():
            self._harness.tools[name] = func

        def teardown():
            self._harness.tools.pop(name, None)

        self.effect(setup, teardown)

        print(f"Registered new tool: {name}")

    def undo(self):
        for undo_func in reversed(self._effects):
            undo_func()

        self._effects.clear()

    def effect(self, setup, teardown):
        setup()
        armed = True

        def dispose():
            nonlocal armed
            if not armed:
                return
            armed = False
            teardown()

        self._effects.append(dispose)
        return dispose

    def use(self, plugin, inject=None):
        fiber = Fiber(self._harness, plugin, inject)
        self._harness.fibers.append(fiber)

        def setup():
            fiber.refresh()

        def teardown():
            fiber.deactivate()
            self._harness.fibers.remove(fiber)

        return self.effect(setup, teardown)

    def set(self, key, value):
        def setup():
            self._harness.values[key] = value
            self._refresh_all()

        def teardown():
            self._harness.values.pop(key, None)
            self._refresh_all()

        return self.effect(setup, teardown)

    def get(self, key):
        return self._harness.values.get(key)

    def _refresh_all(self):
        for fiber in self._harness.fibers:
            fiber.refresh()
