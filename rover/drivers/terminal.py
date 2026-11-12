"""Tầng 4 – driver màn hình, bàn phím (hiện thực Terminal bằng curses) và đồng hồ hệ thống (hiện thực Clock)."""

import curses
import locale
import time


class CursesTerminal:
    """Màn hình toàn khung và bàn phím không cần Enter."""

    def __init__ (self):
        locale .setlocale (locale .LC_ALL, "")
        self ._stdscr = curses .initscr ()
        self ._closed = False

        try:
            curses .cbreak ()
            curses .noecho ()
            curses .curs_set (0)
            self ._stdscr .timeout (50)
        except BaseException:
            self .close ()
            raise

    def read_key (self) -> str | None:
        """Trả ký tự in được vừa bấm, hoặc None nếu không có phím phù hợp."""
        key = self ._stdscr .getch ()
        if key < 0 or key > 255:
            return None

        character = chr (key)
        return character if character .isprintable () else None

    def draw (self, lines: list[str]) -> None:
        """Xóa màn hình rồi vẽ phần vừa với kích thước terminal."""
        self ._stdscr .erase ()
        height, width = self ._stdscr .getmaxyx ()
        for row, line in enumerate (lines [:height]):
            self ._stdscr .addstr (row, 0, line [:max (width - 1, 0)])
        self ._stdscr .refresh ()

    def close (self) -> None:
        """Khôi phục terminal; gọi nhiều lần không gây tác dụng phụ."""
        if self ._closed:
            return

        self ._closed = True
        first_error = None
        for restore in (curses .nocbreak, curses .echo, lambda: curses .curs_set (1), curses .endwin):
            try:
                restore ()
            except BaseException as error:
                if first_error is None:
                    first_error = error

        if first_error is not None:
            raise first_error


class SystemClock:
    """Đồng hồ hệ thống chỉ tăng, không phụ thuộc giờ lịch."""

    def now (self) -> float:
        """Trả thời gian hiện tại theo giây từ time.monotonic ()."""
        return time .monotonic ()
