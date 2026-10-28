from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context, Disposer
    from .harness import Harness


class Reflect:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness
        # Name -> stack of (ticket, value) entries; newest provider is last.
        # A ticket is a fresh object minted per provide() call. It identifies
        # the entry, not the value, so equal values still have different
        # tickets.
        self.provider_stacks: dict[str, list[tuple[object, object]]] = {}

    def value(self, name: str) -> object | None:
        return self.values.get(name)

    # The provider that is current right now: the newest entry for `name`,
    # or None if nobody provides it. Consumers compare its ticket with the
    # ticket they loaded against.
    def current_entry(self, name: str) -> tuple[object, object] | None:
        stack = self.provider_stacks.get(name)
        if not stack:
            return None
        return stack[-1]

    @property
    # names -> the winning value (the newest entry's value).
    # The ticket is dropped here on purpose; current_entry() is the read that
    # keeps it.
    def values(self) -> dict[str, object]:
        return {name: stack[-1][1] for name, stack in self.provider_stacks.items()}


    # Each provide() call mints a fresh ticket. The entry is
    # (ticket, value): the ticket separates providers even when the values
    # compare equal.
    def provide(self, ctx: Context, name: str, value: object) -> Disposer:
        entry = (object(), value)

        def setup() -> None:
            self.provider_stacks.setdefault(name, []).append(entry)
            self.provider_changed()

        def teardown() -> None:
            stack = self.provider_stacks.get(name)
            if stack and entry in stack:
                stack.remove(entry)
            if not stack:
                self.provider_stacks.pop(name, None)
            self.provider_changed()

        return ctx.effect(setup, teardown)

    # A provider appeared or disappeared: let every fiber recompute its
    # wanted_tickets. Fibers that inject nothing are cheap no-ops.
    def provider_changed(self) -> None:
        for fiber in self.harness.registry.fibers:
            fiber.refresh()
