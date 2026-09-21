from grapes import Harness
from grapes.plugins import calculator_plugin, file_search_plugin, greeter_plugin


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


def test_dispose_then_undo_is_safe():
    h = Harness()
    ctx = h.create_context()
    dispose = ctx.use(greeter_plugin)
    dispose()
    ctx.undo()
    assert "greet" not in h.tools
