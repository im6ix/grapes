from grapes import Harness
from grapes.agent.chat import Chat
from grapes.agent.llm import Llm, llm_plugin
from grapes.agent.session import SessionStore


async def test_chat_persists_and_replays_a_turn(tmp_path):
    store = SessionStore(tmp_path)
    session = store.create()

    h = Harness()
    ctx = h.create_context()

    seen = []

    async def fake_model(messages, tools):
        seen.append([message["role"] for message in messages])
        return {"type": "answer", "content": "ok"}

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    chat = Chat(ctx, session)
    assert await chat.ask("first") == "ok"

    reopened = store.open(session.id)
    assert reopened.messages() == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ok"},
    ]

    resumed = Chat(ctx, reopened)
    assert await resumed.ask("second") == "ok"

    assert seen == [["user"], ["user", "assistant", "user"]]

    final = store.open(session.id)
    assert [entry["id"] for entry in final.entries] == ["e1", "e2", "e3", "e4"]
    assert final.entries[2]["parent_id"] == "e2"


async def test_chat_persists_a_tool_turn(tmp_path):
    store = SessionStore(tmp_path)
    session = store.create()

    h = Harness()
    ctx = h.create_context()
    ctx.register_tool(
        "add",
        lambda a, b: a + b,
        description="Add two integers",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )

    async def fake_model(messages, tools):
        if any(message["role"] == "tool" for message in messages):
            return {"type": "answer", "content": messages[-1]["content"]}
        return {"type": "tool", "id": "call_1", "name": "add", "args": {"a": 2, "b": 3}}

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    chat = Chat(ctx, session)
    assert await chat.ask("add 2 and 3") == "5"

    messages = store.open(session.id).messages()

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]
    assert messages[1]["tool_calls"][0]["id"] == "call_1"
    assert messages[2]["tool_call_id"] == "call_1"
    assert messages[2]["content"] == "5"
    assert messages[3]["content"] == "5"
