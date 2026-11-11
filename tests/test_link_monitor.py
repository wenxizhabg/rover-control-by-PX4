"""US-02/T1: kiểm tra LinkMonitor quản lý trạng thái kết nối xe (tầng xử lý thuần, thời gian giả lập)."""

from rover .link_monitor import LINK_TIMEOUT_S, LinkMonitor
from rover .types import LinkState


def test_1_initial_state_is_waiting ():
    # Đầu vào: LinkMonitor () mới tạo, chưa nhận HEARTBEAT nào; kiểm tra tại now = 10.0.
    monitor = LinkMonitor ()

    # Mong đợi: trạng thái WAITING, heartbeat_count = 0, seconds_since_last là None (phục vụ AC4).
    assert monitor .state (10.0) == LinkState .WAITING
    assert monitor .heartbeat_count == 0
    assert monitor .seconds_since_last (10.0) is None


def test_2_heartbeat_sets_connected ():
    # Đầu vào: nhận một HEARTBEAT tại now = 1.0; kiểm tra trạng thái tại now = 1.5.
    monitor = LinkMonitor ()
    monitor .on_heartbeat (1.0)

    # Mong đợi: trạng thái CONNECTED, heartbeat_count = 1, seconds_since_last = 0.5 s (phục vụ AC1).
    assert monitor .state (1.5) == LinkState .CONNECTED
    assert monitor .heartbeat_count == 1
    assert monitor .seconds_since_last (1.5) == 0.5


def test_3_timeout_threshold_connected_then_lost ():
    # Đầu vào: nhận HEARTBEAT tại 1.0; kiểm tra tại đúng ngưỡng 1.0 + 3.0 = 4.0 và quá ngưỡng 4.1.
    monitor = LinkMonitor (timeout_s = LINK_TIMEOUT_S)
    monitor .on_heartbeat (1.0)

    # Mong đợi: đúng ngưỡng 3.0 s vẫn CONNECTED, lớn hơn 3.0 s mới LOST (phục vụ AC2: không báo mất sớm).
    assert monitor .state (4.0) == LinkState .CONNECTED
    assert monitor .state (4.1) == LinkState .LOST


def test_4_lost_then_reconnected ():
    # Đầu vào: nhận HEARTBEAT tại 1.0 -> kiểm tra tại 10.0 (mất) -> nhận HEARTBEAT tiếp tại 10.0 -> kiểm tra tại 10.2.
    monitor = LinkMonitor ()
    monitor .on_heartbeat (1.0)
    assert monitor .state (10.0) == LinkState .LOST

    monitor .on_heartbeat (10.0)

    # Mong đợi: chuyển lại sang CONNECTED, heartbeat_count = 2 (phục vụ AC3: xe bật lại tự kết nối).
    assert monitor .state (10.2) == LinkState .CONNECTED
    assert monitor .heartbeat_count == 2


def test_5_regular_heartbeats_stay_connected ():
    # Đầu vào: nhận HEARTBEAT đều đặn mỗi giây tại 0, 1, 2, ..., 30; kiểm tra tại mỗi thời điểm cộng thêm 0.9 s.
    monitor = LinkMonitor ()
    for t in range (31):
        monitor .on_heartbeat (float (t))
        # Mong đợi: luôn duy trì trạng thái CONNECTED trong suốt 30 s (phục vụ AC1).
        assert monitor .state (float (t) + 0.9) == LinkState .CONNECTED

    assert monitor .heartbeat_count == 31
