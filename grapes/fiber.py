"""One mounted plugin and its lifecycle.

This is a controller, not an event handler. It does not say "on event X, go to
state Y". It keeps three answers:
  - wanted_tickets: which providers we want (their tickets, in inject order),
                    or None when at least one dependency is missing
  - loaded_tickets: which provider tickets the current load was run against
  - state:          where we are (the FiberState enum)
and one driver (_start_transition) that moves state toward wanted_tickets:

  refresh() -> _start_transition() -> _load()/_unload()
            -> _transition_done() -> _start_transition() again

transition_task is the running load/unload task, or None when idle. While it
is not None, _start_transition refuses to start a second transition -- that
guard is what stops a plugin that provides a service (ctx.provide ->
provider_changed -> refresh) from re-entering itself forever.

wanted_tickets and loaded_tickets are compared, never tested for truthiness.
That is how a provider replacement is noticed: same name, same value,
different ticket.
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
        # `plugin` is the function passed to ctx.mount(); we store it, we don't
        # call it yet.
        self.plugin = plugin
        # inject = names this plugin needs before it may activate.
        self.inject = inject or []
        # this fiber's own context; it holds the plugin's effects.
        self.ctx: Context = harness.create_context()
        # The context points back so lookup can find the committed view.
        self.ctx.fiber = self
        # where we are now.
        self.state = FiberState.PENDING
        # where we want to be: the ticket for each inject key, in order.
        # None means at least one dependency is missing.
        self.wanted_tickets: tuple[object, ...] | None = None
        # the tickets the current load was run against.
        # None means "not loaded".
        self.loaded_tickets: tuple[object, ...] | None = None
        # the inject values this load was run against, by name. Context.lookup
        # reads these until unload finishes, so teardown sees the world the
        # plugin was installed in.
        self.committed: dict[str, object] = {}
        # the running load/unload task, or None when idle. This is the guard.
        self.transition_task: asyncio.Task[None] | None = None
        # once we start leaving, refresh must stop changing wanted_tickets.
        self._disposing = False

    # What should we be loaded against? One ticket per inject key, in order.
    # None = a dependency is missing (do not load).
    # ()   = no inject keys (load anyway).
    def _wanted_tickets(self) -> tuple[object, ...] | None:
        tickets: list[object] = []
        for name in self.inject:
            entry = self.harness.reflect.current_entry(name)
            if entry is None:
                return None
            tickets.append(entry[0])
        return tuple(tickets)

    # Deps changed. If we're leaving or already gone, do nothing.
    # Otherwise recompute which provider tickets we want (wanted_tickets) and
    # hand off to _start_transition.
    def refresh(self) -> None:
        if self._disposing or self.state is FiberState.DISPOSED:
            return
        self.wanted_tickets = self._wanted_tickets()
        self._start_transition()

    # The only place that starts a transition, and it never waits.
    # If something is already running (transition_task is not None), do
    # nothing -- otherwise a load triggered by
    # ctx.provide -> provider_changed -> refresh would re-enter itself.
    # equal wanted_tickets/loaded_tickets -> already where we want to be.
    # different + ACTIVE   -> unload first; _transition_done then loads anew.
    # different + PENDING  -> load.
    # A FAILED fiber stays failed: it is not retried automatically.
    def _start_transition(self) -> None:
        if self.transition_task is not None or self.state is FiberState.FAILED:
            return
        if self.wanted_tickets == self.loaded_tickets:
            return
        if self.state is FiberState.ACTIVE:
            self.transition_task = asyncio.create_task(self._unload())
        else:
            self.transition_task = asyncio.create_task(self._load())

    # Wait until nothing is running. A transition can chain another one
    # (_transition_done -> _start_transition), so loop until transition_task
    # becomes None.
    async def wait_until_settled(self) -> None:
        while self.transition_task is not None:
            task = self.transition_task
            await asyncio.shield(task)

    # We're leaving for good:
    # - _disposing: refresh must not resurrect wanted_tickets while we tear down.
    # - clear wanted_tickets: we don't want to load anything anymore.
    # - _start_transition: unloads if we were active.
    # - wait_until_settled: wait for the unloading to finish.
    # only then DISPOSED -- this state can never reload.
    async def dispose(self) -> None:
        if self._disposing or self.state is FiberState.DISPOSED:
            return
        self._disposing = True
        self.wanted_tickets = None
        self._start_transition()
        await self.wait_until_settled()
        self.state = FiberState.DISPOSED

    # Run the plugin with this fiber's own context.
    # A sync plugin returns None; an async plugin returns a coroutine we await.
    async def _load(self) -> None:
        # Re-read before the first await: the task may start after the world
        # changed. If a dep is missing now, do not load.
        wanted_tickets = self._wanted_tickets()
        if wanted_tickets is None:
            self.wanted_tickets = None
            # Nothing was loaded, so there is nothing to remember.
            self.committed = {}
            self.state = FiberState.PENDING
            self._transition_done()
            return
        self.wanted_tickets = wanted_tickets
        # Snapshot the values that go with these tickets. No await has run
        # since _wanted_tickets(), so the entries are still current.
        self.committed = {}
        for name in self.inject:
            entry = self.harness.reflect.current_entry(name)
            if entry is not None:
                self.committed[name] = entry[1]
        self.state = FiberState.LOADING
        try:
            # self.plugin is the function passed to ctx.mount() -- e.g. llm_plugin.
            # self.ctx is this fiber's context, so this call is
            # llm_plugin(fiber_ctx). NOTE: no `self` is passed: plugin is a
            # stored function, not a method of Fiber.
            result = self.plugin(self.ctx)
            if inspect.isawaitable(result):
                await result
        except Exception:
            # The plugin raised: mark FAILED, clear the loaded tickets and our
            # effects, and clear transition_task so we're idle. Re-raise so
            # whoever waits (ctx.mount / wait_until_idle) sees the error.
            self.state = FiberState.FAILED
            self.loaded_tickets = None
            await self.ctx.revert_all()
            # The failure teardowns also saw the snapshot.
            self.committed = {}
            self.transition_task = None
            raise
        # Loaded. Record the tickets this load actually used: the local
        # wanted_tickets, not self.wanted_tickets, because wanted_tickets may
        # have moved on while an async plugin was running. _transition_done
        # re-checks the difference.
        self.loaded_tickets = wanted_tickets
        self.state = FiberState.ACTIVE
        self._transition_done()

    # Run the plugin's teardowns (revert this fiber's ctx).
    # Keep `loaded_tickets` set until every teardown has run, then clear it:
    # the fiber is no longer loaded. Ends PENDING, not DISPOSED: deps may come
    # back.
    async def _unload(self) -> None:
        self.state = FiberState.UNLOADING
        await self.ctx.revert_all()
        # Teardowns saw the snapshot; it is no longer the current load.
        self.committed = {}
        self.loaded_tickets = None
        self.state = FiberState.PENDING
        self._transition_done()

    # A transition just finished: clear transition_task, then start again.
    # Why again: wanted_tickets may have changed while we ran (e.g. a dep
    # vanished mid-load), so we chain the opposite transition if needed.
    def _transition_done(self) -> None:
        self.transition_task = None
        self._start_transition()
