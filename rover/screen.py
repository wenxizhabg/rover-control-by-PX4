"""US-04/T2, US-02/T3 & US-03a/T3: dựng các dòng nội dung của khung màn hình từ ViewModel."""

from dataclasses import dataclass, field

from rover.types import LinkState


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
