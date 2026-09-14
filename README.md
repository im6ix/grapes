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
  deactivate as those dependencies appear and disappear. *(not built yet)*

## Status

- [x] Revertible effects: `ctx.effect(setup, teardown)` is the single mutation
      primitive; every change flows through it.
- [x] `ctx.register_tool` implemented on top of `effect`.
- [x] `ctx.use(plugin)` mounts a plugin in its own child context and returns a
      `dispose`; a parent `ctx.undo()` cascades to its children.
- [ ] Spatial composability (coeffects): declared dependencies that drive
      activation.
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
  harness.py      # Harness: the shared world (holds the tool registry)
  context.py      # Context: a scope that tracks and reverts its effects
  plugins/        # example plugins (calculator, file_search)
  registry.py     # unused: an earlier experimental tool registry
tests/            # tests
docs/             # the reference paper
main.py           # scratch entry point
```

## Reference

The design follows *A Programming Paradigm for Spatiotemporal Composability*
(Shi, Zhang, Cui; Peking University / DeepSeek-AI), which implements these
ideas in a meta-framework called Cordis.
