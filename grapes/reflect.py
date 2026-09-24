from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Disposer
    from .harness import Harness


class Reflect:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.values: dict[str, object] = {}

    def get(self, name: str) -> object | None:
        return self.values.get(name)

    def provide(self, ctx: Context, name: str, value: object) -> Disposer:
        def setup() -> None:
            self.values[name] = value
            self.notify()

        def teardown() -> None:
            self.values.pop(name, None)
            self.notify()

        return ctx.effect(setup, teardown)

    def notify(self) -> None:
        for fiber in self.harness.registry.fibers:
            fiber.refresh()
