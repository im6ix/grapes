from grapes import Harness
from grapes.agent.llm import Llm, llm_plugin


async def test_mounting_provides_the_service():
    h = Harness()
    ctx = h.create_context()

    await ctx.use(llm_plugin)

    assert isinstance(ctx.get("llm"), Llm)


async def test_unmounting_removes_the_service():
    h = Harness()
    ctx = h.create_context()

    dispose = await ctx.use(llm_plugin)
    await dispose()

    assert ctx.get("llm") is None


async def test_chat_delegates_to_the_registered_adapter():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(llm_plugin)
    llm = ctx.get("llm")
    assert isinstance(llm, Llm)

    async def fake_message(messages, tools):
        return {"type": "answer", "content": "hi"}

    llm.register(ctx, fake_message)

    assert await llm.chat([], []) == {"type": "answer", "content": "hi"}


async def test_unregistering_clears_the_adapter():
    h = Harness()
    ctx = h.create_context()
    await ctx.use(llm_plugin)
    llm = ctx.get("llm")
    assert isinstance(llm, Llm)

    async def fake_message(messages, tools):
        return {"type": "answer", "content": "hi"}

    remove = llm.register(ctx, fake_message)
    await remove()

    assert llm._adapter is None
