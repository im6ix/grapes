from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..context import Context

from .loop import run_agent


class Chat:
    def __init__(self, ctx: Context) -> None:
        self.ctx: Context = ctx
        self.messages: list[dict[str, Any]] = []

    async def ask(self, message: str) -> str:
        return await run_agent(self.ctx, message, messages=self.messages)
