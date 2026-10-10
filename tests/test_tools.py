from grapes import Harness


def test_register_tool_exposes_its_schema():
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

    expected = [
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
    assert ctx.tool_schemas() == expected
