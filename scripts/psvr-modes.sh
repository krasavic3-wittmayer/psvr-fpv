#!/usr/bin/env bash
# Add the PSVR PU's undeclared 90/120 Hz modelines via xrandr (X11 only).
#
# Reported, single-source (pyPSVR edid-hacking/hook_me_up.sh): same detailed
# timing as the EDID's native 60 Hz mode, pixel clock scaled up. The EDID
# declares a 150 MHz max TMDS clock, which the 120 Hz mode's 297 MHz exceeds
# — expect xrandr --addmode to be refused; see docs/display.md for the
# result on this machine. Run manually, step by step; do not assume success.
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
