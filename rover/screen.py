"""US-04/T2: dựng các dòng nội dung của khung màn hình từ ViewModel."""

from dataclasses import dataclass, field


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
