from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Approval:
    action: str
    target: str
    scope: str | None = None


Approver = Callable[[Approval], bool]


def make_approver() -> Approver:
    grants: list[str] = []

    def approve(request: Approval) -> bool:
        for grant in grants:
            if request.target == grant:
                return True
            if grant.endswith("/") and request.target.startswith(grant):
                return True

        if request.scope is None:
            answer = input(f"{request.action} {request.target}? [y/n]: ")

            return answer.strip().lower() == "y"

        answer = (
            input(
                f"{request.action} {request.target}? [y] once / [a] always / [n] no: "
            )
            .strip()
            .lower()
        )
        if answer == "y":
            return True
        if answer == "a":
            grants.append(request.scope)
            return True
        return False

    return approve
