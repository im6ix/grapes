from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context


class Service:
    def __init__(self, ctx: Context, name: str) -> None:
        self.ctx = ctx
        self.name = name

        ctx.set(name, self)
