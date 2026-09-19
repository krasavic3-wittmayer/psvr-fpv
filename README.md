# psvr-display

Wakes a Sony PSVR1 Processing Unit over USB and puts it into a chosen
display mode, so the headset works as an ordinary 1920x1080 HDMI monitor
for FPV drone simulators on Linux. Sends two HID commands and exits —
everything after that is the normal Linux graphics stack.

Not a VR runtime, not a SteamVR/OpenXR driver, no compositor, no
tracking. Doesn't read the IMU, doesn't render anything, doesn't require
Monado, OpenHMD, SteamVR or Proton.

See [`psvr-display-spec.md`](psvr-display-spec.md) for the full
implementation spec (protocol, architecture, game plan, known risks) and
[`docs/`](docs/) for protocol details and hardware-verification results.

## Status

Milestone 1 (steps 1-6), step 7 (90/120 Hz), step 8 (`fpv`), and step 10
(`psvr-sbs`) all confirmed on real hardware — see
[`docs/display.md`](docs/display.md) for the results and a few findings
not documented anywhere else (PU auto-disconnect without an HDMI signal;
both high-refresh modes working despite the EDID's declared 150 MHz
limit; a real `XCopyArea`-vs-`XShmGetImage` bug in `psvr-sbs`).

## Install

```
pip install -e .
psvr-display --help
```

Requires `libusb-1.0` (system package) and the udev rule in
[`udev/99-psvr.rules`](udev/99-psvr.rules) for non-root USB access:

```
sudo cp udev/99-psvr.rules /etc/udev/rules.d/
sudo usermod -aG plugdev "$USER"   # then log out and back in
sudo udevadm control --reload-rules && sudo udevadm trigger
```

`uaccess` alone did not grant access on the machine this was verified
on (see `docs/display.md`); the rule includes a `plugdev` `MODE`/`GROUP`
fallback that did. Group membership only applies to new sessions.

## Usage

```
psvr-display probe          # enumerate the PU on USB, no state change
psvr-display on              # power on, wait for confirmation
psvr-display off             # power off
psvr-display mode --mode cinematic|vr
psvr-display fpv              # on + mode + cinematic screen settings, one shot
```

**Send video promptly after `on`/`fpv`.** The PU drops off USB entirely
if it doesn't see an HDMI signal within roughly 90s of powering on —
run your `xrandr --output <connector> --auto` (or whatever your
compositor's equivalent is) right after, don't leave it idle. See
`docs/display.md` for the observed timing.

## psvr-sbs (optional)

A separate C program duplicates whatever's on a chosen screen region
into both eyes for VR mode, so a monoscopic sim looks like a duplicated
view instead of VR mode's raw left/right split. See
[`psvr-sbs/README.md`](psvr-sbs/README.md).

## License

MIT — see [`LICENSE`](LICENSE).
