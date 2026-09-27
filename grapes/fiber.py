"""One mounted plugin and its lifecycle.

This is a controller, not an event handler. It does not say "on event X, go to
state Y". It keeps two answers:
  - target: where we want to be ("should I be loaded?", computed from inject)
  - state:  where we are (the FiberState enum)
and one driver (_drive) that moves state toward target:

  refresh() -> _drive() -> _load()/_unload() -> _settle() -> _drive() again

inertia is the running load/unload task, or None when idle. While it is not
None, _drive refuses to start a second transition -- that guard is what stops
a plugin that provides a service (ctx.set -> notify -> refresh) from
re-entering itself forever.
"""

from __future__ import annotations

import asyncio
import inspect
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Plugin
    from .harness import Harness


class FiberState(Enum):
    PENDING = auto()
    LOADING = auto()
    ACTIVE = auto()
    FAILED = auto()
    DISPOSED = auto()
    UNLOADING = auto()


class Fiber:
    def __init__(
        self, harness: Harness, plugin: Plugin, inject: list[str] | None
    ) -> None:
        self.harness = harness
        # `plugin` is the function passed to ctx.use(); we store it, we don't
        # call it yet.
        self.plugin = plugin
        # inject = names this plugin needs before it may activate.
        self.inject = inject or []
        # this fiber's own context; it holds the plugin's effects.
        self.ctx: Context = harness.create_context()
        # where we are now.
        self.state = FiberState.PENDING
        # where we want to be: "should I be loaded?" recomputed from inject.
        self.target = False
        # the running load/unload task, or None when idle. This is the guard.
        self.inertia: asyncio.Task[None] | None = None
        # once we start leaving, refresh must stop changing target.
        self._disposing = False

    # Deps changed. If we're leaving or already gone, do nothing.
    # Otherwise recompute "should I be loaded?" (target) and hand off to _drive.
    def refresh(self) -> None:
        if self._disposing or self.state is FiberState.DISPOSED:
            return
        self.target = all(key in self.harness.reflect.values for key in self.inject)
        self._drive()

    # The only place that starts a transition, and it never waits.
    # If something is already running (inertia is not None), do nothing --
    # otherwise a load triggered by ctx.set -> notify -> refresh would
    # re-enter itself.
    # target true + not ACTIVE -> start loading.
    # target false + ACTIVE    -> start unloading.
    def _drive(self) -> None:
        if self.inertia is not None:
            return
        if self.target and self.state is not FiberState.ACTIVE:
            self.inertia = asyncio.create_task(self._load())
        elif not self.target and self.state is FiberState.ACTIVE:
            self.inertia = asyncio.create_task(self._unload())

    # Wait until nothing is running. A transition can chain another one
    # (_settle -> _drive), so loop until inertia becomes None.
    async def await_(self) -> None:
        while self.inertia is not None:
            task = self.inertia
            await asyncio.shield(task)

    # We're leaving for good:
    # - _disposing: refresh must not resurrect target while we tear down.
    # - kill target: we don't want to load anything anymore.
    # - _drive: unloads if we were active.
    # - await_: wait for the unloading to finish.
    # only then DISPOSED -- this state can never reload.
    async def dispose(self) -> None:
        if self._disposing or self.state is FiberState.DISPOSED:
            return
        self._disposing = True
        self.target = False
        self._drive()
        await self.await_()
        self.state = FiberState.DISPOSED

    # Run the plugin with this fiber's own context.
    # A sync plugin returns None; an async plugin returns a coroutine we await.
    async def _load(self) -> None:
        self.state = FiberState.LOADING
        try:
            # self.plugin is the function passed to ctx.use() -- e.g. llm_plugin.
            # self.ctx is this fiber's context, so this call is
            # llm_plugin(fiber_ctx). NOTE: no `self` is passed: plugin is a
            # stored function, not a method of Fiber.
            result = self.plugin(self.ctx)
            if inspect.isawaitable(result):
                await result
        except Exception:
            # The plugin raised: mark FAILED, clear inertia so we're idle,
            # and re-raise so whoever waits (ctx.use / settle) sees the error.
            self.state = FiberState.FAILED
            self.inertia = None
            raise
        # Loaded. Now re-check: target may have changed while we were loading.
        self.state = FiberState.ACTIVE
        self._settle()

    # Run the plugin's teardowns (undo this fiber's ctx).
    # Ends PENDING, not DISPOSED: deps may come back and reload us.
    async def _unload(self) -> None:
        self.state = FiberState.UNLOADING
        await self.ctx.undo()
        self.state = FiberState.PENDING
        self._settle()

    # A transition just finished: clear inertia, then _drive again.
    # Why again: target may have changed while we ran (e.g. a dep vanished
    # mid-load), so we chain the opposite transition if needed.
    def _settle(self) -> None:
        self.inertia = None
        self._drive()
