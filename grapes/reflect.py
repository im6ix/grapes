from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Disposer
    from .harness import Harness


class Reflect:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        # Name -> stack of (token, value). newest provider is last.
        self.providers: dict[str, list[tuple[object, object]]] = {}

    def get(self, name: str) -> object | None:
        return self.values.get(name)

    @property
    def values(self) -> dict[str, object]:
        return {name: stack[-1][1] for name, stack in self.providers.items()}

    def provide(self, ctx: Context, name: str, value: object) -> Disposer:
        entry = (object(), value)

        def setup() -> None:
            self.providers.setdefault(name, []).append(entry)
            self.notify()

        def teardown() -> None:
            stack = self.providers.get(name)
            if stack and entry in stack:
                stack.remove(entry)
            if not stack:
                self.providers.pop(name, None)
            self.notify()

        return ctx.effect(setup, teardown)

    def notify(self) -> None:
        for fiber in self.harness.registry.fibers:
            fiber.refresh()
