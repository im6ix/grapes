from .context import Context


class Harness:
    def __init__(self):
        self.tools = {}
        self.plugins = []

    def create_context(self):
        return Context(self)
