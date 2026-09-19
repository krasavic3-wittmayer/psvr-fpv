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

Early — USB control code and CLI are written but not yet verified on
hardware. See the game plan in the spec for the milestone checklist.

## Install

```
pip install -e .
psvr-display --help
```

Requires `libusb-1.0` (system package) and the udev rule in
[`udev/99-psvr.rules`](udev/99-psvr.rules) for non-root USB access:

```
sudo cp udev/99-psvr.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Usage

```
psvr-display probe          # enumerate the PU on USB, no state change
psvr-display on              # power on, wait for confirmation
psvr-display off             # power off
psvr-display mode --mode cinematic|vr
psvr-display fpv              # on + mode + cinematic screen settings, one shot
```

## License

MIT — see [`LICENSE`](LICENSE).
