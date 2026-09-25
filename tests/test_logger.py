from grapes import Harness


def test_logger_prints(capsys):
    h = Harness()
    ctx = h.create_context()
    ctx.logger.info("hello")
    out = capsys.readouterr().out
    assert "[info] hello" in out
