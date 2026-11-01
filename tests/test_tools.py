def test_register_tool_exposes_its_schema(ctx, two_ints):
    ctx.register_tool(
        "add",
        lambda a, b: a + b,
        description="Add two integers",
        parameters=two_ints,
    )

    expected = [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two integers",
                "parameters": two_ints,
            },
        }
    ]
    assert ctx.tool_schemas() == expected
