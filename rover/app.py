"""Tầng 1 – ứng dụng: vòng lặp chính RoverApp nối các tầng lại với nhau, và run_app là nơi duy nhất tạo driver thật."""

from rover .core .model import Action, ArmAck, Heartbeat, LinkState
from rover .core .vehicle import ArmControl, DriveController, LinkMonitor
from rover .core .view import (
    MessageBoard,
    ViewModel,
    action_for,
    format_arm_status,
    format_drive_status,
    format_link_status,
    help_lines,
    render,
)
from rover .drivers .mavlink import MavlinkVehicleLink
from rover .drivers .terminal import CursesTerminal, SystemClock
from rover .hal import Clock, Terminal, VehicleLink

# Tập 4 hành động lái xe theo hướng; Action .STOP dừng ngay thay vì bắt đầu hẹn giờ mới.
_DRIVE_ACTIONS = (
    Action .FORWARD,
    Action .BACKWARD,
    Action .TURN_LEFT,
    Action .TURN_RIGHT,
)


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
        self ._drive = DriveController ()
        # Giữ mỗi thông báo tối thiểu 0.5 s qua các vòng lặp để người vận hành đọc kịp khi có phản hồi liên tiếp.
        self ._messages = MessageBoard ()

    def step (self) -> bool:
        """Xử lý một phím và vẽ khung; trả False khi người dùng yêu cầu thoát."""
        now = self ._clock .now ()
        if self ._link is not None:
            for event in self ._link .poll ():
                if isinstance (event, Heartbeat):
                    self ._link_monitor .on_heartbeat (now)
                    self ._arm_control .on_heartbeat (event .armed)
                elif isinstance (event, ArmAck):
                    self ._messages .post (self ._arm_control .on_ack (event), now)

        link_state = self ._link_monitor .state (now)
        action = action_for (self ._terminal .read_key ())

        if action == Action .QUIT:
            return False
        if action == Action .TOGGLE_HELP:
            self ._show_help = not self ._show_help
        elif action in (Action .ARM, Action .DISARM):
            arm = action == Action .ARM
            should_send, message = self ._arm_control .request (arm, link_state)
            self ._messages .post (message, now)
            if should_send and self ._link is not None:
                self ._link .send_arm (arm)
        elif action in (*_DRIVE_ACTIONS, Action .STOP):
            if link_state != LinkState .CONNECTED:
                self ._messages .post ("Chưa kết nối xe", now)
            elif self ._arm_control .armed is not True:
                self ._messages .post ("Xe chưa mở khóa", now)
            elif action == Action .STOP:
                self ._drive .stop ()
            else:
                # Chuyển sang chế độ Manual trước khi chạy để xe thoát Hold (kết quả spike Q2).
                if self ._link is not None:
                    self ._link .send_manual_mode ()
                self ._drive .start (action, now)

        # Luôn gửi MANUAL_CONTROL (kể cả đứng yên) khi đã kết nối để PX4 không failsafe mất tay điều khiển và cho phép mở khóa ở Manual.
        if self ._link is not None and link_state == LinkState .CONNECTED:
            if self ._arm_control .armed is not True:
                self ._drive .stop ()
            self ._link .send_drive (*self ._drive .setpoint (now))
        else:
            self ._drive .stop ()

        status_lines = []
        if self ._link is not None:
            status_lines .append (
                format_link_status (
                    link_state,
                    self ._link_monitor .heartbeat_count,
                    self ._link_monitor .seconds_since_last (now),
                )
            )
            status_lines .append (format_arm_status (self ._arm_control .armed))
            status_lines .append (
                format_drive_status (
                    self ._drive .active_action (now),
                    self ._drive .remaining_s (now),
                )
            )

        view = ViewModel (
            status_lines = status_lines,
            message = self ._messages .current (now),
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