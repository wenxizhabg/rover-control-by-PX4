"""US-04/T2: kiểm tra nội dung khung màn hình được dựng từ ViewModel."""

from rover .screen import ViewModel, render


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
