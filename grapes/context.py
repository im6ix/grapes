from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Any, Awaitable
from dataclasses import dataclass
import inspect

if TYPE_CHECKING:
    from .harness import Harness


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    func: Callable[..., object]


# A plugin is a function that runs against a context and installs effects on it.
Plugin = Callable[["Context"], Awaitable[None] | None]
# An event handler receives whatever `publish` was called with.
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

    def register_tool(
        self,
        name: str,
        func: Callable[..., object],
        *,
        description: str,
        parameters: dict[str, object],
    ) -> None:
        tool = Tool(name, description, parameters, func)

        def setup() -> None:
            self._harness.tools[name] = tool

        def teardown() -> None:
            self._harness.tools.pop(name, None)
            self.logger.info(f"removed tool: {name}")

        self.effect(setup, teardown)
        self.logger.info(f"registered tool: {name}")

    def call_tool(self, name: str, *args: object, **kwargs: object) -> object:
        return self._harness.tools[name].func(*args, **kwargs)

    def tool_schemas(self) -> list[dict[str, object]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for name, tool in self._harness.tools.items()
        ]

    async def revert_all(self) -> None:
        for dispose in reversed(self._effects):
            try:
                await dispose()
            except Exception as error:
                self.logger.error(str(error))
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

    async def mount(self, plugin: Plugin, inject: list[str] | None = None) -> Disposer:
        return await self._harness.registry.mount(self, plugin, inject)

    def provide(self, name: str, value: object) -> Disposer:
        return self._harness.reflect.provide(self, name, value)

    def lookup(self, name: str) -> object | None:
        return self._harness.reflect.value(name)

    def subscribe(self, event: str, handler: Handler) -> Disposer:
        return self._harness.events.subscribe(self, event, handler)

    def publish(self, event: str, *args: object) -> None:
        self._harness.events.publish(event, *args)
