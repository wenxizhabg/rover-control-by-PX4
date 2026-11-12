"""Tầng 1 – ứng dụng: vòng lặp chính RoverApp nối các tầng lại với nhau, và run_app là nơi duy nhất tạo driver thật."""

from rover .core .model import Action, ArmAck, Heartbeat
from rover .core .vehicle import ArmControl, LinkMonitor
from rover .core .view import ViewModel, action_for, format_arm_status, format_link_status, help_lines, render
from rover .drivers .mavlink import MavlinkVehicleLink
from rover .drivers .terminal import CursesTerminal, SystemClock
from rover .hal import Clock, Terminal, VehicleLink


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
        self ._link_monitor = LinkMonitor ()
        self ._arm_control = ArmControl ()
        # Giữ thông báo gần nhất qua các vòng lặp để không bị xóa sau chu kỳ chờ phím 50 ms.
        self ._message = ""

    def step (self) -> bool:
        """Xử lý một phím và vẽ khung; trả False khi người dùng yêu cầu thoát."""
        now = self ._clock .now ()
        if self ._link is not None:
            for event in self ._link .poll ():
                if isinstance (event, Heartbeat):
                    self ._link_monitor .on_heartbeat (now)
                    self ._arm_control .on_heartbeat (event .armed)
                elif isinstance (event, ArmAck):
                    self ._message = self ._arm_control .on_ack (event)

        action = action_for (self ._terminal .read_key ())

        if action == Action .QUIT:
            return False
        if action == Action .TOGGLE_HELP:
            self ._show_help = not self ._show_help
        elif action in (Action .ARM, Action .DISARM):
            arm = action == Action .ARM
            should_send, self ._message = self ._arm_control .request (
                arm,
                self ._link_monitor .state (now),
            )
            if should_send and self ._link is not None:
                self ._link .send_arm (arm)

        status_lines = []
        if self ._link is not None:
            status_lines .append (
                format_link_status (
                    self ._link_monitor .state (now),
                    self ._link_monitor .heartbeat_count,
                    self ._link_monitor .seconds_since_last (now),
                )
            )
            status_lines .append (format_arm_status (self ._arm_control .armed))

        view = ViewModel (
            status_lines = status_lines,
            message = self ._message,
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
    link = MavlinkVehicleLink ()
    terminal = CursesTerminal ()
    return RoverApp (terminal, SystemClock (), link) .run ()