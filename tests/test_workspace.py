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


async def test_list_dir_lists_one_level_dirs_first(ctx, tmp_path):
    (tmp_path / "zeta").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "nested.txt").write_text("nested\n")
    (tmp_path / "b.txt").write_text("b\n")
    (tmp_path / "a.txt").write_text("a\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool("read_file", path=".")

    assert result == "alpha/\nzeta/\na.txt\nb.txt"


async def test_list_dir_shows_dotfiles(ctx, tmp_path):
    (tmp_path / ".env").write_text("secret\n")
    (tmp_path / "main.py").write_text("x\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool("read_file", path=".")

    assert result == ".env\nmain.py"


async def test_list_dir_pages_entries(ctx, tmp_path):
    for number in range(5):
        (tmp_path / f"f{number}.txt").write_text("x\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool("read_file", path=".", start_line=2, end_line=3)

    assert result == "f1.txt\nf2.txt\n[next: start_line=4]"


async def test_list_dir_empty_directory(ctx, tmp_path):
    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool("read_file", path=".")

    assert result == "(no entries; directory has 0 entries)"


async def test_list_dir_denies_outside_path(ctx, tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-dir"
    outside.mkdir()

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    with pytest.raises(PermissionError):
        await ctx.call_tool("read_file", path=str(outside))


async def test_list_dir_allows_approved_outside_path(ctx, tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-approved-dir"
    outside.mkdir()
    (outside / "x.txt").write_text("x\n")

    calls = []

    def approve(path, action):
        calls.append((path, action))
        return True

    await ctx.mount(workspace_plugin(tmp_path, approve))

    result = await ctx.call_tool("read_file", path=str(outside))

    assert result == "x.txt"
    assert calls == [(outside.resolve(), "read")]


async def test_missing_path_suggests_close_names(ctx, tmp_path):
    (tmp_path / "workspace.py").write_text("x\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    with pytest.raises(FileNotFoundError) as error:
        await ctx.call_tool("read_file", path="WorkSpace")

    message = str(error.value)
    assert "File not found: WorkSpace" in message
    assert "Did you mean one of these?" in message
    assert "workspace.py" in message


async def test_missing_folder_names_nearest_parent(ctx, tmp_path):
    (tmp_path / "plugins").mkdir()

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    with pytest.raises(FileNotFoundError) as error:
        await ctx.call_tool("read_file", path="plugin/x.py")

    message = str(error.value)
    assert f"The folder {tmp_path / 'plugin'} does not exist" in message
    assert f"The nearest folder that does is {tmp_path}" in message
    assert str(tmp_path / "plugins") in message


async def test_missing_path_uses_unique_alternate_name(ctx, tmp_path):
    (tmp_path / "a\u00a0b.txt").write_text("hi\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    result = await ctx.call_tool("read_file", path="a b.txt")

    assert result == "1\thi"


async def test_case_mismatch_is_not_corrected_silently(ctx, tmp_path):
    (tmp_path / "workspace.py").write_text("x\n")

    await ctx.mount(workspace_plugin(tmp_path, lambda path, action: False))

    with pytest.raises(FileNotFoundError):
        await ctx.call_tool("read_file", path="Workspace.py")
