import pytest

from psvr_display.status import parse_status


def _report(flags: int = 0x00, volume: int = 0, minutes: int = 0) -> bytes:
    report = bytearray(20)
    report[0] = 0xF0
    report[4] = flags
    report[5] = volume
    report[8] = minutes
    return bytes(report)


def test_powered_on_bit():
    status = parse_status(_report(flags=0x01))
    assert status.powered_on is True
    assert status.hmd_worn is False
    assert status.cinematic_mode is False


def test_all_flags_combined():
    flags = 0x01 | 0x02 | 0x04 | 0x10 | 0x20
    status = parse_status(_report(flags=flags))
    assert status.powered_on is True
    assert status.hmd_worn is True
    assert status.cinematic_mode is True
    assert status.headphones_connected is True
    assert status.mic_muted is True


def test_volume_and_display_on_minutes():
    status = parse_status(_report(volume=17, minutes=42))
    assert status.volume == 17
    assert status.display_on_minutes == 42


def test_rejects_non_status_report():
    bad = bytearray(20)
    bad[0] = 0x00
    with pytest.raises(ValueError):
        parse_status(bytes(bad))


def test_rejects_short_report():
    with pytest.raises(ValueError):
        parse_status(bytes([0xF0, 0x00]))
