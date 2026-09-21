from grapes import Harness


def test_set_get_and_undo_value():
    h = Harness()
    ctx = h.create_context()
    ctx.set("language", "en")
    assert ctx.get("language") == "en"
    ctx.undo()
    assert ctx.get("language") is None
