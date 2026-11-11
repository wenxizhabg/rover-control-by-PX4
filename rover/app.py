"""US-04/T4: vòng lặp ứng dụng rover, tách biệt driver thật để có thể kiểm thử."""

from rover import keymap, screen
from rover.clock import SystemClock
from rover.hal import Clock, Terminal, VehicleLink
from rover.keymap import help_lines
from rover.screen import ViewModel, render
from rover.terminal import CursesTerminal
from rover.types import Action


class RoverApp:
    """Điều phối phím bấm và khung hiển thị qua các interface được truyền vào."""

    def __init__ (
        self,
        terminal: Terminal,
        clock: Clock,
        link: VehicleLink | None = None,
    ) -> None:
        self ._terminal = terminal
        self ._clock = clock
        self ._link = link
        self ._show_help = False

    def step (self) -> bool:
        """Xử lý một phím và vẽ khung; trả False khi người dùng yêu cầu thoát."""
        action = keymap .action_for (self ._terminal .read_key ())

        if action == Action .QUIT:
            return False
        if action == Action .TOGGLE_HELP:
            self ._show_help = not self ._show_help

        view = ViewModel (
            show_help = self ._show_help,
            help_lines = help_lines (),
        )
        self ._terminal .draw (render (view))
        return True

    def run (self) -> int:
        """Chạy vòng lặp; luôn đóng terminal và link khi thoát hoặc nhấn Ctrl+C."""
        try:
            while self .step ():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            try:
                self ._terminal .close ()
            finally:
                if self ._link is not None:
                    self ._link .close ()

        return 0


def run_app () -> int:
    """Tạo driver thật rồi chạy app."""
    terminal = CursesTerminal ()
    return RoverApp (terminal, SystemClock ()) .run ()