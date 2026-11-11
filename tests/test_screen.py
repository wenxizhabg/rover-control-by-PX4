"""US-04/T2, US-02/T3 & US-03a/T3: kiểm tra nội dung khung màn hình được dựng từ ViewModel."""

from rover import screen
from rover .screen import ViewModel, format_link_status, render
from rover .types import LinkState


def test_1_default_view_renders_basic_frame_without_help ():
    """AC1: khung mặc định có tiêu đề, thông báo, gợi ý phím và trạng thái chờ dữ liệu."""
    lines = render (ViewModel ())

    assert "ROVER – điều khiển xe PX4 qua MAVLink" in lines
    assert "Trạng thái: (chưa có dữ liệu)" in lines
    assert "Thông báo: " in lines
    assert "H: hướng dẫn   Q: thoát" in lines
    assert "H  ẩn / hiện hướng dẫn" not in lines
    assert "Q  thoát app" not in lines


def test_2_view_with_help_renders_help_lines ():
    """AC2: khi bật hướng dẫn, khung hiển thị các dòng hướng dẫn được truyền vào."""
    view = ViewModel (
        show_help = True,
        help_lines = ["H  ẩn / hiện hướng dẫn", "Q  thoát app"],
    )

    lines = render (view)

    assert "H  ẩn / hiện hướng dẫn" in lines
    assert "Q  thoát app" in lines
    assert lines.index ("H  ẩn / hiện hướng dẫn") < lines.index ("Q  thoát app")


def test_3_status_lines_precede_message_in_rendered_frame ():
    """AC1: các dòng trạng thái giữ thứ tự và xuất hiện trước vùng thông báo."""
    view = ViewModel (
        status_lines = ["dòng A", "dòng B"],
        message = "xin chào",
    )

    lines = render (view)

    assert lines.index ("dòng A") < lines.index ("dòng B")
    assert lines.index ("dòng B") < lines.index ("Thông báo: xin chào")


def test_4_link_status_formats_waiting_connected_and_lost ():
    """US-02 AC1, AC2, AC4: dòng kết nối có trạng thái và thời gian đúng định dạng."""
    assert format_link_status (LinkState .WAITING, 0, None) == "Kết nối  : ĐANG CHỜ XE"
    assert format_link_status (
        LinkState .CONNECTED,
        42,
        0.43,
    ) == "Kết nối  : ĐÃ KẾT NỐI   (HEARTBEAT: 42, lần cuối 0.4 s trước)"
    assert format_link_status (
        LinkState .LOST,
        42,
        5.21,
    ) == "Kết nối  : MẤT KẾT NỐI  (HEARTBEAT: 42, lần cuối 5.2 s trước)"


def test_5_arm_status_formats_unknown_armed_and_disarmed ():
    # Đầu vào: gọi format_arm_status với None, True và False.
    unknown = screen .format_arm_status (None)
    armed = screen .format_arm_status (True)
    disarmed = screen .format_arm_status (False)

    # Mong đợi: đúng 3 chuỗi tiếng Việt người dùng thấy (phục vụ US-03a AC1, AC2).
    assert unknown == "Khóa xe  : chưa rõ"
    assert armed == "Khóa xe  : ĐÃ MỞ KHÓA"
    assert disarmed == "Khóa xe  : ĐÃ KHÓA"
