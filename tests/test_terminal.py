"""US-04/T3: kiểm tra driver curses bằng terminal giả."""

import curses

import pytest

from rover import terminal
from rover.clock import SystemClock


class FakeWindow:
    def __init__ (self):
        self .calls = []

    def timeout (self, milliseconds):
        self .calls .append (("timeout", milliseconds))

    def getch (self):
        return self .key

    def erase (self):
        self .calls .append (("erase",))

    def getmaxyx (self):
        return self .size

    def addstr (self, row, column, text):
        self .calls .append (("addstr", row, column, text))

    def refresh (self):
        self .calls .append (("refresh",))


@pytest.fixture
def fake_curses (monkeypatch):
    window = FakeWindow ()
    window .size = (2, 5)
    window .key = ord ("q")
    calls = []

    monkeypatch .setattr (terminal .curses, "initscr", lambda: window)
    for name in ("cbreak", "noecho", "nocbreak", "echo", "endwin"):
        monkeypatch .setattr (terminal .curses, name, lambda name = name: calls .append (name))
    monkeypatch .setattr (terminal .curses, "curs_set", lambda value: calls .append (("curs_set", value)))
    monkeypatch .setattr (terminal .locale, "setlocale", lambda *args: calls .append (("setlocale", *args)))
    return window, calls


def test_terminal_initializes_curses_after_setting_utf8_locale (fake_curses):
    _window, calls = fake_curses

    terminal.CursesTerminal ()

    assert calls [:4] == [
        ("setlocale", terminal .locale .LC_ALL, ""),
        "cbreak",
        "noecho",
        ("curs_set", 0),
    ]
    assert _window .calls == [("timeout", 50)]


def test_read_key_returns_only_printable_characters (fake_curses):
    window, _calls = fake_curses
    driver = terminal.CursesTerminal ()

    assert driver .read_key () == "q"
    window .key = -1
    assert driver .read_key () is None
    window .key = 10
    assert driver .read_key () is None
    window .key = curses .KEY_UP
    assert driver .read_key () is None


def test_draw_crops_lines_to_fit_without_writing_last_column (fake_curses):
    window, _calls = fake_curses
    driver = terminal.CursesTerminal ()

    driver .draw (["abcdef", "xyz", "ignored"])

    assert window .calls[-4:] == [
        ("erase",),
        ("addstr", 0, 0, "abcd"),
        ("addstr", 1, 0, "xyz"),
        ("refresh",),
    ]


def test_close_restores_terminal_once (fake_curses):
    _window, calls = fake_curses
    driver = terminal.CursesTerminal ()

    driver .close ()
    driver .close ()

    assert calls[-4:] == ["nocbreak", "echo", ("curs_set", 1), "endwin"]


def test_close_attempts_all_restores_and_reports_first_error (fake_curses, monkeypatch):
    _window, calls = fake_curses
    driver = terminal.CursesTerminal ()
    failure = curses.error ("restore failed")

    def fail_nocbreak ():
        calls .append ("nocbreak")
        raise failure

    monkeypatch .setattr (terminal .curses, "nocbreak", fail_nocbreak)

    with pytest .raises (curses.error, match = "restore failed"):
        driver .close ()

    assert "echo" in calls
    assert ("curs_set", 1) in calls
    assert "endwin" in calls


def test_system_clock_uses_monotonic_time (monkeypatch):
    monkeypatch .setattr ("rover.clock.time.monotonic", lambda: 12.5)

    assert SystemClock () .now () == 12.5
