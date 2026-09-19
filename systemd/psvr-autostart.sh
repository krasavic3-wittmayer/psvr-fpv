#!/bin/bash
# Auto-start the PSVR PU when it's plugged in. Triggered by udev via
# 99-psvr.rules' SYSTEMD_WANTS tag, which activates psvr-autostart.service.
#
# Runs as root (system unit, no User= set) — fine, and actually
# convenient: root bypasses the plugdev/uaccess permission setup
# entirely for the USB side. DISPLAY/XAUTHORITY below are hardcoded for
# this machine's single-user X session; adjust PSVR_USER/DISPLAY/
# XAUTHORITY if yours differs. root can read another user's .Xauthority
# (it bypasses file permissions), so this doesn't need `sudo -u`.
#
# Scope is deliberately narrow: power on + cinematic mode only (the
# recommended, safe default — see docs/display.md). VR mode needs
# psvr-sbs running against a specific sim window too, so it stays a
# manual `psvr-display toggle` afterward, not something to guess at
# automatically on plug-in.

set -euo pipefail

PSVR_DISPLAY_BIN=/home/michal/Projects/psvr-fpv/.venv/bin/psvr-display
# NOT ~/.Xauthority (unused/empty on this machine) — the `ly` display
# manager keeps the real cookie in the user's runtime dir instead.
# Check yours with: ps aux | grep Xorg  (look for the -auth argument)
PSVR_XAUTHORITY=/run/user/1000/lyxauth
PSVR_X_DISPLAY=:0
PSVR_CONNECTOR=HDMI-1   # see docs/display.md — machine-specific, check `xrandr --listmonitors`

# Give the kernel a moment to finish binding HID drivers to the new device.
sleep 2

"$PSVR_DISPLAY_BIN" fpv

DISPLAY="$PSVR_X_DISPLAY" XAUTHORITY="$PSVR_XAUTHORITY" /usr/bin/xrandr --output "$PSVR_CONNECTOR" --auto
