from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .harness import Harness


# A plugin is a function that runs against a context and installs effects on it.
Plugin = Callable[["Context"], None]
# An event handler receives whatever `emit` was called with.
Handler = Callable[..., None]
# A disposer undoes one effect; `effect` returns one.
Disposer = Callable[[], None]


class Context:
    def __init__(self, harness: Harness) -> None:
        self._harness = harness
        self._effects: list[Disposer] = []

    def register_tool(self, name: str, func: Callable[..., object]) -> None:
        def setup() -> None:
            self._harness.tools[name] = func

        def teardown() -> None:
            self._harness.tools.pop(name, None)

        self.effect(setup, teardown)

        print(f"Registered new tool: {name}")

    def undo(self) -> None:
        for undo_func in reversed(self._effects):
            undo_func()

        self._effects.clear()

    def effect(self, setup: Disposer, teardown: Disposer) -> Disposer:
        setup()
        armed = True

        def dispose() -> None:
            nonlocal armed
            if not armed:
                return
            armed = False
            teardown()

        self._effects.append(dispose)
        return dispose

    def use(self, plugin: Plugin, inject: list[str] | None = None) -> Disposer:
        return self._harness.registry.use(self, plugin, inject)

    def set(self, key: str, value: object) -> Disposer:
        return self._harness.reflect.provide(self, key, value)

    def get(self, key: str) -> object | None:
        return self._harness.reflect.get(key)

    def on(self, name: str, handler: Handler) -> Disposer:
        return self._harness.events.on(self, name, handler)

    def emit(self, name: str, *args: object) -> None:
        self._harness.events.emit(name, *args)
