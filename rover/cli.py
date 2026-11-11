"""US-01/T5: lệnh CLI của app. Đọc lệnh người dùng gõ trong terminal (ví dụ "python -m rover connect --timeout 3"), gọi connect của T4, in kết quả ra màn hình và trả mã thoát cho hệ điều hành (0 = thành công, khác 0 = lỗi)."""

# argparse: thư viện có sẵn của Python để đọc lệnh và tùy chọn người dùng gõ, tự kiểm tra kiểu dữ liệu và tự sinh trang trợ giúp (--help).
import argparse
# sys: dùng sys .stderr để in thông báo lỗi ra luồng lỗi, tách khỏi kết quả bình thường.
import sys

from rover .connection import DEFAULT_TIMEOUT, DEFAULT_URL, ConnectionTimeout, connect
from rover.app import run_app
# Mã thoát: 0 = thành công; 1 = không kết nối được xe. (Mã 2 do argparse tự dùng khi người dùng gõ sai lệnh.)
EXIT_OK = 0
EXIT_NO_VEHICLE = 1


def build_parser ():
    """Tạo bộ đọc lệnh; không có lệnh con thì chạy app."""
    parser = argparse .ArgumentParser (prog = "python -m rover", description = "Điều khiển xe rover PX4 qua MAVLink.")
    commands = parser .add_subparsers (dest = "command", required = False)

    connect_cmd = commands .add_parser ("connect", help = "kết nối tới xe và hiển thị thông tin xe")
    connect_cmd .add_argument ("--url", default = DEFAULT_URL, help = f"địa chỉ MAVLink (mặc định: {DEFAULT_URL})")
    connect_cmd .add_argument ("--timeout", type = float, default = DEFAULT_TIMEOUT, help = f"số giây chờ HEARTBEAT của xe (mặc định: {DEFAULT_TIMEOUT:g})")
    return parser


def run_connect (url, timeout, connect_fn):
    """Thực hiện lệnh "connect": gọi connect_fn, in kết quả, trả mã thoát."""
    try:
        info = connect_fn (url = url, timeout = timeout)
    except ConnectionTimeout as error:
        # Không thấy xe: in thông báo lỗi ra stderr và báo lỗi bằng mã thoát.
        print (error, file = sys .stderr)
        return EXIT_NO_VEHICLE

    # Thấy xe: in một dòng thông tin xe ra stdout (đúng dạng AC2).
    print (f"Đã kết nối: system={info .system_id} component={info .component_id} autopilot={info .autopilot} type={info .vehicle_type}")
    return EXIT_OK


def main (argv = None, connect_fn = connect, app_fn = run_app):
    """Chạy app nếu không có lệnh con; lệnh connect giữ nguyên hành vi."""
    args = build_parser () .parse_args (argv)

    if args .command == "connect":
        return run_connect (args .url, args .timeout, connect_fn)

    return app_fn ()