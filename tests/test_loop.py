from grapes import Harness
from grapes.agent import run_agent
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

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    assert await run_agent(ctx, "what is 2+2") == "4"


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

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    await run_agent(ctx, "hi")
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


async def test_loop_reports_tool_errors_to_the_model():
    h = Harness()
    ctx = h.create_context()

    def explode():
        raise ValueError("bad input")

    ctx.register_tool(
        "explode",
        explode,
        description="Always fails",
        parameters={"type": "object", "properties": {}},
    )

    seen_tool = []

    async def fake_model(messages, tools):
        if any(message["role"] == "tool" for message in messages):
            seen_tool.append(messages[-1])
            return {"type": "answer", "content": "saw error"}
        return {"type": "tool", "id": "call_1", "name": "explode", "args": {}}

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    assert await run_agent(ctx, "try it") == "saw error"
    assert seen_tool == [
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "ERROR: ValueError: bad input",
        }
    ]


async def test_loop_awaits_async_tools():
    h = Harness()
    ctx = h.create_context()

    async def async_add(a, b):
        return a + b

    ctx.register_tool(
        "async_add",
        async_add,
        description="Add two integers asynchronously",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )

    async def fake_model(messages, tools):
        if any(message["role"] == "tool" for message in messages):
            return {"type": "answer", "content": messages[-1]["content"]}
        return {
            "type": "tool",
            "id": "call_1",
            "name": "async_add",
            "args": {"a": 2, "b": 3},
        }

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    assert await run_agent(ctx, "add 2 and 3") == "5"
