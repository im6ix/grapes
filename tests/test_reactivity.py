from grapes import Harness
from grapes.plugins import calculator_plugin, file_search_plugin, greeter_plugin


async def test_two_contexts():
    h = Harness()
    ctx_a = h.create_context()
    calculator_plugin(ctx_a)
    ctx_b = h.create_context()
    file_search_plugin(ctx_b)
    await ctx_a.revert_all()

    assert "add" not in h.tools
    assert "search_file" in h.tools


async def test_plugin_dependency_missing():
    h = Harness()
    ctx = h.create_context()
    await ctx.mount(greeter_plugin, inject=["language"])
    assert "greet" not in h.tools


async def test_plugin_dependency_present():
    h = Harness()
    ctx = h.create_context()
    ctx.provide("language", "en")
    await ctx.mount(greeter_plugin, inject=["language"])
    assert "greet" in h.tools


async def test_dependency_satisfied_by_falsy_value():
    h = Harness()
    ctx = h.create_context()
    ctx.provide("language", "")
    await ctx.mount(greeter_plugin, inject=["language"])
    assert "greet" in h.tools


async def test_activate_automatically():
    h = Harness()
    ctx = h.create_context()
    await ctx.mount(greeter_plugin, inject=["language"])
    assert "greet" not in h.tools

    ctx.provide("language", "en")
    await h.wait_until_idle()
    assert "greet" in h.tools


async def test_deactivation_when_value_removed():
    h = Harness()
    ctx = h.create_context()
    await ctx.mount(greeter_plugin, inject=["language"])

    remove = ctx.provide("language", "en")
    await h.wait_until_idle()
    assert "greet" in h.tools

    await remove()
    await h.wait_until_idle()
    assert "greet" not in h.tools
