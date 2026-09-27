from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Any, Awaitable
import inspect

if TYPE_CHECKING:
    from .harness import Harness


# A plugin is a function that runs against a context and installs effects on it.
Plugin = Callable[["Context"], Awaitable[None] | None]
# An event handler receives whatever `emit` was called with.
Handler = Callable[..., None]
# A disposer undoes one effect; `effect` returns one.
Disposer = Callable[[], Awaitable[None]]
Teardown = Callable[[], Awaitable[None] | None]


async def _settle(result: Any) -> None:
    if inspect.isawaitable(result):
        await result


class Context:
    def __init__(self, harness: Harness) -> None:
        self._harness = harness
        self._effects: list[Disposer] = []
        self.logger = harness.logger

    def register_tool(self, name: str, func: Callable[..., object]) -> None:
        def setup() -> None:
            self._harness.tools[name] = func

        def teardown() -> None:
            self._harness.tools.pop(name, None)

        self.effect(setup, teardown)

        print(f"Registered new tool: {name}")

    def call_tool(self, name: str, *args: object, **kwargs: object) -> object:
        return self._harness.tools[name](*args, **kwargs)

    async def undo(self) -> None:
        for dispose in reversed(self._effects):
            await dispose()
        self._effects.clear()

    def effect(self, setup: Callable[[], object], teardown: Teardown) -> Disposer:
        setup()
        armed = True

        async def dispose() -> None:
            nonlocal armed
            if not armed:
                return
            armed = False
            await _settle(teardown())

        self._effects.append(dispose)
        return dispose

    async def use(self, plugin: Plugin, inject: list[str] | None = None) -> Disposer:
        return await self._harness.registry.use(self, plugin, inject)

    def set(self, key: str, value: object) -> Disposer:
        return self._harness.reflect.provide(self, key, value)

    def get(self, key: str) -> object | None:
        return self._harness.reflect.get(key)

    def on(self, name: str, handler: Handler) -> Disposer:
        return self._harness.events.on(self, name, handler)

    def emit(self, name: str, *args: object) -> None:
        self._harness.events.emit(name, *args)
