from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..context import Context

from .loop import run


class Chat:
    def __init__(self, ctx, model) -> None:
        self.ctx = ctx
        self.model = model
        self.messages: list[dict[str, Any]] = []

    def say(self, message: str) -> str:
        return run(self.ctx, self.model, message, messages=self.messages)
