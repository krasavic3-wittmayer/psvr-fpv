# psvr-autostart

Auto power-on for the PSVR PU: plug it in, it powers on in cinematic
mode with no manual command. Triggered by udev, not a polling daemon —
matches the project's "no long-running process" architecture (see Spec
3 in `../psvr-display-spec.md`): the PU has no keepalive requirement, so
there's nothing for a resident process to do between plug-in events.

VR mode is deliberately **not** part of auto-start — it also needs
`psvr-sbs` running against a specific sim window, which isn't something
to guess at automatically. Use `psvr-display toggle` afterward.

## How it fires

1. `udev/99-psvr.rules` matches the PU's USB "add" event and tags it
   `TAG+="systemd", ENV{SYSTEMD_WANTS}+="psvr-autostart.service"` —
   systemd's own device-triggered activation, not a udev `RUN+=` hack.
2. `psvr-autostart.service` (a `Type=oneshot` unit) runs
   `psvr-autostart.sh`, which calls `psvr-display fpv` then activates
   the HDMI output via `xrandr`.

Runs as root (no `User=` set): convenient, since root bypasses the
`plugdev`/`uaccess` permission setup for the USB side entirely, and can
read another user's `.Xauthority` to reach the X session for `xrandr`.

## Install

```
sudo cp systemd/psvr-autostart.service /etc/systemd/system/
sudo cp udev/99-psvr.rules /etc/udev/rules.d/   # if not already installed, see ../udev/99-psvr.rules
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
```

No `systemctl enable` — this unit is udev-activated, not something that
starts at boot on its own. Don't add an `[Install]` section to it.

**Machine-specific values, hardcoded in `psvr-autostart.sh`, check
before installing on a different machine:**

- `PSVR_DISPLAY_BIN` — path to the `psvr-display` venv binary
- `PSVR_XAUTHORITY` / `PSVR_X_DISPLAY` — this machine's X session.
  `~/.Xauthority` is *not* it here — the `ly` display manager keeps the
  real cookie at `/run/user/<uid>/lyxauth` instead. Find yours with
  `ps aux | grep Xorg` (look for the `-auth` argument).
- `PSVR_CONNECTOR` — `HDMI-1` on this machine (`docs/display.md`);
  check `xrandr --listmonitors` if different

## Test

```
sudo udevadm control --reload-rules
# unplug and replug the PU, then:
systemctl status psvr-autostart.service
journalctl -u psvr-autostart.service -n 20
```

The headset should light up in cinematic mode with no command run by
hand.
