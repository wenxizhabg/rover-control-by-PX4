"""Kiểm tra tầng 2 – giao diện: đổi phím thành hành động, bảng hướng dẫn (US-04/T1, US-03a/T3, US-03b/T3), nội dung khung màn hình (US-04/T2, US-02/T3, US-03a/T3, US-03b/T3) và bảng thông báo giữ thời gian (US-03b/T5)."""

from rover .core import view
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


def test_10_message_board_is_empty_initially ():
    # Đầu vào: tạo mới MessageBoard (), gọi current (0.0).
    board = view .MessageBoard ()

    # Mong đợi: trả về chuỗi rỗng "" lúc mới mở app.
    assert board .current (0.0) == ""


def test_11_first_message_displays_immediately ():
    # Đầu vào: post ("A", 1.0) rồi gọi ngay current (1.0).
    board = view .MessageBoard ()
    board .post ("A", 1.0)

    # Mong đợi: thông báo đầu hiện ngay lập tức (phục vụ US-03b AC5 (a): bấm R thấy ngay "Đã gửi lệnh mở khóa").
    assert board .current (1.0) == "A"


def test_12_next_message_waits_minimum_hold_time ():
    # Đầu vào: post ("A", 0.0) -> current (0.0) -> post ("B", 0.01) -> kiểm tra tại 0.3 và 0.5.
    assert view .MESSAGE_HOLD_S == 0.5
    board = view .MessageBoard ()
    board .post ("A", 0.0)
    assert board .current (0.0) == "A"

    board .post ("B", 0.01)

    # Mong đợi: chưa đủ 0.5 s vẫn giữ "A"; đủ 0.5 s mới chuyển sang "B" (phục vụ US-03b AC5 (a)).
    assert board .current (0.3) == "A"
    assert board .current (0.5) == "B"


def test_13_multiple_messages_display_in_fifo_order_without_dropping ():
    # Đầu vào: post A, B, C cùng lúc tại 0.0 (C sau B sau A); gọi current tại 0.0, 0.49, 0.5, 0.99, 1.0.
    board = view .MessageBoard ()
    board .post ("A", 0.0)
    board .post ("B", 0.0)
    board .post ("C", 0.0)

    # Mong đợi: mỗi thông báo giữ tối thiểu 0.5 s, hiện lần lượt đúng thứ tự FIFO và không mất thông báo nào (phục vụ US-03b AC5 (b)).
    assert board .current (0.0) == "A"
    assert board .current (0.49) == "A"
    assert board .current (0.5) == "B"
    assert board .current (0.99) == "B"
    assert board .current (1.0) == "C"


def test_14_last_message_stays_when_queue_is_empty ():
    # Đầu vào: post ("A", 0.0) rồi kiểm tra sau rất lâu tại current (100.0).
    board = view .MessageBoard ()
    board .post ("A", 0.0)

    # Mong đợi: không có thông báo mới thì giữ nguyên thông báo cuối trên màn hình (phục vụ US-03b AC5 (c)).
    assert board .current (100.0) == "A"


def test_15_new_message_displays_immediately_after_old_held_long_enough ():
    # Đầu vào: post ("A", 0.0) -> current (0.0) -> sau 2.0 s post ("B", 2.0) -> current (2.0).
    board = view .MessageBoard ()
    board .post ("A", 0.0)
    assert board .current (0.0) == "A"

    board .post ("B", 2.0)

    # Mong đợi: thông báo cũ đã giữ đủ lâu thì thông báo mới hiện ngay không bị làm chậm (phục vụ US-03b AC5 (a)).
    assert board .current (2.0) == "B"


def test_16_drive_keys_and_help_lines ():
    # Đầu vào: action_for với các phím "w", "S", "a", "D", " " và danh sách hướng dẫn help_lines ().
    lines = help_lines ()

    # Mong đợi: ánh xạ đủ 5 hành động lái và bảng hướng dẫn hiện đủ các phím mới (phục vụ US-03b AC1–AC3).
    assert action_for ("w") == Action .FORWARD
    assert action_for ("S") == Action .BACKWARD
    assert action_for ("a") == Action .TURN_LEFT
    assert action_for ("D") == Action .TURN_RIGHT
    assert action_for (" ") == Action .STOP
    assert "W  tiến" in lines
    assert "S  lùi" in lines
    assert "A  quay trái" in lines
    assert "D  quay phải" in lines
    assert "Space  dừng ngay" in lines


def test_17_drive_status_formats_idle_and_all_directions ():
    # Đầu vào: gọi format_drive_status với None và 4 hướng lái kèm thời gian còn lại.
    idle = view .format_drive_status (None, 0.0)
    forward = view .format_drive_status (Action .FORWARD, 0.63)
    backward = view .format_drive_status (Action .BACKWARD, 0.2)
    turn_left = view .format_drive_status (Action .TURN_LEFT, 0.5)
    turn_right = view .format_drive_status (Action .TURN_RIGHT, 1.0)

    # Mong đợi: đúng chuỗi tiếng Việt và số giây 1 chữ số thập phân (phục vụ US-03b AC1, AC2).
    assert idle == "Lái xe   : ĐỨNG YÊN"
    assert forward == "Lái xe   : TIẾN (còn 0.6 s)"
    assert backward == "Lái xe   : LÙI (còn 0.2 s)"
    assert turn_left == "Lái xe   : QUAY TRÁI (còn 0.5 s)"
    assert turn_right == "Lái xe   : QUAY PHẢI (còn 1.0 s)"
