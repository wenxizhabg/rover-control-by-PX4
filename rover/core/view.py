"""Tầng 2 – giao diện người dùng: đổi phím bấm thành hành động, tạo bảng hướng dẫn, dựng khung màn hình và giữ thời gian hiển thị thông báo."""

from collections import deque
from dataclasses import dataclass, field

from rover .core .model import Action, LinkState

# Thời gian tối thiểu (giây) giữ mỗi thông báo trên màn hình để người vận hành đọc kịp.
MESSAGE_HOLD_S: float = 0.5


KEY_BINDINGS: list[tuple[str, Action, str]] = [
    ("h", Action .TOGGLE_HELP, "ẩn / hiện hướng dẫn"),
    ("q", Action .QUIT, "thoát app"),
    ("r", Action .ARM, "mở khóa xe"),
    ("f", Action .DISARM, "khóa xe"),
]


def action_for (key: str | None) -> Action | None:
    """Trả hành động tương ứng với phím, không phân biệt chữ hoa hay chữ thường."""
    if key is None:
        return None

    normalized_key = key .lower ()
    for bound_key, action, _description in KEY_BINDINGS:
        if normalized_key == bound_key:
            return action
    return None


def help_lines () -> list[str]:
    """Trả các dòng hướng dẫn theo thứ tự phím được khai báo trong KEY_BINDINGS."""
    return [
        f"{key .upper ()}  {description}"
        for key, _action, description in KEY_BINDINGS
    ]


@dataclass
class ViewModel:
    """Dữ liệu trạng thái, thông báo và hướng dẫn cần hiển thị trong một khung."""

    status_lines: list[str] = field (default_factory = list)
    message: str = ""
    show_help: bool = False
    help_lines: list[str] = field (default_factory = list)


def render (view: ViewModel) -> list[str]:
    """Dựng khung màn hình theo thứ tự tiêu đề, trạng thái, thông báo và hướng dẫn."""
    separator = "-" * 40
    lines = [
        "ROVER – điều khiển xe PX4 qua MAVLink",
        separator,
        *(view .status_lines or ["Trạng thái: (chưa có dữ liệu)"]),
        f"Thông báo: {view .message}",
        separator,
    ]

    if view .show_help:
        lines .extend (view .help_lines)

    lines .append ("H: hướng dẫn   Q: thoát")
    return lines


def format_link_status (
    state: LinkState,
    count: int,
    seconds: float | None,
) -> str:
    """Định dạng trạng thái kết nối và thời điểm nhận HEARTBEAT gần nhất."""
    if state == LinkState .WAITING:
        return "Kết nối  : ĐANG CHỜ XE"

    if seconds is None:
        raise ValueError ("Trạng thái đã nhận HEARTBEAT phải có thời gian lần cuối.")

    if state == LinkState .CONNECTED:
        return f"Kết nối  : ĐÃ KẾT NỐI   (HEARTBEAT: {count}, lần cuối {seconds:.1f} s trước)"
    if state == LinkState .LOST:
        return f"Kết nối  : MẤT KẾT NỐI  (HEARTBEAT: {count}, lần cuối {seconds:.1f} s trước)"

    raise ValueError (f"Trạng thái kết nối không hỗ trợ: {state}")


def format_arm_status (armed: bool | None) -> str:
    """Định dạng dòng hiển thị trạng thái mở / khóa xe theo cờ armed của HEARTBEAT."""
    # None nghĩa là chưa nhận được HEARTBEAT nào để biết xe đang khóa hay mở khóa.
    if armed is None:
        return "Khóa xe  : chưa rõ"
    if armed:
        return "Khóa xe  : ĐÃ MỞ KHÓA"
    return "Khóa xe  : ĐÃ KHÓA"


class MessageBoard:
    """Hàng đợi thông báo theo thứ tự FIFO, giữ mỗi thông báo ít nhất hold_s giây trước khi chuyển sang thông báo kế tiếp."""

    def __init__ (self, hold_s: float = MESSAGE_HOLD_S) -> None:
        self ._hold_s = hold_s
        # Thông báo đang hiển thị và thời điểm bắt đầu hiện; None khi bảng chưa có thông báo nào.
        self ._current: str = ""
        self ._shown_at: float | None = None
        self ._queue: deque[str] = deque ()

    def _advance (self, now: float) -> None:
        """Chuyển sang thông báo kế tiếp trong hàng đợi nếu thông báo hiện tại đã giữ đủ hold_s giây."""
        if self ._queue and self ._shown_at is not None and (now - self ._shown_at) >= self ._hold_s:
            self ._current = self ._queue .popleft ()
            self ._shown_at = now

    def post (self, text: str, now: float) -> None:
        """Thêm thông báo mới vào bảng; hiện ngay nếu bảng đang trống hoặc thông báo cũ đã giữ đủ thời gian."""
        if self ._shown_at is None:
            self ._current = text
            self ._shown_at = now
            return

        self ._queue .append (text)
        self ._advance (now)

    def current (self, now: float) -> str:
        """Trả thông báo cần hiển thị tại thời điểm now; chưa có thông báo nào thì trả chuỗi rỗng."""
        self ._advance (now)
        return self ._current
