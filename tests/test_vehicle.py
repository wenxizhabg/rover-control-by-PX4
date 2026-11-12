"""Kiểm tra tầng 2 – trạng thái của xe: LinkMonitor (US-02/T1), ArmControl (US-03a/T1) và DriveController (US-03b/T1); thời gian giả lập, không cần mạng hay mô phỏng."""

from rover .core .model import Action, ArmAck, LinkState
from rover .core .vehicle import (
    DRIVE_DURATION_S,
    DRIVE_SPEED,
    LINK_TIMEOUT_S,
    TURN_SPEED,
    ArmControl,
    DriveController,
    LinkMonitor,
)


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


def test_6_initial_armed_is_none ():
    # Đầu vào: tạo mới một ArmControl (), chưa nhận HEARTBEAT nào từ xe.
    ctrl = ArmControl ()

    # Mong đợi: armed = None để màn hình hiển thị "chưa rõ" trước khi thấy xe (phục vụ AC4).
    assert ctrl .armed is None


def test_7_heartbeat_updates_armed_state ():
    # Đầu vào: gọi on_heartbeat (True) rồi gọi tiếp on_heartbeat (False).
    ctrl = ArmControl ()
    ctrl .on_heartbeat (True)
    assert ctrl .armed is True

    ctrl .on_heartbeat (False)

    # Mong đợi: armed đổi theo HEARTBEAT mới nhất là False (phục vụ AC1, AC2: trạng thái lấy từ xe).
    assert ctrl .armed is False


def test_8_request_arm_when_connected_sends_command ():
    # Đầu vào: người dùng bấm mở khóa khi xe đang kết nối -> request (True, LinkState .CONNECTED).
    ctrl = ArmControl ()

    should_send, message = ctrl .request (True, LinkState .CONNECTED)

    # Mong đợi: cho phép gửi lệnh và báo "Đã gửi lệnh mở khóa" (phục vụ AC1).
    assert (should_send, message) == (True, "Đã gửi lệnh mở khóa")


def test_9_request_disarm_when_connected_sends_command ():
    # Đầu vào: người dùng bấm khóa khi xe đang kết nối -> request (False, LinkState .CONNECTED).
    ctrl = ArmControl ()

    should_send, message = ctrl .request (False, LinkState .CONNECTED)

    # Mong đợi: cho phép gửi lệnh và báo "Đã gửi lệnh khóa" (phục vụ AC2).
    assert (should_send, message) == (True, "Đã gửi lệnh khóa")


def test_10_request_when_disconnected_does_not_send ():
    # Đầu vào: người dùng bấm mở khóa khi LinkState .WAITING và khi LinkState .LOST.
    ctrl = ArmControl ()

    res_waiting = ctrl .request (True, LinkState .WAITING)
    res_lost = ctrl .request (True, LinkState .LOST)

    # Mong đợi: cả hai trường hợp đều không gửi lệnh và báo "Chưa kết nối xe" (phục vụ AC4).
    assert res_waiting == (False, "Chưa kết nối xe")
    assert res_lost == (False, "Chưa kết nối xe")


def test_11_on_ack_returns_message_for_last_request ():
    # Đầu vào: gửi mở khóa -> bị từ chối; gửi khóa -> bị từ chối; gửi mở khóa -> được chấp nhận; gửi khóa -> được chấp nhận.
    ctrl = ArmControl ()

    ctrl .request (True, LinkState .CONNECTED)
    msg_arm_denied = ctrl .on_ack (ArmAck (False))

    ctrl .request (False, LinkState .CONNECTED)
    msg_disarm_denied = ctrl .on_ack (ArmAck (False))

    ctrl .request (True, LinkState .CONNECTED)
    msg_arm_accepted = ctrl .on_ack (ArmAck (True))

    ctrl .request (False, LinkState .CONNECTED)
    msg_disarm_accepted = ctrl .on_ack (ArmAck (True))

    # Mong đợi: thông báo khớp đúng với lệnh mở / khóa vừa gửi gần nhất (phục vụ AC1, AC2, AC3).
    assert msg_arm_denied == "Xe từ chối lệnh mở khóa"
    assert msg_disarm_denied == "Xe từ chối lệnh khóa"
    assert msg_arm_accepted == "Xe chấp nhận lệnh mở khóa"
    assert msg_disarm_accepted == "Xe chấp nhận lệnh khóa"


