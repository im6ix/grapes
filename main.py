from grapes import Harness
from grapes.plugins import calculator_plugin, file_search_plugin


h = Harness()
ctx = h.create_context()
calculator_plugin(ctx)

print(ctx._harness.tools["add"](3, 5))
ctx.undo()
print(ctx._harness.tools)
