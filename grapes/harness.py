from .context import Context


class Harness:
    def __init__(self):
        self.tools = {}
        self.values = {}
        self.plugins = []
        self.fibers = []

    def create_context(self):
        return Context(self)
