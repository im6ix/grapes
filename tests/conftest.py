"""Run `async def test_...` functions on an event loop.

Pytest calls this hook for every test function. If the test is a coroutine
function, we run it ourselves with asyncio.run and return True to tell pytest
"handled". Sync tests fall through (return None) and run normally.
"""
from typing import Any


def pytest_pyfunc_call(pyfuncitem: Any) -> bool | None:
    import asyncio
    import inspect

    test = pyfuncitem.obj
    if inspect.iscoroutinefunction(test):
        asyncio.run(test(**pyfuncitem.funcargs))
        return True
    return None
