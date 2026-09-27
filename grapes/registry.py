from __future__ import annotations

from typing import TYPE_CHECKING

from .fiber import Fiber

if TYPE_CHECKING:
    from .context import Context, Disposer, Plugin
    from .harness import Harness


class Registry:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        self.fibers: list[Fiber] = []

    # Mount one plugin into its own fiber.
    #
    # It does four things:
    #   1. create a Fiber for the plugin (its own context)
    #   2. remember it in self.fibers so reflect.notify() can reach it
    #   3. register setup/teardown on the MOUNTING ctx:
    #        setup    (sync)  -> just start the fiber (refresh -> _drive)
    #        teardown (async) -> wait for a full unload, then forget the fiber
    #      so undo of the mounting ctx unmounts the plugin
    #   4. wait for the fiber to settle, so `await ctx.use(...)` means
    #      "loaded now" -- or PENDING if the inject deps are missing
    #
    # Returns a disposer that unmounts only this plugin.
    async def use(
        self, ctx: Context, plugin: Plugin, inject: list[str] | None = None
    ) -> Disposer:
        # step 1 + 2
        fiber = Fiber(self.harness, plugin, inject)
        self.fibers.append(fiber)

        # step 3: setup stays sync (it only starts work); teardown is async
        # (it waits for the fiber's own ctx.undo to finish, then forgets it).
        def setup() -> None:
            fiber.refresh()

        async def teardown() -> None:
            await fiber.dispose()
            self.fibers.remove(fiber)

        disposer = ctx.effect(setup, teardown)

        # step 4: don't return until the fiber settled.
        await fiber.await_()
        return disposer
