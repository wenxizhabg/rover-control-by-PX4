"""US-02/T2: driver giao tiếp MAVLink qua UDP (tầng driver, hiện thực VehicleLink). Đọc gói HEARTBEAT không chờ và giải mã thành sự kiện Heartbeat."""

import os

# PX4 gửi MAVLink 2; bật biến môi trường để pymavlink xử lý nhất quán ngay từ đầu.
os .environ ["MAVLINK20"] = "1"

from pymavlink import mavutil
from pymavlink .dialects .v20 import common as mavlink

from rover .connection import DEFAULT_URL
from rover .types import Heartbeat, VehicleEvent
from rover .vehicle_info import parse_heartbeat


class MavlinkVehicleLink:
    """Kênh nhận dữ liệu từ xe qua MAVLink/UDP; poll () đọc hết gói đang chờ mà không làm đơ app."""

    def __init__ (self, url: str = DEFAULT_URL) -> None:
        # udpin không chặn khi tạo nên có thể mở socket lắng nghe ngay.
        self .conn = mavutil .mavlink_connection (url, dialect = "common")
        # Ghi nhớ xe thấy gần nhất để phục vụ US-03a/T2 gửi lệnh mở/khóa.
        self .last_system_id: int | None = None
        self .last_component_id: int | None = None

    def poll (self) -> list [VehicleEvent]:
        """Đọc mọi gói đang chờ trong bộ đệm UDP, không chờ gói mới; trả các gói hợp lệ của xe."""
        events: list [VehicleEvent] = []
        while True:
            # blocking = False: có gói trả ngay, không có trả None lập tức.
            msg = self .conn .recv_match (blocking = False)
            if msg is None:
                break

            msg_type = msg .get_type ()
            if msg_type == "HEARTBEAT":
                info = parse_heartbeat (msg)
                # Bỏ qua gói không phải từ xe (ví dụ QGroundControl có autopilot = INVALID).
                if info is not None:
                    self .last_system_id = info .system_id
                    self .last_component_id = info .component_id
                    armed = bool (msg .base_mode & mavlink .MAV_MODE_FLAG_SAFETY_ARMED)
                    events .append (Heartbeat (info = info, armed = armed))

        return events

    def send_arm (self, arm: bool) -> None:
        """Gửi lệnh mở/khóa xe (được cài đặt chi tiết trong US-03a/T2)."""
        pass

    def close (self) -> None:
        """Đóng kết nối socket."""
        self .conn .close ()

