"""US-01/T4: kết nối tới xe qua MAVLink/UDP. Mở cổng UDP, chờ HEARTBEAT của autopilot (bỏ qua HEARTBEAT của phần mềm khác như QGroundControl), trả về thông tin xe; hết thời gian chờ mà không thấy xe thì báo lỗi ConnectionTimeout."""

# os: dùng để bật chế độ MAVLink 2 cho pymavlink qua biến môi trường.
import os
# time: đo thời gian để tính mốc hết giờ.
import time

# PX4 gửi gói MAVLink 2. pymavlink mặc định dùng MAVLink 1 và chỉ tự chuyển sang bản 2 khi nhận gói đầu tiên có byte mở đầu 0xFD; bật MAVLINK20 ngay từ đầu để app làm việc với MAVLink 2 một cách rõ ràng, không phụ thuộc vào cơ chế tự chuyển đó.
os .environ ["MAVLINK20"] = "1"

# mavutil: phần của pymavlink lo việc mở cổng (UDP, serial...) và nhận / giải mã message.
from pymavlink import mavutil

from rover .vehicle_info import parse_heartbeat

# Địa chỉ mặc định: nghe (udpin) trên mọi địa chỉ của máy, cổng 14540, là cổng PX4 SITL gửi MAVLink cho ứng dụng (instance mode Onboard).
DEFAULT_URL = "udpin:0.0.0.0:14540"
# Thời gian chờ mặc định, tính bằng giây.
DEFAULT_TIMEOUT = 10.0


class ConnectionTimeout (Exception):
    """Lỗi riêng của app: hết thời gian chờ mà không nhận được HEARTBEAT nào của xe."""


def connect (url = DEFAULT_URL, timeout = DEFAULT_TIMEOUT):
    """Mở cổng theo url, chờ HEARTBEAT của xe trong tối đa timeout giây.

    Kết quả:
    1. Gặp HEARTBEAT của xe -> trả VehicleInfo.
    2. Hết giờ mà không gặp -> ném ConnectionTimeout.
    3. Dù kết quả nào thì cổng cũng được đóng trước khi hàm kết thúc.
    """
    # Mở cổng; dialect "common" là tập message chung mà PX4 dùng.
    conn = mavutil .mavlink_connection (url, dialect = "common")
    try:
        # Mốc hết giờ tính một lần từ đầu, để tổng thời gian chờ đúng bằng timeout dù nhận được bao nhiêu gói không phải của xe.
        deadline = time .monotonic () + timeout
        while True:
            remaining = deadline - time .monotonic ()
            if remaining <= 0:
                raise ConnectionTimeout (f"Không nhận được heartbeat từ xe sau {timeout:g} s")

            # Chờ một HEARTBEAT, tối đa bằng thời gian còn lại; không có gói nào thì trả None.
            msg = conn .recv_match (type = "HEARTBEAT", blocking = True, timeout = remaining)
            if msg is None:
                continue  # hết phần thời gian còn lại -> vòng lặp kiểm tra mốc và ném lỗi

            # Dùng hàm của T3: trả VehicleInfo nếu là xe, None nếu là phần mềm khác (bỏ qua, chờ tiếp).
            info = parse_heartbeat (msg)
            if info is not None:
                return info
    finally:
        conn .close ()  # luôn đóng cổng, kể cả khi ném lỗi