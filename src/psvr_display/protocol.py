"""PSVR1 Processing Unit USB control protocol.

Every packet definition used by this project lives here, and nowhere else,
so the byte-exact protocol is auditable and testable without hardware.

Packet format: [0] register, [1] sub-register (send 0x00), [2] 0xAA magic,
[3] payload length (4, 8 or 16), then the payload. The whole packet is
written to the interface-5 HID OUT endpoint as an interrupt transfer.

Confidence marks follow docs/protocol.md. Sources: OpenHMD drv_psvr,
Monado drv_psvr, PSVRFramework wiki (see docs/protocol.md for links).
"""

from __future__ import annotations

VENDOR_ID = 0x054C
PRODUCT_ID = 0x09AF

CONTROL_INTERFACE = 5   # "PS VR Control" HID interface — the only one this project touches
SENSOR_INTERFACE = 4    # "PS VR Sensor" (IMU) — not used

EP_OUT = 0x04  # interrupt OUT, 64 bytes
EP_IN = 0x84   # interrupt IN, 64 bytes

STATUS_REPORT_ID = 0xF0
STATUS_REPORT_LEN = 20

# --- confirmed (present in >=2 independent sources) ---
PACKET_POWER_ON = bytes.fromhex("1700AA0401000000")
PACKET_POWER_OFF = bytes.fromhex("1700AA0400000000")
PACKET_VRMODE_ON = bytes.fromhex("2300AA0401000000")
PACKET_CINEMATIC_ON = bytes.fromhex("2300AA0400000000")  # i.e. VR mode off

# --- reported (single source: psvrd / pyPSVR) ---
PACKET_PU_POWER_OFF = bytes.fromhex("1300AA0401000000")
PACKET_RECENTRE_SCREEN = bytes.fromhex("1B00AA0400000000")

# Cinematic screen settings (report 0x21, 16-byte payload). Field meanings
# are reported/provisional (pyPSVR parameter clamping) — verify on hardware.
_SCREEN_SIZE_RANGE = (26, 100)
_SCREEN_DISTANCE_RANGE = (20, 50)
_SCREEN_MIST_RANGE = (1, 40)
_SCREEN_BRIGHTNESS_RANGE = (1, 32)
_SCREEN_SOCIAL_RES_RANGE = (0, 4)


def build_cinematic_screen_settings(
    *,
    locked: bool = True,
    size: int = 52,
    distance: int = 35,
    mist: int = 20,
    brightness: int = 20,
    social_screen_resolution: int = 0,
) -> bytes:
    """Build the 0x21 cinematic-screen-settings packet.

    Out-of-range values are rejected here rather than left for the device
    to reject with a "Bad sidetone value" error report.
    """
    _check_range("size", size, _SCREEN_SIZE_RANGE)
    _check_range("distance", distance, _SCREEN_DISTANCE_RANGE)
    _check_range("mist", mist, _SCREEN_MIST_RANGE)
    _check_range("brightness", brightness, _SCREEN_BRIGHTNESS_RANGE)
    _check_range("social_screen_resolution", social_screen_resolution, _SCREEN_SOCIAL_RES_RANGE)

    payload = bytearray(16)
    payload[0] = 0x00 if locked else 0x40
    payload[1] = size
    payload[2] = distance
    payload[3] = mist
    payload[10] = brightness
    payload[12] = social_screen_resolution

    header = bytes([0x21, 0x00, 0xAA, 0x10])
    return header + bytes(payload)


def _check_range(name: str, value: int, bounds: tuple[int, int]) -> None:
    lo, hi = bounds
    if not (lo <= value <= hi):
        raise ValueError(f"{name}={value} out of range [{lo}, {hi}]")
