"""US-01/T1: kiểm tra môi trường dự án đã sẵn sàng trước khi viết code. File này chỉ kiểm 2 điều: package rover của dự án nạp được, và thư viện pymavlink đã được cài vào venv. Nếu test ở đây fail thì các test khác cũng không chạy được, nên khi gặp lỗi hãy xem file này trước."""


def test_import_rover_package():
    """Kiểm tra package rover (thư mục rover/ có file __init__.py) nạp được và có đúng phiên bản."""
    # Nạp package của dự án; nếu thư mục rover/ hoặc file __init__.py chưa có thì Python báo ModuleNotFoundError và test fail ngay tại đây.
    import rover

    # __version__ được khai báo trong rover/__init__.py; kiểm tra giá trị để chắc chắn nạp đúng package của dự án chứ không phải một package trùng tên nào khác.
    assert rover.__version__ == "0.1.0"


def test_import_pymavlink():
    """Kiểm tra thư viện pymavlink đã được cài (pip install -r requirements.txt) và dùng được."""
    # mavutil là module của pymavlink chứa các hàm mở kết nối MAVLink; nếu chưa cài pymavlink thì dòng này báo ModuleNotFoundError.
    from pymavlink import mavutil

    # mavlink_connection là hàm mở cổng kết nối tới xe, sẽ dùng ở T4; kiểm tra hàm này có tồn tại để chắc thư viện cài đủ, không bị hỏng.
    assert hasattr(mavutil, "mavlink_connection")