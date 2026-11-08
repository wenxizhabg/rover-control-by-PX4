"""US-01/T3: kiểm tra việc đọc thông tin xe từ message HEARTBEAT.

Ý tưởng chung của file test này:
- Không cần mô phỏng hay mạng. Test tự tạo ra một HEARTBEAT giống hệt gói mà
  PX4 gửi qua mạng, rồi đưa cho hàm parse_heartbeat để xem kết quả có đúng không.
"""

# Bộ định nghĩa MAVLink 2, tập message chung ("common").
# Trong đó có: cách đóng gói / giải mã message, và các bảng tra số -> tên
# (ví dụ MAV_AUTOPILOT_PX4 = 12, MAV_TYPE_GROUND_ROVER = 10).
from pymavlink.dialects.v20 import common as mavlink

# Thứ cần kiểm tra (sẽ viết ở rover/vehicle_info.py).
# Lúc này file đó chưa có, nên chạy pytest sẽ fail ngay ở dòng import -> đúng như mong đợi.
from rover.vehicle_info import VehicleInfo, parse_heartbeat


def make_heartbeat (system_id, component_id, autopilot, vehicle_type):
    """Tạo một HEARTBEAT giống như nhận được từ mạng.

    Làm 2 bước để giống thật:
    1. Bên gửi: đóng gói HEARTBEAT thành dãy byte. system_id và component_id của bên gửi được ghi vào phần đầu (header) của gói.
    2. Bên nhận: giải mã dãy byte đó thành message, như app sẽ làm khi nhận từ mạng.
    """
    # Bên gửi, tự xưng là system_id / component_id.
    sender = mavlink. MAVLink (file = None, srcSystem = system_id, srcComponent = component_id)
    msg = sender. heartbeat_encode (
        type = vehicle_type,                        # loại thiết bị
        autopilot = autopilot,                      # loại firmware
        base_mode = 0,                              # các cờ trạng thái (không dùng trong test)
        custom_mode= 0,                             # chế độ riêng của PX4 (không dùng trong test)
        system_status = mavlink. MAV_STATE_STANDBY,  # trạng thái: đang chờ
    )
    data = msg. pack (sender)                         # -> dãy byte, đúng như gửi qua UDP

    # Bên nhận giải mã dãy byte thành message.
    receiver = mavlink. MAVLink (file = None)
    return receiver. decode (bytearray (data))


def test_1_heartbeat_tu_xe_px4_binh_thuong ():
    # Đầu vào: HEARTBEAT của xe mô phỏng (system 1, component 1, PX4, xe mặt đất).
    msg = make_heartbeat (
        system_id = 1,
        component_id = 1,
        autopilot = mavlink.MAV_AUTOPILOT_PX4,
        vehicle_type = mavlink.MAV_TYPE_GROUND_ROVER,
    )

    info = parse_heartbeat (msg)

    # Mong đợi: đọc ra đúng 4 thông tin, tên đã bỏ tiền tố "MAV_..._".
    assert info == VehicleInfo (
        system_id = 1,
        component_id = 1,
        autopilot = "PX4",
        vehicle_type = "GROUND_ROVER",
    )


def test_2_heartbeat_tu_QroundControl ():
    # Đầu vào: HEARTBEAT kiểu QGroundControl gửi:
    # autopilot = INVALID (không phải autopilot), type = GCS (trạm mặt đất).
    msg = make_heartbeat (
        system_id = 255,
        component_id = 190,
        autopilot = mavlink. MAV_AUTOPILOT_INVALID,
        vehicle_type = mavlink. MAV_TYPE_GCS,
    )

    # Mong đợi: None, nghĩa là "đây không phải xe", app sẽ bỏ qua gói này.
    assert parse_heartbeat (msg) is None


def test_3_loai_xe_la_khong_gay_loi ():
    # Đầu vào: firmware PX4 nhưng type = 250, số này không có trong bảng tra MAV_TYPE.
    msg = make_heartbeat (
        system_id = 1,
        component_id = 1,
        autopilot = mavlink. MAV_AUTOPILOT_PX4,
        vehicle_type = 250,
    )

    info = parse_heartbeat (msg)

    # Mong đợi: không lỗi; vẫn nhận là xe, loại xe ghi "UNKNOWN(250)" để người dùng biết số thật.
    assert info is not None
    assert info.autopilot == "PX4"
    assert info.vehicle_type == "UNKNOWN(250)"


def test_4_doc_system_id_tu_goi_khong_gan_cung ():
    # Đầu vào: HEARTBEAT của một xe khác, có system_id = 2.
    msg = make_heartbeat (
        system_id = 2,
        component_id = 1,
        autopilot = mavlink.MAV_AUTOPILOT_PX4,
        vehicle_type = mavlink.MAV_TYPE_GROUND_ROVER,
    )

    info = parse_heartbeat (msg)

    # Mong đợi: system_id = 2, lấy từ phần đầu của gói, không phải số 1 viết sẵn trong code.
    assert info.system_id == 2
    assert info.component_id == 1