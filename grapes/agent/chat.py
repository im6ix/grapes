from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context
    from .session import Session

from .loop import run_agent


class Chat:
    def __init__(self, ctx: Context, session: Session) -> None:
        self.ctx: Context = ctx
        self.session: Session = session
        self.messages = session.messages()

    async def ask(self, message: str) -> str:
        before = len(self.messages)
        answer = await run_agent(self.ctx, message, messages=self.messages)

        for entry in self.messages[before:]:
            self.session.append("message", entry)

        return answer
