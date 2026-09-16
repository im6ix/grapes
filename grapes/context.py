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
        comp = {
            "plugin": plugin,
            "inject": inject or [],
            "child": child,
            "active": False,
        }
        self._harness.components.append(comp)

        def setup():
            self._refresh(comp)

        def teardown():
            if comp["active"]:
                child.undo()
                comp["active"] = False
            self._harness.components.remove(comp)

        self.effect(setup, teardown)
        return teardown

    def set(self, key, value):
        def setup():
            self._harness.values[key] = value
            self._refresh_all()

        def teardown():
            self._harness.values.pop(key, None)
            self._refresh_all()

        self.effect(setup, teardown)

    def get(self, key):
        return self._harness.values.get(key)

    def _refresh(self, comp):
        satisfied = all(key in self._harness.values for key in comp["inject"])

        if satisfied and not comp["active"]:
            comp["plugin"](comp["child"])  # -> run the plugin on the child
            comp["active"] = True
        elif not satisfied and comp["active"]:
            comp["child"].undo()
            comp["active"] = False

    def _refresh_all(self):
        for comp in self._harness.components:
            self._refresh(comp)
