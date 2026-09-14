def calculator_plugin(ctx):
    ctx.register_tool("add", lambda a, b: a + b)
    ctx.register_tool("subtract", lambda a, b: a - b)
    ctx.register_tool("multiply", lambda a, b: a * b)
    ctx.register_tool("divide", lambda a, b: a / b)
