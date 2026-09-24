from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Plugin
    from .harness import Harness


class Fiber:
    def __init__(
        self, harness: Harness, plugin: Plugin, inject: list[str] | None
    ) -> None:
        self.harness = harness
        self.plugin = plugin
        self.inject = inject or []
        self.ctx: Context = harness.create_context()
        self.active = False

    def refresh(self) -> None:
        satisfied = all(key in self.harness.reflect.values for key in self.inject)

        if satisfied:
            self.activate()
        else:
            self.deactivate()

    def activate(self) -> None:
        if self.active:
            return
        self.plugin(self.ctx)
        self.active = True

    def deactivate(self) -> None:
        if not self.active:
            return
        self.ctx.undo()
        self.active = False
