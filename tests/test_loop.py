from grapes import Harness
from grapes.agent import run


def test_loop_runs_a_tool_then_answers():
    h = Harness()
    ctx = h.create_context()
    ctx.register_tool("add", lambda a, b: a + b)

    def fake_model(messages):
        if any(m["role"] == "tool" for m in messages):
            return {"type": "answer", "content": messages[-1]["content"]}
        return {"type": "tool", "id": "call_1", "name": "add", "args": {"a": 2, "b": 2}}

    assert run(ctx, fake_model, "what is 2+2") == "4"
