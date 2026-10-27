from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Awaitable
from ..service import Service

if TYPE_CHECKING:
    from ..context import Context, Disposer

Adapter = Callable[[list[dict], list[dict]], Awaitable[dict]]


class Llm(Service):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "llm")
        self._adapter: Adapter | None = None

    def register(self, ctx: Context, adapter: Adapter) -> Disposer:
        def setup() -> None:
            self._adapter = adapter

        def teardown() -> None:
            self._adapter = None

        return ctx.effect(setup, teardown)

    async def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        if self._adapter is None:
            raise RuntimeError("no llm adapter register")
        return await self._adapter(messages, tools)


def llm_plugin(ctx: Context) -> None:
    Llm(ctx)