def test_12_drive_controller_initial_state_is_idle ():
    # Đầu vào: tạo mới DriveController (); kiểm tra tại now = 0.0.
    ctrl = DriveController ()

    # Mong đợi: đứng yên (setpoint = (0.0, 0.0), active_action = None, remaining_s = 0.0) (phục vụ AC1).
    assert ctrl .setpoint (0.0) == (0.0, 0.0)
    assert ctrl .active_action (0.0) is None
    assert ctrl .remaining_s (0.0) == 0.0


def test_13_drive_forward_for_one_second_then_stops ():
    # Đầu vào: bắt đầu tiến tại now = 10.0; kiểm tra tại 10.5, 10.99 và đúng mốc 11.0 s.
    ctrl = DriveController ()
    ctrl .start (Action .FORWARD, 10.0)

    # Mong đợi: trong 1 giây đầu trả mức tiến DRIVE_SPEED; đúng 11.0 s tự dừng (phục vụ AC1).
    assert ctrl .setpoint (10.5) == (DRIVE_SPEED, 0.0)
    assert ctrl .setpoint (10.99) == (DRIVE_SPEED, 0.0)
    assert ctrl .setpoint (11.0) == (0.0, 0.0)


def test_14_drive_backward_and_turn_directions ():
    # Đầu vào: kiểm tra các hướng lùi (BACKWARD), quay trái (TURN_LEFT), quay phải (TURN_RIGHT) tại now = 0.5.
    ctrl = DriveController ()

    ctrl .start (Action .BACKWARD, 0.0)
    assert ctrl .setpoint (0.5) == (-DRIVE_SPEED, 0.0)

    ctrl .start (Action .TURN_LEFT, 0.0)
    assert ctrl .setpoint (0.5) == (0.0, -TURN_SPEED)

    ctrl .start (Action .TURN_RIGHT, 0.0)
    # Mong đợi: đúng hướng và dấu quy ước (phục vụ AC2).
    assert ctrl .setpoint (0.5) == (0.0, TURN_SPEED)


def test_15_drive_stop_stops_immediately ():
    # Đầu vào: đang tiến tại now = 0.0 thì gọi stop () ngay; kiểm tra tại now = 0.2.
    ctrl = DriveController ()
    ctrl .start (Action .FORWARD, 0.0)
    ctrl .stop ()

    # Mong đợi: dừng ngay lập tức, trả (0.0, 0.0) và active_action là None (phục vụ AC3).
    assert ctrl .setpoint (0.2) == (0.0, 0.0)
    assert ctrl .active_action (0.2) is None


def test_16_repeated_drive_command_resets_timeout ():
    # Đầu vào: bấm tiến tại now = 0.0, sau đó 0.8 s bấm tiếp tiến lần nữa; kiểm tra tại 1.5 s và 1.8 s.
    ctrl = DriveController ()
    ctrl .start (Action .FORWARD, 0.0)
    ctrl .start (Action .FORWARD, 0.8)

    # Mong đợi: thời gian 1 s được tính lại từ lần bấm cuối; 1.5 s vẫn chạy, 1.8 s mới dừng (phục vụ AC3).
    assert ctrl .setpoint (1.5) == (DRIVE_SPEED, 0.0)
    assert ctrl .setpoint (1.8) == (0.0, 0.0)


def test_17_drive_active_action_and_remaining_seconds ():
    # Đầu vào: bắt đầu quay phải tại now = 2.0; kiểm tra hướng và thời gian còn lại tại now = 2.4 và 3.5.
    ctrl = DriveController ()
    ctrl .start (Action .TURN_RIGHT, 2.0)

    # Mong đợi: active_action trả TURN_RIGHT; remaining_s trả 0.6 s; sau khi hết giờ trả 0.0 (phục vụ AC1, AC2).
    assert ctrl .active_action (2.4) == Action .TURN_RIGHT
    assert abs (ctrl .remaining_s (2.4) - 0.6) < 1e-9
    assert ctrl .remaining_s (3.5) == 0.0
