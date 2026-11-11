"""US-01/T4: kiểm tra hàm connect: mở cổng UDP, chờ HEARTBEAT của xe, báo ConnectionTimeout khi hết giờ.

Ý tưởng chung của file test này:
1. Không cần mô phỏng PX4. Mỗi test chạy một "giả lập" trên chính máy (localhost): một luồng phụ liên tục gửi gói HEARTBEAT tới một cổng UDP, giống như PX4 gửi tới cổng 14540.
2. Hàm connect nghe ở đúng cổng đó và phải phản ứng đúng với từng tình huống: có xe, không có ai, chỉ có trạm mặt đất, trạm mặt đất gửi trước rồi mới tới xe.
3. Mỗi test dùng một cổng trống ngẫu nhiên, nên không đụng cổng 14540 của mô phỏng thật đang chạy (nếu có).
"""

# time: đo thời gian (kiểm tra hết giờ đúng lúc).
import time

# pytest .raises dùng để kiểm tra "đoạn code này phải ném ra lỗi X".
import pytest

# Các hàm và giả lập MAVLink chuyển sang tests/mavlink_sim.py từ US-02/T2.
from tests .mavlink_sim import GCS_HEARTBEAT, VEHICLE_HEARTBEAT, HeartbeatSimulator, find_free_port

# Thứ cần kiểm tra (sẽ viết ở rover/connection.py). Lúc này file đó chưa có, nên chạy pytest sẽ báo lỗi ngay ở dòng import -> đúng như mong đợi.
from rover .connection import ConnectionTimeout, connect
from rover .vehicle_info import VehicleInfo


def test_1_ket_noi_duoc_voi_gia_lap_xe_px4 ():
    # Đầu vào: giả lập xe PX4 rover gửi HEARTBEAT (MAVLink 2) liên tục trong 5 giây.
    port = find_free_port ()

    with HeartbeatSimulator (port, [(VEHICLE_HEARTBEAT, 5)]):
        info = connect (url = f"udpin:127.0.0.1:{port}", timeout = 3)

    # Mong đợi: connect nhận ra xe và trả đúng thông tin xe; đồng thời chứng minh app giải mã được gói MAVLink 2.
    assert info == VehicleInfo (
        system_id = 1,
        component_id = 1,
        autopilot = "PX4",
        vehicle_type = "GROUND_ROVER",
    )


def test_2_khong_co_ai_gui_thi_bao_het_gio ():
    # Đầu vào: không có giả lập nào gửi gói; thời gian chờ 0,5 giây.
    port = find_free_port ()
    start = time .monotonic ()

    # Mong đợi: connect ném ConnectionTimeout (đúng AC3: hết giờ thì báo lỗi).
    with pytest .raises (ConnectionTimeout):
        connect (url = f"udpin:127.0.0.1:{port}", timeout = 0.5)

    # Mong đợi: báo lỗi sau khoảng 0,5 giây; không sớm hơn (chờ đủ thời gian) và không treo (không quá lâu).
    elapsed = time .monotonic () - start
    assert 0.4 <= elapsed < 2.0


def test_3_chi_co_tram_mat_dat_thi_van_bao_het_gio ():
    # Đầu vào: chỉ có giả lập trạm mặt đất (QGroundControl) gửi HEARTBEAT; thời gian chờ 0,5 giây.
    port = find_free_port ()

    # Mong đợi: vẫn ném ConnectionTimeout, vì trạm mặt đất không phải xe.
    with HeartbeatSimulator (port, [(GCS_HEARTBEAT, 5)]):
        with pytest .raises (ConnectionTimeout):
            connect (url = f"udpin:127.0.0.1:{port}", timeout = 0.5)


def test_4_bo_qua_tram_mat_dat_va_cho_tiep_toi_khi_gap_xe ():
    # Đầu vào: giả lập trạm mặt đất gửi trong 0,5 giây đầu, sau đó giả lập xe mới bắt đầu gửi.
    port = find_free_port ()

    with HeartbeatSimulator (port, [(GCS_HEARTBEAT, 0.5), (VEHICLE_HEARTBEAT, 5)]):
        info = connect (url = f"udpin:127.0.0.1:{port}", timeout = 3)

    # Mong đợi: connect không dừng ở gói đầu tiên (của trạm mặt đất), mà chờ tiếp và trả thông tin của xe.
    assert info .autopilot == "PX4"
    assert info .vehicle_type == "GROUND_ROVER"