def test_logger_prints(capsys, ctx):
    ctx.logger.info("hello")
    out = capsys.readouterr().out
    assert "[info] hello" in out
