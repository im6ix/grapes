from grapes import Harness
from grapes import Context
from grapes.plugins import calculator_plugin, file_search_plugin, greeter_plugin


def test_undo_removes_the_tool():
    h = Harness()
    ctx = h.create_context()
    ctx.register_tool("add", lambda a, b: a + b)
    ctx.undo()

    assert "add" not in h.tools


def test_two_contexts():
    h = Harness()
    ctx_a = h.create_context()
    calculator_plugin(ctx_a)
    ctx_b = h.create_context()
    file_search_plugin(ctx_b)
    ctx_a.undo()

    assert "add" not in h.tools
    assert "search_file" in h.tools


def test_child_ctx():
    h = Harness()
    ctx = h.create_context()
    dispose_calc = ctx.use(calculator_plugin)
    dispose_search = ctx.use(file_search_plugin)
    dispose_calc()
    assert "add" not in h.tools
    assert "search_file" in h.tools


def test_parent_sees_child():
    h = Harness()
    ctx = h.create_context()
    dispose_calc = ctx.use(calculator_plugin)
    dispose_search = ctx.use(file_search_plugin)
    ctx.undo()
    assert "add" not in h.tools
    assert "search_file" not in h.tools


def test_set_get_and_undo_value():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "en")
    assert ctx.get("language") == "en"
    ctx.undo()
    assert ctx.get("language") is None


def test_plugin_dependency_missing():
    h = Harness()
    ctx = h.create_context()
    ctx.use(greeter_plugin, inject=["language"])
    assert "greet" not in h.tools


def test_plugin_dependency_present():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "en")
    ctx.use(greeter_plugin, inject=["language"])
    assert "greet" in h.tools


def test_dependency_satisfied_by_falsy_value():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "")
    ctx.use(greeter_plugin, inject=["language"])
    assert "greet" in h.tools


def test_activate_automatically():
    h = Harness()
    ctx = h.create_context()
    ctx.use(greeter_plugin, inject=["language"])
    assert "greet" not in h.tools
    ctx.set("language", "en")
    assert "greet" in h.tools
