"""US-01/T3: đọc thông tin xe từ message HEARTBEAT. File này chỉ xử lý dữ liệu (không mở mạng): nhận một HEARTBEAT đã giải mã, trả về thông tin xe ở dạng dễ đọc, hoặc None nếu HEARTBEAT đó không phải của xe (ví dụ của QGroundControl)."""

# dataclass: cách khai báo class chỉ để chứa dữ liệu; Python tự sinh hàm khởi tạo, hàm so sánh  =  =  và hàm in ra chuỗi.
from dataclasses import dataclass

# Bộ định nghĩa MAVLink 2, tập message chung "common"; dùng để lấy các hằng số (ví dụ MAV_AUTOPILOT_INVALID) và bảng tra số -> tên.
from pymavlink .dialects .v20 import common as mavlink


@dataclass (frozen = True)
class VehicleInfo:
    """Thông tin cơ bản của một xe, đọc từ HEARTBEAT. frozen = True nghĩa là tạo xong thì không sửa được các trường, tránh vô tình thay đổi thông tin xe ở chỗ khác trong chương trình."""

    system_id: int      # số hiệu của xe trên mạng MAVLink, lấy từ phần đầu (header) của gói
    component_id: int   # số hiệu của bộ phận gửi gói trong xe; 1 là autopilot
    autopilot: str      # tên loại firmware, ví dụ "PX4"
    vehicle_type: str   # tên loại thiết bị, ví dụ "GROUND_ROVER"


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
    # Phần mềm không phải autopilot gửi autopilot  =  MAV_AUTOPILOT_INVALID (số 8) -> không phải xe, bỏ qua.
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