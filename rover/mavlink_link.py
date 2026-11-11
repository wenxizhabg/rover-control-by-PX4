"""US-02/T2 & US-03a/T2: driver giao tiếp MAVLink qua UDP (tầng driver, hiện thực VehicleLink). Đọc HEARTBEAT, COMMAND_ACK không chờ và gửi lệnh mở / khóa xe."""

import os

# PX4 gửi MAVLink 2; bật biến môi trường để pymavlink xử lý nhất quán ngay từ đầu.
os .environ ["MAVLINK20"] = "1"

from pymavlink import mavutil
from pymavlink .dialects .v20 import common as mavlink

from rover .connection import DEFAULT_URL
from rover .types import ArmAck, Heartbeat, VehicleEvent
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
            elif msg_type == "COMMAND_ACK":
                # Chỉ chuyển đổi phản hồi của lệnh mở / khóa (MAV_CMD_COMPONENT_ARM_DISARM = 400); bỏ qua ACK lệnh khác.
                if msg .command == mavlink .MAV_CMD_COMPONENT_ARM_DISARM:
                    accepted = msg .result == mavlink .MAV_RESULT_ACCEPTED
                    events .append (ArmAck (accepted = accepted))

        return events

    def send_arm (self, arm: bool) -> None:
        """Gửi lệnh mở khóa (arm = True) hoặc khóa (arm = False) tới xe đã thấy gần nhất."""
        # Với udpin, chỉ gửi được sau khi đã nhận HEARTBEAT để biết system_id, component_id và địa chỉ UDP của xe.
        if self .last_system_id is None or self .last_component_id is None:
            return

        self .conn .mav .command_long_send (
            target_system = self .last_system_id,
            target_component = self .last_component_id,
            command = mavlink .MAV_CMD_COMPONENT_ARM_DISARM,
            confirmation = 0,
            param1 = 1 if arm else 0,
            param2 = 0,
            param3 = 0,
            param4 = 0,
            param5 = 0,
            param6 = 0,
            param7 = 0,
        )

    def close (self) -> None:
        """Đóng kết nối socket."""
        self .conn .close ()

