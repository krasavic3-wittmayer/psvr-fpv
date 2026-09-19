"""psvr-display CLI: probe | on | off | mode | fpv."""

from __future__ import annotations

import argparse
import sys

from . import __version__, protocol
from .device import PsvrDevice, PsvrError, find_raw_device


def cmd_probe(_args: argparse.Namespace) -> int:
    dev = find_raw_device()
    if dev is None:
        print(f"not found: {protocol.VENDOR_ID:04x}:{protocol.PRODUCT_ID:04x}")
        return 1

    print(f"device: {protocol.VENDOR_ID:04x}:{protocol.PRODUCT_ID:04x}  bcdDevice={dev.bcdDevice:#06x}")
    print(f"bus={dev.bus} address={dev.address}")

    for cfg in dev:
        print(f"configuration {cfg.bConfigurationValue}")
        for intf in cfg:
            marker = " <-- control interface" if intf.bInterfaceNumber == protocol.CONTROL_INTERFACE else ""
            print(
                f"  interface {intf.bInterfaceNumber} alt {intf.bAlternateSetting} "
                f"class={intf.bInterfaceClass:#04x}{marker}"
            )
            for ep in intf:
                print(f"    endpoint {ep.bEndpointAddress:#04x} maxpacket={ep.wMaxPacketSize}")
    return 0


def cmd_on(_args: argparse.Namespace) -> int:
    with PsvrDevice() as dev:
        dev.power_on()
    print("on")
    return 0


def cmd_off(_args: argparse.Namespace) -> int:
    with PsvrDevice() as dev:
        dev.power_off()
    print("off")
    return 0


def cmd_mode(args: argparse.Namespace) -> int:
    with PsvrDevice() as dev:
        if args.mode == "vr":
            dev.vr_mode_on()
        else:
            dev.cinematic_mode_on()
    print(args.mode)
    return 0


def cmd_fpv(args: argparse.Namespace) -> int:
    with PsvrDevice() as dev:
        dev.power_on()
        if args.mode == "vr":
            dev.vr_mode_on()
        else:
            dev.cinematic_mode_on()
            dev.set_cinematic_screen(
                locked=not args.free,
                size=args.size,
                distance=args.distance,
            )
    print(f"ready: {args.mode}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psvr-display",
        description=(
            "Wake a Sony PSVR1 Processing Unit over USB and drive it as a "
            "plain HDMI display, for FPV drone simulators on Linux."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("probe", help="enumerate the PU on USB without changing its state").set_defaults(func=cmd_probe)

    sub.add_parser("on", help="power on the PU and wait for confirmation").set_defaults(func=cmd_on)
    sub.add_parser("off", help="power off the PU and wait for confirmation").set_defaults(func=cmd_off)

    mode_parser = sub.add_parser("mode", help="switch display mode")
    mode_parser.add_argument("--mode", choices=["cinematic", "vr"], required=True)
    mode_parser.set_defaults(func=cmd_mode)

    fpv_parser = sub.add_parser("fpv", help="power on + mode + cinematic screen settings, in one command")
    fpv_parser.add_argument("--mode", choices=["cinematic", "vr"], default="cinematic")
    fpv_parser.add_argument("--free", action="store_true", help="unlock the cinematic screen (default: locked)")
    fpv_parser.add_argument("--size", type=int, default=52, help="cinematic screen size, 26-100 (default 52)")
    fpv_parser.add_argument("--distance", type=int, default=35, help="cinematic screen distance, 20-50 (default 35)")
    fpv_parser.set_defaults(func=cmd_fpv)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PsvrError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
