import asyncio
import time
import json
from datetime import datetime

from grapes import Harness
from grapes.plugins import calculator_plugin
from grapes.agent.chat import Chat
from grapes.agent.model import model_plugin
from grapes.agent.llm import llm_plugin
from grapes.agent.session import SessionStore, default_sessions_dir


async def main() -> None:
    h = Harness()
    ctx = h.create_context()
    await ctx.mount(calculator_plugin)
    await ctx.mount(llm_plugin)
    await ctx.mount(model_plugin, inject=["llm"])
    store = SessionStore(default_sessions_dir())
    session = store.create()
    chat = Chat(ctx, session)
    print(f"session file: {session.path}")
    print(f"grapes chat - session {session.id} -'quit' or Ctrl-D to exit")
    try:
        while True:
            try:
                line = input(f"\n[{session.id[-6:]}] > ").strip()
            except EOFError:
                break
            if not line or line in {"quit", "exit"}:
                break
            if line == "/sessions":
                for header in store.list():
                    stamp = datetime.fromtimestamp(header["created_at"] / 1000)
                    marker = "*" if header["id"] == session.id else " "
                    print(f"{marker} {header['id']} {stamp:%Y-%m-%d %H:%M}")
                continue

            if line == "/new":
                session = store.create()
                chat = Chat(ctx, session)
                print(f"new session: {session.id}")
                continue

            if line == "/resume":
                print("usage: /resume <session-id>")
                continue

            if line.startswith("/resume "):
                session_id = line.split(maxsplit=1)[1]
                if not (session_id.startswith("ses_") and session_id[4:].isalnum()):
                    print("invalid session id")
                    continue
                try:
                    session = store.open(session_id)
                except FileNotFoundError:
                    print("no such session:", session_id)
                    continue
                chat = Chat(ctx, session)
                print(f"resumed: {session.id}")
                continue

            if line == "/help":
                print("/sessions | /resume <id> | /new | quit")
                continue

            start = time.monotonic()
            answer = await chat.ask(line)
            print(
                f"{answer}        [{time.monotonic() - start:.1f}s, {len(json.dumps(chat.messages)) // 4} tok]"
            )
    except KeyboardInterrupt:
        pass
    finally:
        await ctx.revert_all()
        print("after revert_all, tools left:", ctx.tool_schemas())


asyncio.run(main())
