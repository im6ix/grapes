import pytest

from grapes.plugins.workspace import workspace_plugin


async def test_read_file_numbers_and_limits_lines(ctx, tmp_path):
    (tmp_path / "hello.txt").write_text("one\ntwo\nthree\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool(
        "read_file",
        path="hello.txt",
        start_line=2,
        end_line=3,
    )

    assert result == "2\ttwo\n3\tthree"


async def test_read_file_denies_outside_path(ctx, tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    with pytest.raises(PermissionError):
        await ctx.call_tool("read_file", path=str(outside))


async def test_read_file_defaults_to_500_lines(ctx, tmp_path):
    lines = [f"line {i}" for i in range(1, 502)]
    (tmp_path / "big.txt").write_text("\n".join(lines))

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool("read_file", path="big.txt")

    assert "1\tline 1" in result
    assert "500\tline 500" in result
    assert "501\tline 501" not in result
    assert result.endswith("[next: start_line=501]")


async def test_read_file_allows_approved_outside_path(ctx, tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-approved.txt"
    outside.write_text("yes\n")

    calls = []

    def approve(path, action):
        calls.append((path, action))
        return True

    await ctx.mount(workspace_plugin(tmp_path, approve))

    result = await ctx.call_tool("read_file", path=str(outside))

    assert result == "1\tyes"
    assert calls == [(outside.resolve(), "read")]


async def test_read_file_rejects_start_line_zero(ctx, tmp_path):
    (tmp_path / "hello.txt").write_text("one\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    with pytest.raises(ValueError):
        await ctx.call_tool("read_file", path="hello.txt", start_line=0)
