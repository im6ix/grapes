from grapes import Harness
from grapes.agent.llm import Llm, llm_plugin
from grapes.agent.model import _reply_from
import grapes.agent.model as model_module
import pytest


def test_answer():
    message = {"content": "paris"}
    assert _reply_from(message) == {"type": "answer", "content": "paris"}


def test_tool_call():
    message = {
        "content": "",
        "tool_calls": [
            {
                "id": "call_abc",
                "type": "function",
                "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
            }
        ],
    }
    assert _reply_from(message) == {
        "type": "tool",
        "id": "call_abc",
        "name": "add",
        "args": {"a": 2, "b": 3},
    }


async def test_model_forwards_tool_schemas_to_the_wire(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_chat(messages, model="qwen3.8-flash", tools=None):
        captured["message"] = messages
        captured["tools"] = tools
        return {"content": "paris"}

    monkeypatch.setattr(model_module, "_chat", fake_chat)

    tools = [{"type": "function", "function": {"name": "add"}}]
    reply = await model_module.model([{"role": "user", "content": "hi"}], tools)

    assert captured["tools"] == tools
    assert reply == {"type": "answer", "content": "paris"}


async def test_model_plugin_fills_and_clears_the_slot():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(llm_plugin)
    llm = ctx.get("llm")
    assert isinstance(llm, Llm)

    dispose = await ctx.use(model_module.model_plugin, inject=["llm"])
    assert llm._adapter is model_module.model

    await dispose()
    assert llm._adapter is None
