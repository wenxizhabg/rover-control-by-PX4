"""Kiểm tra tầng 1 – vòng lặp RoverApp bằng terminal, đồng hồ và kênh xe giả lập (US-04/T4, US-02/T3, US-03a/T3)."""

from rover.app import RoverApp
from rover .core .model import ArmAck, Heartbeat, VehicleInfo
from tests.fakes import FakeClock, FakeTerminal, FakeVehicleLink


def test_vong_dau_ve_khung_mac_dinh ():
    terminal = FakeTerminal ()
    app = RoverApp (terminal, FakeClock ())

    assert app .step () is True
    assert not any ("Kết nối" in line for line in terminal .last_lines)
    assert "H: hướng dẫn   Q: thoát" in terminal .last_lines


def test_bam_h_hai_lan_an_hien_huong_dan ():
    terminal = FakeTerminal (["h", "h"])
    app = RoverApp (terminal, FakeClock ())

    assert app .step () is True
    assert "Q  thoát app" in terminal .last_lines

    assert app .step () is True
    assert "Q  thoát app" not in terminal .last_lines


def test_bam_q_dong_terminal_va_tra_ma_0 ():
    terminal = FakeTerminal (["q"])
    app = RoverApp (terminal, FakeClock ())

    assert app .run () == 0
    assert terminal .closed is True


def test_ctrl_c_dong_terminal_va_tra_ma_0 ():
    class InterruptingTerminal (FakeTerminal):
        def read_key (self) -> str | None:
            raise KeyboardInterrupt

    terminal = InterruptingTerminal ()
    app = RoverApp (terminal, FakeClock ())

    assert app .run () == 0
    assert terminal .closed is True


def test_link_status_is_waiting_before_first_heartbeat ():
    # Đầu vào: FakeVehicleLink chưa có sự kiện nào; gọi step () lần đầu.
    terminal = FakeTerminal ()
    app = RoverApp (terminal, FakeClock (), FakeVehicleLink ())

    # Mong đợi: dòng trạng thái hiển thị "ĐANG CHỜ XE" (phục vụ AC4).
    assert app .step () is True
    assert "Kết nối  : ĐANG CHỜ XE" in terminal .last_lines


def test_link_status_counts_received_heartbeat ():
    # Đầu vào: push một Heartbeat vào FakeVehicleLink; gọi step ().
    terminal = FakeTerminal ()
    clock = FakeClock ()
    link = FakeVehicleLink ()
    link .push (
        Heartbeat (
            info = VehicleInfo (
                system_id = 1,
                component_id = 1,
                autopilot = "PX4",
                vehicle_type = "GROUND_ROVER",
            ),
            armed = False,
        )
    )
    app = RoverApp (terminal, clock, link)

    # Mong đợi: dòng trạng thái có "ĐÃ KẾT NỐI" và tăng đếm "HEARTBEAT: 1" (phục vụ AC1).
    assert app .step () is True
    assert any ("ĐÃ KẾT NỐI" in line for line in terminal .last_lines)
    assert any ("HEARTBEAT: 1" in line for line in terminal .last_lines)


def test_link_status_changes_to_lost_and_reconnected ():
    # Đầu vào: push Heartbeat -> step () -> advance 3.5 s -> step () -> push Heartbeat -> step ().
    terminal = FakeTerminal ()
    clock = FakeClock ()
    link = FakeVehicleLink ()
    heartbeat = Heartbeat (
        info = VehicleInfo (
            system_id = 1,
            component_id = 1,
            autopilot = "PX4",
            vehicle_type = "GROUND_ROVER",
        ),
        armed = False,
    )
    link .push (heartbeat)
    app = RoverApp (terminal, clock, link)

    assert app .step () is True
    assert any ("ĐÃ KẾT NỐI" in line for line in terminal .last_lines)

    # Mong đợi lần 2: sau 3.5 s không có gói mới -> hiển thị "MẤT KẾT NỐI" (phục vụ AC2).
    clock .advance (3.5)
    assert app .step () is True
    assert any ("MẤT KẾT NỐI" in line for line in terminal .last_lines)

    # Mong đợi lần 3: nhận lại Heartbeat -> hiển thị "ĐÃ KẾT NỐI" và "HEARTBEAT: 2" (phục vụ AC3).
    link .push (heartbeat)
    assert app .step () is True
    assert any ("ĐÃ KẾT NỐI" in line for line in terminal .last_lines)
    assert any ("HEARTBEAT: 2" in line for line in terminal .last_lines)


def _make_heartbeat (armed: bool = False) -> Heartbeat:
    """Tạo một Heartbeat giả lập với trạng thái khóa armed."""
    return Heartbeat (
        info = VehicleInfo (
            system_id = 1,
            component_id = 1,
            autopilot = "PX4",
            vehicle_type = "GROUND_ROVER",
        ),
        armed = armed,
    )


def test_press_r_when_connected_sends_arm_and_updates_status ():
    # Đầu vào: push Heartbeat (armed = False) -> step () -> bấm "r" -> step () -> push Heartbeat (armed = True) -> step ().
    terminal = FakeTerminal ([None, "r"])
    link = FakeVehicleLink ()
    app = RoverApp (terminal, FakeClock (), link)

    link .push (_make_heartbeat (armed = False))
    assert app .step () is True
    assert any ("ĐÃ KHÓA" in line for line in terminal .last_lines)

    assert app .step () is True
    # Mong đợi ở bước bấm R: đã gửi lệnh mở khóa và hiện thông báo "Đã gửi lệnh mở khóa" (phục vụ US-03a AC1).
    assert link .sent_arm == [True]
    assert any ("Đã gửi lệnh mở khóa" in line for line in terminal .last_lines)

    link .push (_make_heartbeat (armed = True))
    assert app .step () is True
    # Mong đợi ở bước sau khi nhận HEARTBEAT mới: khung cuối hiện "ĐÃ MỞ KHÓA" (phục vụ US-03a AC1).
    assert any ("ĐÃ MỞ KHÓA" in line for line in terminal .last_lines)


def test_arm_ack_rejected_shows_message ():
    # Đầu vào: đã kết nối -> bấm "r" -> step () -> push ArmAck (False) -> step ().
    terminal = FakeTerminal ([None, "r"])
    link = FakeVehicleLink ()
    app = RoverApp (terminal, FakeClock (), link)

    link .push (_make_heartbeat (armed = False))
    assert app .step () is True
    assert app .step () is True

    link .push (ArmAck (False))
    assert app .step () is True

    # Mong đợi: vùng thông báo hiện "Xe từ chối lệnh mở khóa" (phục vụ US-03a AC3).
    assert any ("Xe từ chối lệnh mở khóa" in line for line in terminal .last_lines)


def test_press_r_when_not_connected_does_not_send ():
    # Đầu vào: chưa có Heartbeat; người dùng bấm "r"; gọi step ().
    terminal = FakeTerminal (["r"])
    link = FakeVehicleLink ()
    app = RoverApp (terminal, FakeClock (), link)

    assert app .step () is True

    # Mong đợi: không gửi lệnh nào và khung hiện "Chưa kết nối xe" (phục vụ US-03a AC4).
    assert link .sent_arm == []
    assert any ("Chưa kết nối xe" in line for line in terminal .last_lines)