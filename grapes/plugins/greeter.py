def greeter_plugin(ctx):
    ctx.register_tool("greet", lambda: "hello")
