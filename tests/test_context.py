from grapes import Harness
from grapes import Context
from grapes.plugins import calculator_plugin, file_search_plugin


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
