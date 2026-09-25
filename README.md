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
- [x] Events: `ctx.on(name, handler)` / `ctx.emit(name, ...)`; listeners are
      revertible effects.
- [x] Logger: `ctx.logger.info / warn / error`.
- [x] Agent loop: `run(ctx, model, message)` drives model → tool → model until an
      answer. The model is a plain function, so it can be faked in tests.
- [x] Real model: `grapes/agent/model.py` talks to an OpenAI-compatible chat API
      (opencode-go) and turns tool calls into loop replies, which `run` executes.
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

### An agent that uses a tool

```python
from grapes import Harness
from grapes.agent import run
from grapes.agent.model import model

h = Harness()
ctx = h.create_context()
ctx.register_tool("add", lambda a, b: a + b)

print(run(ctx, model, "Use the add tool to add 2 and 3."))   # 5
```

The model is a plain function (`messages -> reply`), so tests can pass a fake.
The real one speaks an OpenAI-compatible chat API; the nested wire format is
confined to `grapes/agent/model.py`.

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
  events.py       # Events: ctx.on / ctx.emit
  logger.py       # Logger: ctx.logger.info / warn / error
  agent/
    loop.py       # run(): model -> tool -> model, capped by max_steps
    model.py      # the real model: OpenAI-compatible chat API (opencode-go)
  plugins/        # example plugins (calculator, file_search, greeter)
tests/            # one test file per concern
docs/             # the reference paper
main.py           # scratch entry point
```

## Reference

The design follows *A Programming Paradigm for Spatiotemporal Composability*
(Shi, Zhang, Cui; Peking University / DeepSeek-AI), which implements these
ideas in a meta-framework called Cordis.
