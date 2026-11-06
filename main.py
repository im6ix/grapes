import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from grapes import Harness
from grapes.agent.chat import Chat
from grapes.agent.llm import llm_plugin
from grapes.agent.model import current_model, list_models, model_plugin, set_model
from grapes.agent.session import SessionStore, default_sessions_dir
from grapes.plugins import calculator_plugin
from grapes.plugins.workspace import workspace_plugin


async def main() -> None:
    h = Harness()
    ctx = h.create_context()
    await ctx.mount(calculator_plugin)
    await ctx.mount(workspace_plugin(Path.cwd(), make_approver()))
    print(f"workspace: {Path.cwd()}")
    await ctx.mount(llm_plugin)
    await ctx.mount(model_plugin, inject=["llm"])
    store = SessionStore(default_sessions_dir())
    session = store.create()
    chat = Chat(ctx, session)
    print(f"session file: {session.path}")
    print(f"model: {current_model()}")
    print(f"grapes chat - session {session.id} -'quit' or Ctrl-D to exit")
    try:
        while True:
            try:
                line = input(f"\n[{session.id[-6:]}] > ").strip()
            except EOFError:
                break
            if not line or line in {"quit", "exit"}:
                break
            if line == "/model":
                try:
                    models = list_models()
                except Exception as error:
                    print("could not list models:", error)
                    continue
                chosen = choose(models, "model")
                if chosen:
                    set_model(chosen)
                    print("model:", chosen)
                continue

            if line == "/sessions":
                choices = []
                for header in store.list():
                    stamp = datetime.fromtimestamp(
                        header["created_at"] / 1000, tz=UTC
                    ).astimezone()
                    choices.append(f"{header['id']}  {stamp:%Y-%m-%d %H:%M}")
                chosen = choose(choices, "session")
                if chosen:
                    session = store.open(chosen.split()[0])
                    chat = Chat(ctx, session)
                    print(f"resumed: {session.id}")
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
                print("/model | /sessions | /resume <id> | /new | quit")
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


def choose(options: list[str], prompt: str) -> str | None:
    for number, option in enumerate(options, 1):
        print(f"{number:2}  {option}")
    answer = input(f"{prompt} number (blank cancels): ").strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(options):
        return None
    return options[int(answer) - 1]


def make_approver():
    grants: list[Path] = []

    def approve(path: Path, action: str) -> bool:
        for grant in grants:
            if grant == path:
                return True
            if grant.is_dir() and path.is_relative_to(grant):
                return True
        answer = (
            input(f"{action} access to {path}? [y] once / [a] always / [n] no:")
            .strip()
            .lower()
        )

        if answer == "y":
            return True
        if answer == "a":
            grants.append(path)
            return True
        return False

    return approve


asyncio.run(main())
