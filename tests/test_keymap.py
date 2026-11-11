"""US-04/T1: kiểm tra bảng đổi phím thành hành động và nội dung hướng dẫn."""

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
    assert help_lines () == [
        "H  ẩn / hiện hướng dẫn",
        "Q  thoát app",
    ]
