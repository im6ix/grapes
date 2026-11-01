"""Run `async def test_...` functions on an event loop.

Pytest calls this hook for every test function. If the test is a coroutine
function, we run it ourselves with asyncio.run and return True to tell pytest
"handled". Sync tests fall through (return None) and run normally.
"""

from typing import Any

import pytest

from grapes import Harness
from grapes.agent.llm import Llm, llm_plugin


def pytest_pyfunc_call(pyfuncitem: Any) -> bool | None:
    import asyncio
    import inspect

    test = pyfuncitem.obj
    if inspect.iscoroutinefunction(test):
        params = inspect.signature(test).parameters
        kwargs = {
            name: value for name, value in pyfuncitem.funcargs.items() if name in params
        }
        asyncio.run(test(**kwargs))
        return True
    return None


@pytest.fixture
def h():
    return Harness()


@pytest.fixture
def ctx(h):
    return h.create_context()


@pytest.fixture
def mount_llm():
    async def mount(context, adapter):
        await context.mount(llm_plugin)
        llm = context.lookup("llm")
        assert isinstance(llm, Llm)
        llm.register_adapter(context, adapter)
        return llm

    return mount


@pytest.fixture
def two_ints():
    return {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    }
