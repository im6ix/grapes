# grapes

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![tests](https://github.com/im6ix/grapes/actions/workflows/tests.yml/badge.svg)](https://github.com/im6ix/grapes/actions/workflows/tests.yml)
[![Status: experimental](https://img.shields.io/badge/status-experimental-orange)](#status)

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

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
uv run python main.py
```

`main.py` needs an `OPENCODE_API_KEY` (or a credential in OpenCode's local
store). The tests need neither.

## Status

- [x] Revertible effects: `ctx.effect(setup, teardown)` is the single mutation
      primitive; every change flows through it.
- [x] Tools carry a description + JSON Schema: `ctx.register_tool(name, func, *,
      description, parameters)` stores them (still on top of `effect`), and
      `ctx.tool_schemas()` returns them in the OpenAI function-calling shape.
      Unmounting a plugin removes its schemas automatically.
- [x] `ctx.mount(plugin)` mounts a plugin in its own child context and returns a
      `dispose`; a parent `ctx.revert_all()` cascades to its children.
- [x] Spatial composability (basic): a plugin with `inject` keys activates when
      they are provided and deactivates when they are withdrawn. `ctx.provide` /
      `ctx.lookup` provide and read values, and `Service` is the base class for
      providing a capability.
- [x] Provider identity: every provided value carries a ticket, and a fiber
      reloads when the ticket for one of its inject keys changes -- even if the
      new value is equal.
- [x] Committed view: a plugin's teardown sees the injected values it loaded
      with, even after a provider is removed or replaced.
- [x] Events: `ctx.subscribe(event, handler)` / `ctx.publish(event, ...)`;
      subscriptions are revertible effects.
- [x] Logger: `ctx.logger.info / warn / error`.
- [x] Agent loop: `run_agent(ctx, message)` drives model → tool → model until an
      answer. The model is a plain async `(messages, tools) -> reply` function,
      so it can be faked in tests.
- [x] Real model: `grapes/agent/model.py` talks to an OpenAI-compatible chat API
      (opencode-go) and turns tool calls into loop replies, which `run_agent`
      executes.
- [x] The model sees the registered tools: `run_agent` passes
      `ctx.tool_schemas()` to the adapter every turn.
- [ ] Component loader: configuration reconciliation and hot module replacement.

## Usage

```python
import asyncio

from grapes import Harness
from grapes.plugins import calculator_plugin


async def main() -> None:
    h = Harness()
    ctx = h.create_context()

    dispose = await ctx.mount(calculator_plugin)   # mount the plugin
    print(h.tools["add"].func(3, 5))         # 8

    await dispose()                              # unload just this plugin
    print(h.tools)                               # {}


asyncio.run(main())
```

### An agent that uses a tool

```python
import asyncio

from grapes import Harness
from grapes.agent import run_agent
from grapes.agent.llm import Llm, llm_plugin


async def fake_model(messages, tools):
    if any(message["role"] == "tool" for message in messages):
        return {"type": "answer", "content": messages[-1]["content"]}
    return {
        "type": "tool",
        "id": "call_1",
        "name": "add",
        "args": {"a": 2, "b": 3},
    }


async def main() -> None:
    h = Harness()
    ctx = h.create_context()
    ctx.register_tool(
        "add",
        lambda a, b: a + b,
        description="Add two integers",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )

    await ctx.mount(llm_plugin)
    llm = ctx.lookup("llm")
    assert isinstance(llm, Llm)
    llm.register_adapter(ctx, fake_model)

    print(await run_agent(ctx, "Use the add tool to add 2 and 3."))  # 5


asyncio.run(main())
```

The adapter is a plain async `(messages, tools) -> reply` function, so tests can
pass a fake. The real one speaks an OpenAI-compatible chat API; the nested wire
format is confined to `grapes/agent/model.py`.

## Tests

```
uv run pytest
```

(or `.venv/bin/python -m pytest`)

## Layout

```
grapes/
  harness.py      # Harness: the shared world (reflect + registry + tools)
  context.py      # Context: a scope; effects + the tool API (register/call/schemas)
  fiber.py        # Fiber: one mounted plugin instance and its lifecycle
  reflect.py      # Reflect: provider stacks (provide / current_entry / value)
  registry.py     # Registry: the mounted fibers + the mount operation
  service.py      # Service: base class for a plugin that provides a capability
  events.py       # Events: ctx.subscribe / ctx.publish
  logger.py       # Logger: ctx.logger.info / warn / error
  agent/
    loop.py       # run_agent(): model -> tool -> model, capped by max_steps
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

## License

MIT. See [LICENSE](LICENSE).
