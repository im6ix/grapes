from grapes import Harness
from grapes.agent import run
from grapes.agent.llm import Llm, llm_plugin


async def test_loop_runs_a_tool_then_answers():
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
        if any(m["role"] == "tool" for m in messages):
            return {"type": "answer", "content": messages[-1]["content"]}
        return {"type": "tool", "id": "call_1", "name": "add", "args": {"a": 2, "b": 2}}

    await ctx.use(llm_plugin)
    llm = ctx.get("llm")
    assert isinstance(llm, Llm)
    llm.register(ctx, fake_model)

    assert await run(ctx, "what is 2+2") == "4"


async def test_loop_passes_tool_schemas_to_the_model():
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

    received = None

    async def fake_model(messages, tools):
        nonlocal received
        received = tools
        return {"type": "answer", "content": "done"}

    await ctx.use(llm_plugin)
    llm = ctx.get("llm")
    assert isinstance(llm, Llm)
    llm.register(ctx, fake_model)

    await run(ctx, "hi")
    assert received == [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two integers",
                "parameters": {
                    "type": "object",
                    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                    "required": ["a", "b"],
                },
            },
        }
    ]
