from .registry import Registry
from .context import Context
from .reflect import Reflect


class Harness:
    def __init__(self):
        self.tools = {}
        self.reflect = Reflect(self)
        self.registry = Registry(self)

    def create_context(self):
        return Context(self)
