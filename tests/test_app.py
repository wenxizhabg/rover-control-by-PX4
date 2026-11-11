"""US-04/T4: kiểm tra vòng lặp app bằng terminal và đồng hồ giả lập."""

from rover.app import RoverApp
from tests.fakes import FakeClock, FakeTerminal


def test_vong_dau_ve_khung_mac_dinh ():
    terminal = FakeTerminal ()
    app = RoverApp (terminal, FakeClock ())

    assert app .step () is True
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