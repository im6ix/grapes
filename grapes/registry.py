from __future__ import annotations

from typing import TYPE_CHECKING

from .fiber import Fiber

if TYPE_CHECKING:
    from .context import Context, Disposer, Plugin
    from .harness import Harness


class Registry:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.fibers: list[Fiber] = []

    def use(
        self, ctx: Context, plugin: Plugin, inject: list[str] | None = None
    ) -> Disposer:
        fiber = Fiber(self.harness, plugin, inject)
        self.fibers.append(fiber)

        def setup() -> None:
            fiber.refresh()

        def teardown() -> None:
            fiber.deactivate()
            self.fibers.remove(fiber)

        return ctx.effect(setup, teardown)
