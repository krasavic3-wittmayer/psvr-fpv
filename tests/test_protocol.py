import pytest

from psvr_display import protocol


def test_power_on_bytes():
    assert protocol.PACKET_POWER_ON == bytes.fromhex("1700AA0401000000")


def test_power_off_bytes():
    assert protocol.PACKET_POWER_OFF == bytes.fromhex("1700AA0400000000")


def test_vrmode_on_bytes():
    assert protocol.PACKET_VRMODE_ON == bytes.fromhex("2300AA0401000000")


def test_cinematic_on_bytes():
    assert protocol.PACKET_CINEMATIC_ON == bytes.fromhex("2300AA0400000000")


def test_pu_power_off_bytes():
    assert protocol.PACKET_PU_POWER_OFF == bytes.fromhex("1300AA0401000000")


def test_recentre_screen_bytes():
    assert protocol.PACKET_RECENTRE_SCREEN == bytes.fromhex("1B00AA0400000000")


def test_all_packets_start_with_aa_magic():
    for packet in (
        protocol.PACKET_POWER_ON,
        protocol.PACKET_POWER_OFF,
        protocol.PACKET_VRMODE_ON,
        protocol.PACKET_CINEMATIC_ON,
        protocol.PACKET_PU_POWER_OFF,
        protocol.PACKET_RECENTRE_SCREEN,
    ):
        assert packet[2] == 0xAA


def test_cinematic_screen_defaults():
    packet = protocol.build_cinematic_screen_settings()
    assert packet[:4] == bytes([0x21, 0x00, 0xAA, 0x10])
    payload = packet[4:]
    assert len(payload) == 16
    assert payload[0] == 0x00  # locked by default
    assert payload[1] == 52    # size
    assert payload[2] == 35    # distance
    assert payload[3] == 20    # mist
    assert payload[10] == 20   # brightness
    assert payload[12] == 0    # social screen resolution


def test_cinematic_screen_free_flag():
    packet = protocol.build_cinematic_screen_settings(locked=False)
    assert packet[4] == 0x40


@pytest.mark.parametrize(
    "kwargs",
    [
        {"size": 25},
        {"size": 101},
        {"distance": 19},
        {"distance": 51},
        {"mist": 0},
        {"mist": 41},
        {"brightness": 0},
        {"brightness": 33},
        {"social_screen_resolution": 5},
    ],
)
def test_cinematic_screen_rejects_out_of_range(kwargs):
    with pytest.raises(ValueError):
        protocol.build_cinematic_screen_settings(**kwargs)
