"""Tầng 4 – driver MAVLink qua UDP (hiện thực VehicleLink): giải mã HEARTBEAT, COMMAND_ACK của xe và gửi lệnh mở / khóa xe."""

import os

# PX4 gửi gói MAVLink 2. pymavlink mặc định dùng MAVLink 1 và chỉ tự chuyển sang bản 2 khi nhận gói đầu tiên có byte mở đầu 0xFD; bật MAVLINK20 ngay từ đầu để app làm việc với MAVLink 2 một cách rõ ràng, không phụ thuộc vào cơ chế tự chuyển đó.
os .environ ["MAVLINK20"] = "1"

# mavutil: phần của pymavlink lo việc mở cổng (UDP, serial...) và nhận / giải mã message.
from pymavlink import mavutil
# Bộ định nghĩa MAVLink 2, tập message chung "common"; dùng để lấy các hằng số (ví dụ MAV_AUTOPILOT_INVALID) và bảng tra số -> tên.
from pymavlink .dialects .v20 import common as mavlink

from rover .core .model import ArmAck, Heartbeat, VehicleEvent, VehicleInfo

# Địa chỉ mặc định: nghe (udpin) trên mọi địa chỉ của máy, cổng 14540, là cổng PX4 SITL gửi MAVLink cho ứng dụng (instance mode Onboard).
DEFAULT_URL = "udpin:0.0.0.0:14540"


def _enum_name (enum_name, value, prefix):
    """Đổi một con số thành tên dễ đọc bằng bảng tra của MAVLink, đồng thời bỏ tiền tố. Ví dụ: bảng "MAV_TYPE", số 10, tiền tố "MAV_TYPE_" -> "GROUND_ROVER". Số không có trong bảng thì trả "UNKNOWN(<số>)" thay vì báo lỗi."""
    # mavlink.enums là bảng tra lớn: tên bảng -> {số -> mục}; .get trả None nếu số không có trong bảng.
    entry = mavlink .enums [enum_name] .get (value)

    # Không có trong bảng, hoặc là mục đánh dấu cuối bảng "..._ENUM_END" do pymavlink tự thêm (không phải loại thật) -> ghi rõ số thật để người dùng biết.
    if entry is None or entry .name .endswith ("_ENUM_END"):
        return f"UNKNOWN({value})"

    # Bỏ phần tiền tố: "MAV_TYPE_GROUND_ROVER" -> "GROUND_ROVER".
    return entry.name [len (prefix):]


def parse_heartbeat (msg):
    """Nhận một message HEARTBEAT đã giải mã; trả VehicleInfo nếu đó là xe, trả None nếu không phải xe (autopilot = INVALID, ví dụ QGroundControl hay app khác)."""
    # Phần mềm không phải autopilot gửi autopilot = MAV_AUTOPILOT_INVALID (số 8) -> không phải xe, bỏ qua.
    if msg .autopilot == mavlink .MAV_AUTOPILOT_INVALID:
        return None

    return VehicleInfo (
        # system_id và component_id nằm ở phần đầu (header) của gói, không nằm trong nội dung HEARTBEAT; pymavlink đọc chúng qua 2 hàm dưới (tên hàm theo cách đặt của thư viện).
        system_id = msg .get_srcSystem(),
        component_id = msg .get_srcComponent(),
        # autopilot và type nằm trong nội dung HEARTBEAT, là con số -> đổi sang tên.
        autopilot = _enum_name ("MAV_AUTOPILOT", msg .autopilot, "MAV_AUTOPILOT_"),
        vehicle_type = _enum_name ("MAV_TYPE", msg .type, "MAV_TYPE_"),
    )


class MavlinkVehicleLink:
    """Kênh nhận dữ liệu từ xe qua MAVLink/UDP; poll () đọc hết gói đang chờ mà không làm đơ app."""

    def __init__ (self, url: str = DEFAULT_URL) -> None:
        # udpin không chặn khi tạo nên có thể mở socket lắng nghe ngay.
        self .conn = mavutil .mavlink_connection (url, dialect = "common")
        # Ghi nhớ xe thấy gần nhất để gửi lệnh mở / khóa đúng xe.
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
