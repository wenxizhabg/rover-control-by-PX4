"""US-04/T1 & US-03a/T3: kiểm tra bảng đổi phím thành hành động và nội dung hướng dẫn."""

from rover .types import Action
from rover .keymap import action_for, help_lines


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
