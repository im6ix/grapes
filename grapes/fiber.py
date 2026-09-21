class Fiber:
    def __init__(self, harness, plugin, inject):
        self.harness = harness
        self.plugin = plugin
        self.inject = inject or []
        self.ctx = harness.create_context()
        self.active = False

    def refresh(self):
        satisfied = all(key in self.harness.reflect.values for key in self.inject)

        if satisfied:
            self.activate()
        else:
            self.deactivate()

    def activate(self):
        if self.active:
            return
        self.plugin(self.ctx)
        self.active = True

    def deactivate(self):
        if not self.active:
            return
        self.ctx.undo()
        self.active = False
