from grapes.plugins.shell import shell_plugin


async def test_run_shell_reports_the_exit_code(ctx, tmp_path):
    await ctx.mount(shell_plugin(tmp_path))

    result = await ctx.call_tool("run_shell", command="exit 7")

    assert result.endswith("[exit code 7]")


async def test_run_shell_timeout_kills_the_command(ctx, tmp_path):
    await ctx.mount(shell_plugin(tmp_path))

    result = await ctx.call_tool("run_shell", command="sleep 5", timeout=0.5)

    assert "Command timed out after 0.5 seconds" in result
    assert result.endswith("[exit code 137]")


async def test_run_shell_truncates_long_output(ctx, tmp_path):
    await ctx.mount(shell_plugin(tmp_path))

    result = await ctx.call_tool("run_shell", command="seq 1 3000")

    assert result.startswith("1001\n")
    assert result.endswith(
        "[truncated: showing the last 2000 of 3000 lines]\n\n[exit code 0]"
    )
