from grapes.plugins.calculator import calculator_plugin
from grapes.context import Context


class FakeHarness:
    def __init__(self):
        self.tools = {}


def make_context():
    return Context(FakeHarness())


def test_add_tool_adds_numbers():
    ctx = make_context()
    calculator_plugin(ctx)
    add = ctx._harness.tools["add"]
    assert add(2, 3) == 5


def test_divide_tool_divides_numbers():
    ctx = make_context()
    calculator_plugin(ctx)
    divide = ctx._harness.tools["divide"]
    assert divide(10, 2) == 5
