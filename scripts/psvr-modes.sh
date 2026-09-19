#!/usr/bin/env bash
# Add the PSVR PU's undeclared 90/120 Hz modelines via xrandr (X11 only).
#
# Same detailed timing as the EDID's native 60 Hz mode, pixel clock scaled
# up (pyPSVR edid-hacking/hook_me_up.sh). The EDID declares a 150 MHz max
# TMDS clock, which both the 90 Hz (222.75 MHz) and 120 Hz (297 MHz) modes
# exceed — on the machine in docs/display.md both were accepted and ran
# clean anyway, so don't assume the EDID's figure is a hard limit on your
# hardware; verify with your own run and record the result.
#
# Usage: scripts/psvr-modes.sh <CONNECTOR>
#   e.g. scripts/psvr-modes.sh HDMI-1

set -euo pipefail

CONNECTOR="${1:?usage: $0 <CONNECTOR>  (see: xrandr --listmonitors)}"

xrandr --newmode "1920x1080_90" 222.75 1920 2008 2052 2200 1080 1084 1089 1125 +HSync +Vsync
xrandr --newmode "1920x1080_120" 297.00 1920 2008 2052 2200 1080 1084 1089 1125 +HSync +Vsync

xrandr --addmode "$CONNECTOR" "1920x1080_90"
xrandr --addmode "$CONNECTOR" "1920x1080_120"

echo "modes added to $CONNECTOR (if xrandr didn't reject them)."
echo "switch with: xrandr --output $CONNECTOR --mode 1920x1080_90   (or _120)"
