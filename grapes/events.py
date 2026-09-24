from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Disposer, Handler
    from .harness import Harness


class Events:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.listeners: dict[str, list[Handler]] = {}

    def on(self, ctx: Context, name: str, handler: Handler) -> Disposer:
        def setup() -> None:
            self.listeners.setdefault(name, []).append(handler)

        def teardown() -> None:
            self.listeners[name].remove(handler)

        return ctx.effect(setup, teardown)

    def emit(self, name: str, *args: object) -> None:
        for handler in self.listeners.get(name, []):
            handler(*args)
