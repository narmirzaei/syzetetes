import io
import logging

from syzetetes import ui


def test_progress_is_inert_without_a_tty(monkeypatch, capsys):
    p = ui.Progress()
    assert p.enabled is False          # pytest's stderr is not a tty
    p.start(); p.set_phase("Round 1/2"); p.task_start("Claude (opus, high)", "round 1")
    p.ledger(1, {"agreed": 1, "disputed": 1}); p.task_end("Claude (opus, high)"); p.stop()
    assert capsys.readouterr().err == ""   # nothing drawn, no bar


def test_status_line_contents(monkeypatch):
    p = ui.Progress(); p.enabled = True
    p.set_phase("Round 2/4"); p.task_start("Claude (opus, high)", "round 2"); p.task_start("Codex (gpt-6.1-sol, high)", "round 2")
    line = p._line()
    assert "Round 2/4" in line and "Claude (opus, high)" in line and "Codex" in line and "round 2" in line
    p.task_end("Claude (opus, high)")
    assert "Claude" not in p._line()


def test_log_handler_writes_lines(monkeypatch):
    buf = io.StringIO()
    monkeypatch.setattr(ui.sys, "stderr", buf)
    h = ui.StatusLineHandler(buf); h.setFormatter(logging.Formatter("%(message)s"))
    lg = logging.getLogger("ui-test"); lg.handlers[:] = [h]; lg.propagate = False
    lg.info("hello"); lg.warning("careful")
    assert "hello\n" in buf.getvalue() and "careful" in buf.getvalue()


def test_clean_strips_terminal_control_sequences():
    from syzetetes.ui import clean
    s = "a\x1b[2Jb\x1b]0;evil\x07c\x1b]52;c;aGVsbG8=\x1b\\d\x00e\n\tf"
    assert clean(s) == "abcde\n\tf"
