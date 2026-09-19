"""USB transport: find, detach, claim, write, read status, release.

This is the only file that touches libusb. PyUSB (not hidapi) writes raw
bytes straight to the interrupt endpoint, sidestepping hidapi's report-ID
handling — see docs/protocol.md.

Untested on hardware as of writing — steps 2-4 of the game plan.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import usb.core
import usb.util

from . import protocol
from .status import PsvrStatus, parse_status

POLL_INTERVAL_S = 0.001
POLL_MAX_ITERATIONS = 5000  # ~5s cap, matches Monado's control_*_and_wait()


class PsvrError(Exception):
    """Base error for this package."""


class PsvrNotFoundError(PsvrError):
    """054c:09af not found on the USB bus."""


class PsvrTimeoutError(PsvrError):
    """Sent a command but never saw a confirming 0xF0 status."""


class PsvrDevice:
    def __init__(self) -> None:
        self._dev: Optional[usb.core.Device] = None
        self._detached = False

    # -- lifecycle --

    def open(self) -> "PsvrDevice":
        dev = usb.core.find(idVendor=protocol.VENDOR_ID, idProduct=protocol.PRODUCT_ID)
        if dev is None:
            raise PsvrNotFoundError(
                f"PSVR Processing Unit not found "
                f"({protocol.VENDOR_ID:04x}:{protocol.PRODUCT_ID:04x})"
            )
        self._dev = dev

        # Detach interface 5 only. Detaching audio interfaces would break sound.
        if dev.is_kernel_driver_active(protocol.CONTROL_INTERFACE):
            dev.detach_kernel_driver(protocol.CONTROL_INTERFACE)
            self._detached = True

        usb.util.claim_interface(dev, protocol.CONTROL_INTERFACE)
        return self

    def close(self) -> None:
        if self._dev is None:
            return
        try:
            usb.util.release_interface(self._dev, protocol.CONTROL_INTERFACE)
        finally:
            if self._detached:
                self._dev.attach_kernel_driver(protocol.CONTROL_INTERFACE)
                self._detached = False
            usb.util.dispose_resources(self._dev)
            self._dev = None

    def __enter__(self) -> "PsvrDevice":
        return self.open()

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- transport --

    def _write(self, packet: bytes) -> None:
        assert self._dev is not None, "device not open"
        self._dev.write(protocol.EP_OUT, packet)

    def _read_status_report(self) -> Optional[bytes]:
        assert self._dev is not None, "device not open"
        try:
            data = self._dev.read(protocol.EP_IN, 64, timeout=1)
        except usb.core.USBError as exc:
            if exc.errno in (110, None):  # ETIMEDOUT, or platform-reported timeout
                return None
            raise
        if len(data) >= 1 and data[0] == protocol.STATUS_REPORT_ID:
            return bytes(data)
        return None

    def send_and_wait(
        self,
        packet: bytes,
        confirmed: Callable[[PsvrStatus], bool],
    ) -> PsvrStatus:
        """Write a packet, then poll for a 0xF0 status report matching `confirmed`.

        Matches Monado's control_power_and_wait() / control_vrmode_and_wait():
        1ms poll interval, ~5s timeout cap, no fixed delays.
        """
        self._write(packet)
        for _ in range(POLL_MAX_ITERATIONS):
            report = self._read_status_report()
            if report is not None:
                status = parse_status(report)
                if confirmed(status):
                    return status
            time.sleep(POLL_INTERVAL_S)
        raise PsvrTimeoutError("timed out waiting for status confirmation")

    # -- commands --

    def power_on(self) -> PsvrStatus:
        return self.send_and_wait(protocol.PACKET_POWER_ON, lambda s: s.powered_on)

    def power_off(self) -> PsvrStatus:
        return self.send_and_wait(protocol.PACKET_POWER_OFF, lambda s: not s.powered_on)

    def cinematic_mode_on(self) -> PsvrStatus:
        return self.send_and_wait(protocol.PACKET_CINEMATIC_ON, lambda s: s.cinematic_mode)

    def vr_mode_on(self) -> PsvrStatus:
        # No confirmed dedicated VR-mode bit exists (see status.py) — use the
        # inverse of cinematic_mode as the confirmation proxy until the real
        # offset is found on hardware.
        return self.send_and_wait(protocol.PACKET_VRMODE_ON, lambda s: not s.cinematic_mode)

    def set_cinematic_screen(self, **kwargs: object) -> None:
        packet = protocol.build_cinematic_screen_settings(**kwargs)  # type: ignore[arg-type]
        self._write(packet)

    def recentre_screen(self) -> None:
        self._write(protocol.PACKET_RECENTRE_SCREEN)


def find_raw_device() -> Optional[usb.core.Device]:
    """Find the PU without claiming any interface — used by `probe`."""
    return usb.core.find(idVendor=protocol.VENDOR_ID, idProduct=protocol.PRODUCT_ID)
