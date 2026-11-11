"""US-03a/T1: kiểm tra logic mở / khóa xe trong ArmControl (tầng xử lý thuần, không cần mạng hay mô phỏng)."""

from rover .arm_control import ArmControl
from rover .types import ArmAck, LinkState


def test_1_initial_armed_is_none ():
    # Đầu vào: tạo mới một ArmControl (), chưa nhận HEARTBEAT nào từ xe.
    ctrl = ArmControl ()

    # Mong đợi: armed = None để màn hình hiển thị "chưa rõ" trước khi thấy xe (phục vụ AC4).
    assert ctrl .armed is None


def test_2_heartbeat_updates_armed_state ():
    # Đầu vào: gọi on_heartbeat (True) rồi gọi tiếp on_heartbeat (False).
    ctrl = ArmControl ()
    ctrl .on_heartbeat (True)
    assert ctrl .armed is True

    ctrl .on_heartbeat (False)

    # Mong đợi: armed đổi theo HEARTBEAT mới nhất là False (phục vụ AC1, AC2: trạng thái lấy từ xe).
    assert ctrl .armed is False


def test_3_request_arm_when_connected_sends_command ():
    # Đầu vào: người dùng bấm mở khóa khi xe đang kết nối -> request (True, LinkState .CONNECTED).
    ctrl = ArmControl ()

    should_send, message = ctrl .request (True, LinkState .CONNECTED)

    # Mong đợi: cho phép gửi lệnh và báo "Đã gửi lệnh mở khóa" (phục vụ AC1).
    assert (should_send, message) == (True, "Đã gửi lệnh mở khóa")


def test_4_request_disarm_when_connected_sends_command ():
    # Đầu vào: người dùng bấm khóa khi xe đang kết nối -> request (False, LinkState .CONNECTED).
    ctrl = ArmControl ()

    should_send, message = ctrl .request (False, LinkState .CONNECTED)

    # Mong đợi: cho phép gửi lệnh và báo "Đã gửi lệnh khóa" (phục vụ AC2).
    assert (should_send, message) == (True, "Đã gửi lệnh khóa")


def test_5_request_when_disconnected_does_not_send ():
    # Đầu vào: người dùng bấm mở khóa khi LinkState .WAITING và khi LinkState .LOST.
    ctrl = ArmControl ()

    res_waiting = ctrl .request (True, LinkState .WAITING)
    res_lost = ctrl .request (True, LinkState .LOST)

    # Mong đợi: cả hai trường hợp đều không gửi lệnh và báo "Chưa kết nối xe" (phục vụ AC4).
    assert res_waiting == (False, "Chưa kết nối xe")
    assert res_lost == (False, "Chưa kết nối xe")


def test_6_on_ack_returns_message_for_last_request ():
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