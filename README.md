# grapes

A tiny experimental AI harness where **everything is a plugin** — built from
scratch to understand dynamic composition, inspired by the Cordis paper
(see [Reference](#reference)).

## What it is

`grapes` is a small runtime for plugins that can be added and removed at
runtime without restarting and without disturbing each other. Every change a
plugin makes to the shared environment is tracked, so removing the plugin
undoes it completely.

Two ideas drive the design:

- **Temporal composability** — removing a plugin reverts everything it did.
- **Spatial composability** — plugins declare dependencies and activate /
  deactivate as those dependencies appear and disappear.

## Status

- [x] Revertible effects: `ctx.effect(setup, teardown)` is the single mutation
      primitive; every change flows through it.
- [x] `ctx.register_tool` implemented on top of `effect`.
- [x] `ctx.use(plugin)` mounts a plugin in its own child context and returns a
      `dispose`; a parent `ctx.undo()` cascades to its children.
- [x] Spatial composability (basic): a plugin with `inject` keys activates when
      they are provided and deactivates when they are withdrawn. `ctx.set` /
      `ctx.get` provide and read values, and `Service` is the base class for
      providing a capability.
- [ ] Component loader: configuration reconciliation and hot module replacement.

## Usage

```python
from grapes import Harness
from grapes.plugins import calculator_plugin

h = Harness()
ctx = h.create_context()

dispose = ctx.use(calculator_plugin)   # mount the plugin
print(h.tools["add"](3, 5))            # 8

dispose()                              # unload just this plugin
print(h.tools)                         # {}
```

## Tests

```
uv run pytest
```

(or `.venv/bin/python -m pytest`)

## Layout

```
grapes/
  harness.py      # Harness: the shared world (reflect + registry + tools)
  context.py      # Context: a scope that tracks and reverts its effects
  fiber.py        # Fiber: one mounted plugin instance and its lifecycle
  reflect.py      # Reflect: the value store (provide / get / notify)
  registry.py     # Registry: the mounted fibers + the mount operation
  service.py      # Service: base class for a plugin that provides a capability
  plugins/        # example plugins (calculator, file_search, greeter)
tests/            # one test file per concern
docs/             # the reference paper
main.py           # scratch entry point
```

## Reference

The design follows *A Programming Paradigm for Spatiotemporal Composability*
(Shi, Zhang, Cui; Peking University / DeepSeek-AI), which implements these
ideas in a meta-framework called Cordis.
