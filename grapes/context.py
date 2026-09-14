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
        self._effects.append(teardown)
