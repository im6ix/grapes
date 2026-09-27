from __future__ import annotations

import asyncio
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

    async def settle(self) -> None:
        # Keep waiting as long as any fiber has a task in flight.
        # A finished transition can chain another one (_settle -> _drive),
        # so we re-check after every gather instead of just once.
        while True:
            tasks = [f.inertia for f in self.registry.fibers if f.inertia is not None]
            if not tasks:
                return
            await asyncio.gather(*tasks)
