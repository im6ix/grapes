from __future__ import annotations

from typing import Callable

from .context import Context
from .events import Events
from .reflect import Reflect
from .registry import Registry
from .logger import Logger


class Harness:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., object]] = {}
        self.reflect = Reflect(self)
        self.registry = Registry(self)
        self.events = Events(self)
        self.logger = Logger()

    def create_context(self) -> Context:
        return Context(self)
