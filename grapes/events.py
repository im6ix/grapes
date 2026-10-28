from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Disposer, Handler
    from .harness import Harness


class Events:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.subscriptions: dict[str, list[Handler]] = {}

    def subscribe(self, ctx: Context, event: str, handler: Handler) -> Disposer:
        def setup() -> None:
            self.subscriptions.setdefault(event, []).append(handler)

        def teardown() -> None:
            self.subscriptions[event].remove(handler)

        return ctx.effect(setup, teardown)

    def publish(self, event: str, *args: object) -> None:
        for handler in self.subscriptions.get(event, []):
            handler(*args)
