"""Parse the PSVR PU's unsolicited 0xF0 status report."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PsvrStatus:
    raw: bytes
    powered_on: bool
    hmd_worn: bool
    cinematic_mode: bool
    headphones_connected: bool
    mic_muted: bool
    volume: int
    display_on_minutes: int


def parse_status(report: bytes) -> PsvrStatus:
    """Parse a 20-byte 0xF0 status report.

    Byte 4 is the status bitfield, byte 5 volume, byte 8 display-on time
    in minutes (Monado / PSVRFramework wiki). The exact byte offset of a
    dedicated VR-mode flag was not determined from any source — do not
    rely on one; `cinematic_mode` is the only mode bit confirmed here.
    """
    if len(report) < 9 or report[0] != 0xF0:
        raise ValueError(f"not a 0xF0 status report: {report[:4].hex() if report else b''}")

    flags = report[4]
    return PsvrStatus(
        raw=bytes(report),
        powered_on=bool(flags & 0x01),
        hmd_worn=bool(flags & 0x02),
        cinematic_mode=bool(flags & 0x04),
        headphones_connected=bool(flags & 0x10),
        mic_muted=bool(flags & 0x20),
        volume=report[5],
        display_on_minutes=report[8],
    )
