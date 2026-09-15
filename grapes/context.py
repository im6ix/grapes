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

    def use(self, plugin, inject=None):
        child = self._harness.create_context()
        inject = inject or []

        if all(key in self._harness.values for key in inject):

            def setup():
                plugin(child)

            self.effect(setup, child.undo)
        return child.undo

    def set(self, key, value):
        def setup():
            self._harness.values[key] = value

        def teardown():
            self._harness.values.pop(key, None)

        self.effect(setup, teardown)

    def get(self, key):
        return self._harness.values.get(key)
