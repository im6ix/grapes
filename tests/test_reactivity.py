from grapes import Harness
from grapes.plugins import calculator_plugin, file_search_plugin, greeter_plugin


async def test_two_contexts():
    h = Harness()
    ctx_a = h.create_context()
    calculator_plugin(ctx_a)
    ctx_b = h.create_context()
    file_search_plugin(ctx_b)
    await ctx_a.undo()

    assert "add" not in h.tools
    assert "search_file" in h.tools


async def test_plugin_dependency_missing():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(greeter_plugin, inject=["language"])
    assert "greet" not in h.tools


async def test_plugin_dependency_present():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "en")
    await ctx.use(greeter_plugin, inject=["language"])
    assert "greet" in h.tools


async def test_dependency_satisfied_by_falsy_value():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "")
    await ctx.use(greeter_plugin, inject=["language"])
    assert "greet" in h.tools


async def test_activate_automatically():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(greeter_plugin, inject=["language"])
    assert "greet" not in h.tools

    ctx.set("language", "en")
    await h.settle()
    assert "greet" in h.tools


async def test_deactivation_when_value_removed():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(greeter_plugin, inject=["language"])

    remove = ctx.set("language", "en")
    await h.settle()
    assert "greet" in h.tools

    await remove()
    await h.settle()
    assert "greet" not in h.tools
