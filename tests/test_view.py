"""Kiểm tra tầng 2 – giao diện: đổi phím thành hành động, bảng hướng dẫn (US-04/T1, US-03a/T3) và nội dung khung màn hình (US-04/T2, US-02/T3, US-03a/T3)."""

from rover .core .model import Action, LinkState
from rover .core .view import ViewModel, action_for, format_arm_status, format_link_status, help_lines, render


def test_1_h_key_toggles_help_case_insensitively ():
    """AC2: phím H hoặc h đều bật / tắt hướng dẫn."""
    assert action_for ("h") == Action .TOGGLE_HELP
    assert action_for ("H") == Action .TOGGLE_HELP


def test_2_q_key_quits_case_insensitively ():
    """AC3: phím Q hoặc q yêu cầu thoát app."""
    assert action_for ("q") == Action .QUIT
    assert action_for ("Q") == Action .QUIT


def test_3_unknown_key_is_ignored_and_help_lines_are_listed ():
    """AC2, AC3: phím lạ được bỏ qua; bảng hướng dẫn liệt kê H và Q."""
    assert action_for ("x") is None
    assert action_for (None) is None
    assert help_lines () [:2] == [
        "H  ẩn / hiện hướng dẫn",
        "Q  thoát app",
    ]


def test_4_r_and_f_keys_arm_and_disarm ():
    # Đầu vào: action_for ("r"), action_for ("F") và bảng hướng dẫn help_lines ().
    lines = help_lines ()

    # Mong đợi: R ứng với Action .ARM, F ứng với Action .DISARM; bảng phím có đủ "R  mở khóa xe" và "F  khóa xe" (phục vụ US-03a AC1, AC2).
    assert action_for ("r") == Action .ARM
    assert action_for ("F") == Action .DISARM
    assert "R  mở khóa xe" in lines
    assert "F  khóa xe" in lines


def test_5_default_view_renders_basic_frame_without_help ():
    """AC1: khung mặc định có tiêu đề, thông báo, gợi ý phím và trạng thái chờ dữ liệu."""
    lines = render (ViewModel ())

    assert "ROVER – điều khiển xe PX4 qua MAVLink" in lines
    assert "Trạng thái: (chưa có dữ liệu)" in lines
    assert "Thông báo: " in lines
    assert "H: hướng dẫn   Q: thoát" in lines
    assert "H  ẩn / hiện hướng dẫn" not in lines
    assert "Q  thoát app" not in lines


def test_6_view_with_help_renders_help_lines ():
    """AC2: khi bật hướng dẫn, khung hiển thị các dòng hướng dẫn được truyền vào."""
    view = ViewModel (
        show_help = True,
        help_lines = ["H  ẩn / hiện hướng dẫn", "Q  thoát app"],
    )

    lines = render (view)

    assert "H  ẩn / hiện hướng dẫn" in lines
    assert "Q  thoát app" in lines
    assert lines.index ("H  ẩn / hiện hướng dẫn") < lines.index ("Q  thoát app")


def test_7_status_lines_precede_message_in_rendered_frame ():
    """AC1: các dòng trạng thái giữ thứ tự và xuất hiện trước vùng thông báo."""
    view = ViewModel (
        status_lines = ["dòng A", "dòng B"],
        message = "xin chào",
    )

    lines = render (view)

    assert lines.index ("dòng A") < lines.index ("dòng B")
    assert lines.index ("dòng B") < lines.index ("Thông báo: xin chào")


def test_8_link_status_formats_waiting_connected_and_lost ():
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


def test_9_arm_status_formats_unknown_armed_and_disarmed ():
    # Đầu vào: gọi format_arm_status với None, True và False.
    unknown = format_arm_status (None)
    armed = format_arm_status (True)
    disarmed = format_arm_status (False)

    # Mong đợi: đúng 3 chuỗi tiếng Việt người dùng thấy (phục vụ US-03a AC1, AC2).
    assert unknown == "Khóa xe  : chưa rõ"
    assert armed == "Khóa xe  : ĐÃ MỞ KHÓA"
    assert disarmed == "Khóa xe  : ĐÃ KHÓA"
