from grapes import Harness


def test_undo_removes_the_tool():
    h = Harness()
    ctx = h.create_context()
    ctx.register_tool("add", lambda a, b: a + b)
    ctx.undo()

    assert "add" not in h.tools
